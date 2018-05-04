import bitstring
import pygatt
import numpy as np
from time import time, sleep
from sys import platform


class Muse():
    """Muse 2016 headband"""

    def __init__(self, address=None, callback_eeg=None, callback_control=None,
                callback_telemetry=None, callback_acc=None, callback_gyro=None,
                backend='auto', interface=None, time_func=time, name=None):
        """Initialize

        callback_eeg -- callback for eeg data, function(data, timestamps)
        callback_control -- function(message)
        callback_telemetry -- function(timestamp, battery, fuel_gauge, adc_volt, temperature)

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

        self.enable_eeg = not callback_eeg is None
        self.enable_control = not callback_control is None
        self.enable_telemetry = not callback_telemetry is None
        self.enable_acc = not callback_acc is None
        self.enable_gyro = not callback_gyro is None

        self.interface = interface
        self.time_func = time_func

        if backend in ['auto', 'gatt', 'bgapi']:
            if backend == 'auto':
                if platform == "linux" or platform == "linux2":
                    self.backend = 'gatt'
                else:
                    self.backend = 'bgapi'
            else:
                self.backend = backend
        else:
            raise(ValueError('Backend must be auto, gatt or bgapi'))

    def connect(self, interface=None, backend='auto'):
        """Connect to the device"""

        if self.backend == 'gatt':
            self.interface = self.interface or 'hci0'
            self.adapter = pygatt.GATTToolBackend(self.interface)
        else:
            self.adapter = pygatt.BGAPIBackend(serial_port=self.interface)

        self.adapter.start()

        if self.address is None:
            address = self.find_muse_address(self.name)
            if address is None:
                raise(ValueError("Can't find Muse Device"))
            else:
                self.address = address
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

    def find_muse_address(self, name=None):
        """look for ble device with a muse in the name"""
        list_devices = self.adapter.scan(timeout=10.5)
        for device in list_devices:
            if name:
                if device['name'] == name:
                    print('Found device %s : %s' % (device['name'],
                                                    device['address']))
                    return device['address']

            elif 'Muse' in device['name']:
                    print('Found device %s : %s' % (device['name'],
                                                    device['address']))
                    return device['address']

        return None

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
        self._write_cmd([0x03, 0x76, 0x31, 0x0a])

    def start(self):
        """Start streaming."""
        self._init_timestamp_correction()
        self._init_sample()
        self.last_tm = 0
        self._write_cmd([0x02, 0x64, 0x0a])

        self._init_control()

    def stop(self):
        """Stop streaming."""
        self._write_cmd([0x02, 0x68, 0x0a])

    def disconnect(self):
        """disconnect."""
        self.device.disconnect()
        self.adapter.stop()


    def _subscribe_eeg(self):
        """subscribe to eeg stream."""
        self.device.subscribe('273e0003-4c4d-454d-96be-f03bac821358',
                              callback=self._handle_eeg)
        self.device.subscribe('273e0004-4c4d-454d-96be-f03bac821358',
                              callback=self._handle_eeg)
        self.device.subscribe('273e0005-4c4d-454d-96be-f03bac821358',
                              callback=self._handle_eeg)
        self.device.subscribe('273e0006-4c4d-454d-96be-f03bac821358',
                              callback=self._handle_eeg)
        self.device.subscribe('273e0007-4c4d-454d-96be-f03bac821358',
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

    def _init_timestamp_correction(self):
        """Init IRLS params"""
        # initial params for the timestamp correction
        # the time it started + the inverse of sampling rate
        self.sample_index = 0
        self.reg_params = np.array([self.time_func(), 1./256])

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

            # affect as timestamps
            timestamps = self.reg_params[1] * idxs + self.reg_params[0]

            # push data
            self.callback_eeg(self.data, timestamps)
            self._init_sample()


    def _init_control(self):
        """Variable to store the current incoming message."""
        self._current_msg = ""

    def _subscribe_control(self):
        self.device.subscribe('273e0001-4c4d-454d-96be-f03bac821358', callback=self._handle_control)

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

        if incoming_message[-1] == '}': # Message ended completely
            self.callback_control(self._current_msg)

            self._init_control()

    def _subscribe_telemetry(self):
        self.device.subscribe('273e000b-4c4d-454d-96be-f03bac821358',
                            callback=self._handle_telemetry)

    def _handle_telemetry(self, handle, packet):
        """Handle the telemetry (battery, temperature and stuff) incoming data"""

        if handle != 26: # handle 0x1a
            return
        timestamp = self.time_func()

        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:16,uint:16,uint:16,uint:16" # The rest is 0 padding
        data = bit_decoder.unpack(pattern)

        packet_index = data[0]
        battery = data[1] / 512
        fuel_gauge = data[2] * 2.2
        adc_volt = data[3]
        temperature = data[4]

        self.callback_telemetry(timestamp, battery, fuel_gauge, adc_volt, temperature)


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

        samples = [[
            scale * data[index],        # x
            scale * data[index + 1],    # y
            scale * data[index + 2]     # z
        ] for index in [1, 4, 7]]

        ## samples is a list with 3 samples
        ## each sample is a list with [x, y, z]

        return packet_index, samples

    def _subscribe_acc(self):
        self.device.subscribe('273e000a-4c4d-454d-96be-f03bac821358',
                            callback=self._handle_acc)

    def _handle_acc(self, handle, packet):
        """Handle incoming accelerometer data.

        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        if handle != 23: # handle 0x17
            return
        timestamp = self.time_func()

        packet_index, samples = self._unpack_imu_channel(packet, scale=0.0000610352)

        self.callback_acc(timestamp, samples)

    def _subscribe_gyro(self):
        self.device.subscribe('273e0009-4c4d-454d-96be-f03bac821358',
                            callback=self._handle_gyro)

    def _handle_gyro(self, handle, packet):
        """Handle incoming gyroscope data.

        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        if handle != 20: # handle 0x14
            return

        timestamp = self.time_func()

        packet_index, samples = self._unpack_imu_channel(packet, scale=0.0074768)

        self.callback_gyro(timestamp, samples)
