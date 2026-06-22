"""Muse S Athena (Gen 3) BLE streaming.

Decode logic ported from BrainFlow PR #779 (commit 7b2e41d3, MIT license).
https://github.com/brainflow-dev/brainflow/pull/779
"""

import logging
import struct
from time import sleep, time

import bitstring
import numpy as np
import pygatt

from . import backends, helper
from .constants import (
    LSL_ATHENA_ACC_CHUNK,
    LSL_ATHENA_EEG_CHUNK,
    LSL_ATHENA_GYRO_CHUNK,
    LSL_ATHENA_OPTICS_CHUNK,
    MUSE_ATHENA_ACCELEROMETER_SCALE,
    MUSE_ATHENA_BATTERY_SCALE,
    MUSE_ATHENA_DEFAULT_PRESET,
    MUSE_ATHENA_DEVICE_CLOCK_HZ,
    MUSE_ATHENA_EEG_SCALE,
    MUSE_ATHENA_GATT_CONTROL,
    MUSE_ATHENA_GATT_DATA_1,
    MUSE_ATHENA_GATT_DATA_2,
    MUSE_ATHENA_GYRO_SCALE,
    MUSE_ATHENA_NB_ACC_CHANNELS,
    MUSE_ATHENA_NB_EEG_CHANNELS,
    MUSE_ATHENA_NB_GYRO_CHANNELS,
    MUSE_ATHENA_NB_OPTICS_CHANNELS,
    MUSE_ATHENA_OPTICS_SCALE,
    MUSE_ATHENA_PACKET_HEADER_SIZE,
    MUSE_ATHENA_SAMPLING_ACC_RATE,
    MUSE_ATHENA_SAMPLING_EEG_RATE,
    MUSE_ATHENA_SAMPLING_GYRO_RATE,
    MUSE_ATHENA_SAMPLING_OPTICS_RATE,
    MUSE_ATHENA_SENSOR_CONFIG,
    MUSE_ATHENA_SUBPACKET_HEADER_SIZE,
    MUSE_ATHENA_VALID_PRESETS,
)
from .stream_descriptor import StreamDescriptor

logger = logging.getLogger(__name__)

EEG_CHANNEL_NAMES = ('TP9', 'AF7', 'AF8', 'TP10')
OPTICS_CHANNEL_NAMES = tuple(f'OPT{i}' for i in range(MUSE_ATHENA_NB_OPTICS_CHANNELS))


def extract_lsb_bits(data, bit_start, bit_width):
    """Read bit_width bits at absolute bit index bit_start (LSB-first in byte stream)."""
    bits = bitstring.Bits(bytes=data)
    value = 0
    for bit in range(bit_width):
        absolute_bit = bit_start + bit
        if bits[absolute_bit]:
            value |= 1 << bit
    return value


def get_sensor_config(tag):
    """Return sensor config tuple or None for unknown tags."""
    return MUSE_ATHENA_SENSOR_CONFIG.get(tag)


def optics_canonical_index(tag, channel):
    """Map per-tag channel index to canonical optics channel 0..15."""
    if tag == 0x34:
        if 0 <= channel < 4:
            return channel + 4
    elif tag == 0x35:
        if 0 <= channel < 8:
            return channel
    elif tag == 0x36:
        if 0 <= channel < 16:
            return channel
    return -1


def decode_eeg(data, n_channels, n_samples):
    """Decode 14-bit LSB-first EEG payload -> (n_channels, n_samples) float32 µV."""
    out = np.zeros((n_channels, n_samples), dtype=np.float32)
    for sample in range(n_samples):
        for channel in range(n_channels):
            bit_start = (sample * n_channels + channel) * 14
            raw = extract_lsb_bits(data, bit_start, 14)
            out[channel, sample] = raw * MUSE_ATHENA_EEG_SCALE
    return out


def decode_acc_gyro(data, n_samples):
    """Decode int16 LE ACC+GYRO payload -> acc (3, n), gyro (3, n)."""
    acc = np.zeros((3, n_samples), dtype=np.float32)
    gyro = np.zeros((3, n_samples), dtype=np.float32)
    for sample in range(n_samples):
        for channel in range(6):
            offset = (sample * 6 + channel) * 2
            raw = struct.unpack_from('<h', data, offset)[0]
            if channel < 3:
                acc[channel, sample] = raw * MUSE_ATHENA_ACCELEROMETER_SCALE
            else:
                gyro[channel - 3, sample] = raw * MUSE_ATHENA_GYRO_SCALE
    return acc, gyro


