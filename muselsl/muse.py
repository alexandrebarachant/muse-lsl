import bitstring
import pygatt
import numpy as np
from time import time, sleep
from sys import platform
import subprocess
from . import helper
from .constants import *


class Muse():
    """Muse 2016 headband"""

    def __init__(self, address, callback_eeg=None, callback_control=None,
                 callback_telemetry=None, callback_acc=None, callback_gyro=None,
                 callback_ppg=None, backend='auto', interface=None, time_func=time, name=None):
        """Initialize

        callback_eeg -- callback for eeg data, function(data, timestamps)
        callback_control -- function(message)
        callback_telemetry -- function(timestamp, battery, fuel_gauge,
                                       adc_volt, temperature)

        callback_acc -- function(timestamp, samples)
        callback_gyro -- function(timestamp, samples)
        - samples is a list of 3 samples, where each sample is [x, y, z]
        """

        self.address = address
        self.name = name
        self.callback_eeg = callback_eeg
        self.callback_telemetry = callback_telemetry
        self.callback_control = callback_control
        self.callback_acc = callback_acc
        self.callback_gyro = callback_gyro
        self.callback_ppg = callback_ppg

        self.enable_eeg = not callback_eeg is None
        self.enable_control = not callback_control is None
        self.enable_telemetry = not callback_telemetry is None
        self.enable_acc = not callback_acc is None
        self.enable_gyro = not callback_gyro is None
        self.enable_ppg = not callback_ppg is None

        self.interface = interface
        self.time_func = time_func

        self.backend = helper.resolve_backend(backend)

    def connect(self, interface=None, backend='auto'):
        """Connect to the device"""
        try:
            if self.backend == 'bluemuse':
                print('Starting BlueMuse.')
                subprocess.call('start bluemuse:', shell=True)

            else:
                print('Connecting to %s : %s...' %
                      (self.name if self.name else 'Muse', self.address))
                if self.backend == 'gatt':
                    self.interface = self.interface or 'hci0'
                    self.adapter = pygatt.GATTToolBackend(self.interface)
                else:
                    self.adapter = pygatt.BGAPIBackend(
                        serial_port=self.interface)

                self.adapter.start()
                self.device = self.adapter.connect(self.address)

                # subscribes to EEG stream
                if self.enable_eeg:
                    self._subscribe_eeg()

                if self.enable_control:
                    self._subscribe_control()

                if self.enable_telemetry:
                    self._subscribe_telemetry()

                if self.enable_acc:
                    self._subscribe_acc()

                if self.enable_gyro:
                    self._subscribe_gyro()

                if self.enable_ppg:
                    self._subscribe_ppg()

                self.last_timestamp = self.time_func()

            return True

        except pygatt.exceptions.BLEError as error:
            if("characteristic" in str(error)):
                self.ask_reset()
                sleep(2)
                self.device = self.adapter.connect(self.address)
                self.select_preset(preset=21)

                # subscribes to EEG stream
                if self.enable_eeg:
                    self._subscribe_eeg()

                if self.enable_control:
                    self._subscribe_control()

                if self.enable_telemetry:
                    self._subscribe_telemetry()

                if self.enable_acc:
                    self._subscribe_acc()

                if self.enable_gyro:
                    self._subscribe_gyro()

                if self.enable_ppg:
                    self._subscribe_ppg()

                self.last_timestamp = self.time_func()

                return True

            else:
                print('Connection to', self.address, 'failed')
                return False

    def _write_cmd(self, cmd):
        """Wrapper to write a command to the Muse device.
        cmd -- list of bytes"""
        self.device.char_write_handle(0x000e, cmd, False)

    def ask_control(self):
        """Send a message to Muse to ask for the control status.

        Only useful if control is enabled (to receive the answer!)

        The message received is a dict with the following keys:
        "hn": device name
        "sn": serial number
        "ma": MAC address
        "id":
        "bp": battery percentage
        "ts":
        "ps": preset selected
        "rc": return status, if 0 is OK
        """
        if self.backend == 'bluemuse':
            helper.warn_bluemuse_not_supported()
            return
        self._write_cmd([0x02, 0x73, 0x0a])

    def ask_device_info(self):
        """Send a message to Muse to ask for the device info.

        The message received is a dict with the following keys:
        "ap":
        "sp":
        "tp": firmware type, e.g: "consumer"
        "hw": hardware version?
        "bn": build number?
        "fw": firmware version?
        "bl":
        "pv": protocol version?
        "rc": return status, if 0 is OK
        """
        if self.backend == 'bluemuse':
            helper.warn_bluemuse_not_supported()
            return
        self._write_cmd([0x03, 0x76, 0x31, 0x0a])

    def ask_reset(self):
        """Undocumented command reset for '*1'
        The message received is a singleton with:
        "rc": return status, if 0 is OK
        """
        self._write_cmd([0x03, 0x2a, 0x31, 0x0a])

    def start(self):
        """Start streaming."""
        if self.backend == 'bluemuse':
            address = self.address if self.address is not None else self.name
            if address is None:
                subprocess.call(
                    'start bluemuse://start?streamfirst=true', shell=True)
            else:
                subprocess.call(
                    'start bluemuse://start?addresses={0}'.format(address), shell=True)
            return

        self._init_timestamp_correction()
        self._init_sample()
        self._init_ppg_sample()
        self.last_tm = 0
        self.last_tm_ppg = 0
        self._init_control()
        self.resume()

    def resume(self):
        """Resume streaming, sending 'd' command"""
        self._write_cmd([0x02, 0x64, 0x0a])

    def stop(self):
        """Stop streaming."""
        if self.backend == 'bluemuse':
            address = self.address if self.address is not None else self.name
            if address is None:
                subprocess.call('start bluemuse://stopall', shell=True)
            else:
                subprocess.call(
                    'start bluemuse://stop?addresses={0}'.format(address), shell=True)
            return

        self._write_cmd([0x02, 0x68, 0x0a])

    def keep_alive(self):
        """Keep streaming, sending 'k' command"""
        self._write_cmd([0x02, 0x6b, 0x0a])

    def select_preset(self, preset=21):
        """Setting preset for headband configuration

        See details on https://goo.gl/FPN1ib
        For 2016 headband, possible choice are 'p20' and 'p21'.
        Untested but possible values are 'p22' and 'p23'
        Default is 'p21'."""
        if preset == 20:
            self._write_cmd([0x04, 0x70, 0x32, 0x30, 0x0a])
        elif preset == 22:
            self._write_cmd([0x04, 0x70, 0x32, 0x32, 0x0a])
        elif preset == 23:
            self._write_cmd([0x04, 0x70, 0x32, 0x33, 0x0a])
        else:
            self._write_cmd([0x04, 0x70, 0x32, 0x31, 0x0a])

    def disconnect(self):
        """disconnect."""
        if self.backend == 'bluemuse':
            subprocess.call('start bluemuse://shutdown', shell=True)
            return

        self.device.disconnect()
        if self.adapter:
            self.adapter.stop()

    def _subscribe_eeg(self):
        """subscribe to eeg stream."""
        self.device.subscribe(MUSE_GATT_ATTR_TP9,
                              callback=self._handle_eeg)
        self.device.subscribe(MUSE_GATT_ATTR_AF7,
                              callback=self._handle_eeg)
        self.device.subscribe(MUSE_GATT_ATTR_AF8,
                              callback=self._handle_eeg)
        self.device.subscribe(MUSE_GATT_ATTR_TP10,
                              callback=self._handle_eeg)
        self.device.subscribe(MUSE_GATT_ATTR_RIGHTAUX,
                              callback=self._handle_eeg)

    def _unpack_eeg_channel(self, packet):
        """Decode data packet of one EEG channel.

        Each packet is encoded with a 16bit timestamp followed by 12 time
        samples with a 12 bit resolution.
        """
        aa = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:12,uint:12,uint:12,uint:12,uint:12,uint:12, \
                   uint:12,uint:12,uint:12,uint:12,uint:12,uint:12"
        res = aa.unpack(pattern)
        packetIndex = res[0]
        data = res[1:]
        # 12 bits on a 2 mVpp range
        data = 0.48828125 * (np.array(data) - 2048)
        return packetIndex, data

    def _init_sample(self):
        """initialize array to store the samples"""
        self.timestamps = np.zeros(5)
        self.data = np.zeros((5, 12))

    def _init_ppg_sample(self):
        """ Initialise array to store PPG samples

            Must be separate from the EEG packets since they occur with a different sampling rate. Ideally the counters
            would always match, but this is not guaranteed
        """
        self.timestamps_ppg = np.zeros(3)
        self.data_ppg = np.zeros((3, 6))

    def _init_timestamp_correction(self):
        """Init IRLS params"""
        # initial params for the timestamp correction
        # the time it started + the inverse of sampling rate
        self.sample_index = 0
        self.sample_index_ppg = 0
        self.reg_params = np.array(
            [self.time_func(), 1. / MUSE_SAMPLING_EEG_RATE])
        self.reg_ppg_sample_rate = np.array(
            [self.time_func(), 1. / MUSE_SAMPLING_PPG_RATE])

    def _update_timestamp_correction(self, x, y):
        """Update regression for dejittering

        use stochastic gradient descent
        """
        pass

    def _handle_eeg(self, handle, data):
        """Callback for receiving a sample.

        samples are received in this order : 44, 41, 38, 32, 35
        wait until we get 35 and call the data callback
        """
        timestamp = self.time_func()
        index = int((handle - 32) / 3)
        tm, d = self._unpack_eeg_channel(data)

        if self.last_tm == 0:
            self.last_tm = tm - 1

        self.data[index] = d
        self.timestamps[index] = timestamp
        # last data received
        if handle == 35:
            if tm != self.last_tm + 1:
                print("missing sample %d : %d" % (tm, self.last_tm))
            self.last_tm = tm

            # calculate index of time samples
            idxs = np.arange(0, 12) + self.sample_index
            self.sample_index += 12

            # timestamps are extrapolated backwards based on sampling rate and current time
            timestamps = self.reg_params[1] * idxs + self.reg_params[0]

            # push data
            self.callback_eeg(self.data, timestamps)

            # save last timestamp for disconnection timer
            self.last_timestamp = timestamps[-1]

            # reset sample
            self._init_sample()

    def _init_control(self):
        """Variable to store the current incoming message."""
        self._current_msg = ""

    def _subscribe_control(self):
        self.device.subscribe(
            MUSE_GATT_ATTR_STREAM_TOGGLE, callback=self._handle_control)

        self._init_control()

    def _handle_control(self, handle, packet):
        """Handle the incoming messages from the 0x000e handle.

        Each message is 20 bytes
        The first byte, call it n, is the length of the incoming string.
        The rest of the bytes are in ASCII, and only n chars are useful

        Multiple messages together are a json object (or dictionary in python)
        If a message has a '}' then the whole dict is finished.

        Example:
        {'key': 'value',
        'key2': 'really-long
        -value',
        'key3': 'value3'}

        each line is a message, the 4 messages are a json object.
        """
        if handle != 14:
            return

        # Decode data
        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8, \
                    uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8,uint:8"
        chars = bit_decoder.unpack(pattern)

        # Length of the string
        n_incoming = chars[0]

        # Parse as chars, only useful bytes
        incoming_message = "".join(map(chr, chars[1:]))[:n_incoming]

        # Add to current message
        self._current_msg += incoming_message

        if incoming_message[-1] == '}':  # Message ended completely
            self.callback_control(self._current_msg)

            self._init_control()

    def _subscribe_telemetry(self):
        self.device.subscribe(MUSE_GATT_ATTR_TELEMETRY,
                              callback=self._handle_telemetry)

    def _handle_telemetry(self, handle, packet):
        """Handle the telemetry (battery, temperature and stuff) incoming data
        """

        if handle != 26:  # handle 0x1a
            return
        timestamp = self.time_func()

        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:16,uint:16,uint:16,uint:16"  # The rest is 0 padding
        data = bit_decoder.unpack(pattern)

        battery = data[1] / 512
        fuel_gauge = data[2] * 2.2
        adc_volt = data[3]
        temperature = data[4]

        self.callback_telemetry(
            timestamp, battery, fuel_gauge, adc_volt, temperature)

    def _unpack_imu_channel(self, packet, scale=1):
        """Decode data packet of the accelerometer and gyro (imu) channels.

        Each packet is encoded with a 16bit timestamp followed by 9 samples
        with a 16 bit resolution.
        """
        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:16,int:16,int:16,int:16,int:16, \
                   int:16,int:16,int:16,int:16,int:16"
        data = bit_decoder.unpack(pattern)

        packet_index = data[0]

        samples = np.array(data[1:]).reshape((3, 3), order='F') * scale

        return packet_index, samples

    def _subscribe_acc(self):
        self.device.subscribe(MUSE_GATT_ATTR_ACCELEROMETER,
                              callback=self._handle_acc)

    def _handle_acc(self, handle, packet):
        """Handle incoming accelerometer data.

        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        if handle != 23:  # handle 0x17
            return
        timestamps = [self.time_func()] * 3

        # save last timestamp for disconnection timer
        self.last_timestamp = timestamps[-1]

        packet_index, samples = self._unpack_imu_channel(
            packet, scale=MUSE_ACCELEROMETER_SCALE_FACTOR)

        self.callback_acc(samples, timestamps)

    def _subscribe_gyro(self):
        self.device.subscribe(MUSE_GATT_ATTR_GYRO,
                              callback=self._handle_gyro)

    def _handle_gyro(self, handle, packet):
        """Handle incoming gyroscope data.

        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        if handle != 20:  # handle 0x14
            return

        timestamps = [self.time_func()] * 3

        # save last timestamp for disconnection timer
        self.last_timestamp = timestamps[-1]

        packet_index, samples = self._unpack_imu_channel(
            packet, scale=MUSE_GYRO_SCALE_FACTOR)

        self.callback_gyro(samples, timestamps)

    def _subscribe_ppg(self):
        """subscribe to ppg stream."""
        self.device.subscribe(MUSE_GATT_ATTR_PPG1,
                              callback=self._handle_ppg)
        self.device.subscribe(MUSE_GATT_ATTR_PPG2,
                              callback=self._handle_ppg)
        self.device.subscribe(MUSE_GATT_ATTR_PPG3,
                              callback=self._handle_ppg)

    def _handle_ppg(self, handle, data):
        """Callback for receiving a sample.

        samples are received in this order : 56, 59, 62
        wait until we get x and call the data callback
        """
        timestamp = self.time_func()
        index = int((handle - 56) / 3)
        tm, d = self._unpack_ppg_channel(data)

        if self.last_tm_ppg == 0:
            self.last_tm_ppg = tm - 1

        self.data_ppg[index] = d
        self.timestamps_ppg[index] = timestamp
        # last data received
        if handle == 62:
            if tm != self.last_tm_ppg + 1:
                print("missing sample %d : %d" % (tm, self.last_tm_ppg))
            self.last_tm_ppg = tm

            # calculate index of time samples
            idxs = np.arange(0, LSL_PPG_CHUNK) + self.sample_index_ppg
            self.sample_index_ppg += LSL_PPG_CHUNK

            # timestamps are extrapolated backwards based on sampling rate and current time
            timestamps = self.reg_ppg_sample_rate[1] * \
                idxs + self.reg_ppg_sample_rate[0]

            # save last timestamp for disconnection timer
            self.last_timestamp = timestamps[-1]

            # push data
            if self.callback_ppg:
                self.callback_ppg(self.data_ppg, timestamps)

            # reset sample
            self._init_ppg_sample()

    def _unpack_ppg_channel(self, packet):
        """Decode data packet of one PPG channel.
        Each packet is encoded with a 16bit timestamp followed by 3
        samples with an x bit resolution.
        """

        aa = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:24,uint:24,uint:24,uint:24,uint:24,uint:24"
        res = aa.unpack(pattern)
        packetIndex = res[0]
        data = res[1:]

        return packetIndex, data