def decode_optics(data, tag, n_channels, n_samples):
    """Decode 20-bit LSB-first optics -> (16, n_samples); unused slots stay 0."""
    out = np.zeros((MUSE_ATHENA_NB_OPTICS_CHANNELS, n_samples), dtype=np.float32)
    for sample in range(n_samples):
        for channel in range(n_channels):
            bit_start = (sample * n_channels + channel) * 20
            raw = extract_lsb_bits(data, bit_start, 20)
            idx = optics_canonical_index(tag, channel)
            if idx >= 0:
                out[idx, sample] = raw * MUSE_ATHENA_OPTICS_SCALE
    return out


def decode_battery(data):
    """Battery percent from first uint16 LE."""
    if len(data) < 2:
        return None
    return struct.unpack_from('<H', data, 0)[0] * MUSE_ATHENA_BATTERY_SCALE


def split_packets(data):
    """Split a BLE notification into (packet_bytes, ...) using length-prefixed framing."""
    packets = []
    offset = 0
    size = len(data)
    while offset < size:
        if size - offset < MUSE_ATHENA_PACKET_HEADER_SIZE:
            break
        packet_len = data[offset]
        if packet_len < MUSE_ATHENA_PACKET_HEADER_SIZE or offset + packet_len > size:
            break
        packets.append(bytes(data[offset:offset + packet_len]))
        offset += packet_len
    return packets


def parse_packet_header(packet):
    """Return (device_tick, packet_index, primary_tag, payload_bytes)."""
    device_tick = struct.unpack_from('<I', packet, 2)[0]
    packet_index = struct.unpack_from('<H', packet, 1)[0]
    primary_tag = packet[9]
    payload = packet[MUSE_ATHENA_PACKET_HEADER_SIZE:]
    return device_tick, packet_index, primary_tag, payload


def iter_sensor_blocks(packet):
    """Yield (tag, package_num, device_tick, payload) for primary + subpackets."""
    device_tick, packet_index, primary_tag, payload = parse_packet_header(packet)
    offset = 0
    remaining = len(payload)

    def emit(tag, block_index, block_payload):
        package_num = (packet_index << 8) | block_index
        yield tag, package_num, device_tick, block_payload

    config = get_sensor_config(primary_tag)
    if config is not None:
        _, _, _, _, data_len, variable = config
        primary_len = remaining if variable else data_len
        if primary_len > remaining:
            primary_len = remaining
        block_index = packet[10]
        yield from emit(primary_tag, block_index, payload[:primary_len])
        offset = primary_len
    else:
        offset = remaining

    while offset + MUSE_ATHENA_SUBPACKET_HEADER_SIZE <= len(payload):
        tag = payload[offset]
        sub_index = payload[offset + 1]
        config = get_sensor_config(tag)
        if config is None:
            break
        _, _, _, _, data_len, variable = config
        sub_remaining = len(payload) - offset - MUSE_ATHENA_SUBPACKET_HEADER_SIZE
        sensor_len = sub_remaining if variable else data_len
        if sensor_len <= 0 or sensor_len > sub_remaining:
            break
        start = offset + MUSE_ATHENA_SUBPACKET_HEADER_SIZE
        end = start + sensor_len
        block = payload[start:end]
        yield from emit(tag, sub_index, block)
        offset += MUSE_ATHENA_SUBPACKET_HEADER_SIZE + sensor_len


def device_tick_delta(tick, t0_tick):
    """uint32 device tick difference with wraparound."""
    return (tick - t0_tick) & 0xFFFFFFFF


def sample_timestamps(device_tick, n_samples, sampling_rate, t0_tick, t0_host, time_func):
    """Per-sample host timestamps from device clock (§2.8)."""
    base = t0_host + device_tick_delta(device_tick, t0_tick) / MUSE_ATHENA_DEVICE_CLOCK_HZ
    return np.array(
        [base + i / sampling_rate for i in range(n_samples)],
        dtype=np.float64,
    )


class Athena:
    """Muse S Athena headband (multiplexed DATA_1/DATA_2 protocol)."""

    def __init__(
        self,
        address,
        callback_eeg=None,
        callback_control=None,
        callback_acc=None,
        callback_gyro=None,
        callback_optics=None,
        backend='auto',
        interface=None,
        time_func=time,
        name=None,
        preset=None,
        disable_light=False,
        low_latency=True,
    ):
        self.address = address
        self.name = name
        self.callback_eeg = callback_eeg
        self.callback_control = callback_control
        self.callback_acc = callback_acc
        self.callback_gyro = callback_gyro
        self.callback_optics = callback_optics

        self.enable_eeg = callback_eeg is not None
        self.enable_control = callback_control is not None
        self.enable_acc = callback_acc is not None
        self.enable_gyro = callback_gyro is not None
        self.enable_optics = callback_optics is not None

        self.interface = interface
        self.time_func = time_func
        self.backend = helper.resolve_backend(backend)
        self.preset = preset or MUSE_ATHENA_DEFAULT_PRESET
        self.disable_light = disable_light
        self.low_latency = low_latency

        self.device = None
        self.adapter = None
        self.last_timestamp = self.time_func()
        self._battery = 0.0
        self._timestamp_initialized = False
        self._t0_tick = 0
        self._t0_host = 0.0

    def stream_descriptors(self):
        """LSL stream shapes for Athena."""
        descs = [
            StreamDescriptor(
                'EEG', 'EEG', MUSE_ATHENA_NB_EEG_CHANNELS, EEG_CHANNEL_NAMES,
                MUSE_ATHENA_SAMPLING_EEG_RATE, LSL_ATHENA_EEG_CHUNK, 'microvolts',
            ),
            StreamDescriptor(
                'ACC', 'ACC', MUSE_ATHENA_NB_ACC_CHANNELS, ('X', 'Y', 'Z'),
                MUSE_ATHENA_SAMPLING_ACC_RATE, LSL_ATHENA_ACC_CHUNK, 'g',
            ),
            StreamDescriptor(
                'GYRO', 'GYRO', MUSE_ATHENA_NB_GYRO_CHANNELS, ('X', 'Y', 'Z'),
                MUSE_ATHENA_SAMPLING_GYRO_RATE, LSL_ATHENA_GYRO_CHUNK, 'dps',
            ),
            StreamDescriptor(
                'OPTICS', 'OPTICS', MUSE_ATHENA_NB_OPTICS_CHANNELS, OPTICS_CHANNEL_NAMES,
                MUSE_ATHENA_SAMPLING_OPTICS_RATE, LSL_ATHENA_OPTICS_CHUNK, 'a.u.',
            ),
        ]
        return descs

    def connect(self, interface=None, retries=0):
        """Connect, subscribe control + DATA_1 + DATA_2, run init command sequence."""
        try:
            logger.info(
                'Connecting to %s: %s...',
                self.name if self.name else 'Muse Athena',
                self.address,
            )
            if self.backend == 'gatt':
                self.interface = self.interface or interface or 'hci0'
                self.adapter = pygatt.GATTToolBackend(self.interface)
            elif self.backend == 'bleak':
                self.adapter = backends.BleakBackend()
            else:
                self.adapter = pygatt.BGAPIBackend(serial_port=self.interface or interface)

            self.adapter.start()
            device = self.adapter.connect(self.address, retries, self.name)
            if device is None:
                return False
            self.device = device

            if not self._has_athena_data_char():
                raise RuntimeError(
                    'Device does not expose Athena data characteristic '
                    f'{MUSE_ATHENA_GATT_DATA_1}; not a Muse S Athena.'
                )

            print('[athena] Subscribing to control + DATA_1/DATA_2...')
            self._subscribe_control()
            self._subscribe_data()

            if self.disable_light:
                self._write_cmd_str('L0')

            self._run_init_sequence()
            print('[athena] Headband setup complete.')
            self.last_timestamp = self.time_func()
            return True

        except pygatt.exceptions.BLEError:
            logger.error('Connection to %s failed', self.address)
            return False

    def _has_athena_data_char(self):
        if hasattr(self.device, 'has_characteristic'):
            return self.device.has_characteristic(MUSE_ATHENA_GATT_DATA_1)
        return True

    def _subscribe_control(self):
        self.device.subscribe(MUSE_ATHENA_GATT_CONTROL, callback=self._handle_control)

    def _subscribe_data(self):
        self.device.subscribe(MUSE_ATHENA_GATT_DATA_1, callback=self._handle_data)
        self.device.subscribe(MUSE_ATHENA_GATT_DATA_2, callback=self._handle_data)

    def _write_cmd(self, cmd):
        if hasattr(self.device, 'char_write_uuid'):
            self.device.char_write_uuid(MUSE_ATHENA_GATT_CONTROL, cmd, False)
        else:
            self.device.char_write_handle(0x000e, cmd, False)

    def _write_cmd_str(self, cmd):
        logger.debug('[athena] -> cmd %r', cmd)
        self._write_cmd([len(cmd) + 1, *(ord(c) for c in cmd), ord('\n')])

    def _run_init_sequence(self):
        for cmd in ('v6', 's', 'h', self._normalize_preset(self.preset), 's'):
            self._write_cmd_str(cmd)
            sleep(0.2)

    def _normalize_preset(self, preset):
        preset = str(preset)
        if preset[0] == 'p':
            preset = preset[1:]
        preset = 'p' + preset
        if preset not in MUSE_ATHENA_VALID_PRESETS:
            logger.warning('Unknown Athena preset %s, using %s', preset, MUSE_ATHENA_DEFAULT_PRESET)
            preset = MUSE_ATHENA_DEFAULT_PRESET
        return preset

    def select_preset(self, preset=None):
        preset = self._normalize_preset(preset or self.preset)
        self.preset = preset
        self._write_cmd_str(preset)

    def start(self):
        self._reset_timestamps()
        self._write_cmd_str('dc001')
        sleep(0.05)
        self._write_cmd_str('dc001')
        if self.low_latency:
            sleep(0.1)
            self._write_cmd_str('L1')
        sleep(0.3)
        self._write_cmd_str('s')
        sleep(0.2)

    def stop(self):
        self._write_cmd_str('h')

    def refresh_subscriptions(self):
        """No-op: Athena always notifies on DATA_1/DATA_2 once connected."""

    def disconnect(self):
        if self.device:
            self.device.disconnect()
        if self.adapter:
            self.adapter.stop()

    def _reset_timestamps(self):
        self._timestamp_initialized = False
        self._t0_tick = 0
        self._t0_host = 0.0

    def _init_timestamp(self, device_tick):
        if not self._timestamp_initialized:
            self._t0_tick = device_tick
            self._t0_host = self.time_func()
            self._timestamp_initialized = True

    def _handle_data(self, handle, data):
        """BLE notify callback: demux length-prefixed packets by sensor tag.

        One notification may contain several packets back-to-back:

            [len][idx_lo][idx_hi][tick x4][---][tag][idx2][---][payload...][sub hdr+payload]*

        Primary block uses 14-byte header; optional 5-byte subpacket headers follow.
        """
        # ponytail: exceptions raised in a Bleak notify callback are swallowed by
        # asyncio, so wrap + log or a decode bug looks identical to "no data arriving".
        try:
            logger.debug(
                '[athena] notify handle=0x%04x len=%d data=%s',
                handle, len(data), bytes(data).hex(),
            )
            packets = split_packets(data)
            if not packets:
                logger.debug('[athena] notify produced no framed packets (len=%d)', len(data))
            for packet in packets:
                for tag, _package_num, device_tick, payload in iter_sensor_blocks(packet):
                    logger.debug(
                        '[athena] block tag=0x%02x tick=%d payload_len=%d',
                        tag, device_tick, len(payload),
                    )
                    self._init_timestamp(device_tick)
                    self._parse_payload(tag, device_tick, payload)
        except Exception:
            logger.exception('[athena] exception in _handle_data (handle=0x%04x)', handle)

    def _parse_payload(self, tag, device_tick, data):
        config = get_sensor_config(tag)
        if config is None:
            return
        sensor_type, n_channels, n_samples, rate, _data_len, _variable = config

        if sensor_type == 'unknown':
            return

        if sensor_type == 'battery':
            pct = decode_battery(data)
            if pct is not None:
                self._battery = pct
            return

        timestamps = sample_timestamps(
            device_tick, n_samples, rate,
            self._t0_tick, self._t0_host, self.time_func,
        )
        # The liveness watchdog (stream.py) compares last_timestamp against the host
        # wall clock, so track host receipt time here — not the device-tick sample
        # time, which runs on its own clock and would trip the 3s watchdog. The
        # device timestamps still flow to the LSL callbacks below.
        self.last_timestamp = self.time_func()
        logger.debug(
            '[athena] %s tag=0x%02x n=%d device_ts=%.3f host_ts=%.3f',
            sensor_type, tag, n_samples, float(timestamps[-1]), self.last_timestamp,
        )

        if sensor_type == 'eeg' and self.enable_eeg:
            # Tag 0x11 packs 4 channels, 0x12 packs 8 (first 4 are TP9/AF7/AF8/TP10,
            # the rest are aux). Decode all n_channels for correct 14-bit offsets,
            # then push only the 4 the outlet expects (mirrors BrainFlow PR #779).
            samples = decode_eeg(data, n_channels, n_samples)
            self.callback_eeg(samples[:MUSE_ATHENA_NB_EEG_CHANNELS], timestamps)

        elif sensor_type == 'acc_gyro':
            acc, gyro = decode_acc_gyro(data, n_samples)
            if self.enable_acc:
                self.callback_acc(acc, timestamps)
            if self.enable_gyro:
                self.callback_gyro(gyro, timestamps)

        elif sensor_type == 'optics' and self.enable_optics:
            samples = decode_optics(data, tag, n_channels, n_samples)
            self.callback_optics(samples, timestamps)

    def _handle_control(self, handle, packet):
        n_incoming = packet[0]
        message = bytes(packet[1:1 + n_incoming]).decode('ascii', errors='replace')
        logger.debug('[athena] control reply: %r', message)
        if self.enable_control and self.callback_control:
            self.callback_control(message)
