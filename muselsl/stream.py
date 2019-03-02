from time import time, sleep
from pylsl import StreamInfo, StreamOutlet
import pygatt
import subprocess
from sys import platform
import helper as hp
from muse import Muse
from constants import MUSE_NB_EEG_CHANNELS, MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_RATE, MUSE_SCAN_TIMEOUT, LSL_CHUNK, AUTO_DISCONNECT_DELAY


# Returns a list of available Muse devices.
def list_muses(backend='auto', interface=None):
    backend = hp.resolve_backend(backend)

    if backend == 'gatt':
        interface = interface or 'hci0'
        adapter = pygatt.GATTToolBackend(interface)
    elif backend == 'bluemuse':
        print('Starting BlueMuse, see BlueMuse window for interactive list of devices.')
        subprocess.call('start bluemuse:', shell=True)
        return
    else:
        adapter = pygatt.BGAPIBackend(serial_port=interface)

    adapter.start()
    print('Searching for Muses, this may take up to 10 seconds...')
    devices = adapter.scan(timeout=MUSE_SCAN_TIMEOUT)
    adapter.stop()
    muses = []

    for device in devices:
        if device['name'] and 'Muse' in device['name']:
            muses = muses + [device]

    if(muses):
        for muse in muses:
            print('Found device %s, MAC Address %s' % (muse['name'], muse['address']))
    else:
        print('No Muses found.')

    return muses


# Returns the address of the Muse with the name provided, otherwise returns address of first available Muse.
def find_muse(name=None):
    muses = list_muses()
    if name:
        for muse in muses:
            if muse['name'] == name:
                return muse
    elif muses:
        return muses[0]


# Begins an LSL stream containing EEG data from a Muse with a given address
def stream(address, backend='auto', interface=None, name=None, streamtype=1):
    bluemuse = backend == 'bluemuse'
    if not bluemuse:
        if not address:
            found_muse = find_muse(name)
            if not found_muse:
                return
            else:
                address = found_muse['address']
                name = found_muse['name']

    enable_gyro = False ;
    enable_accelero = False ;
    enable_telemetry = False ;
    enable_ppg = False ;
    enable_eeg = False ;

    if streamtype >= 16 :
        enable_gyro = True
        streamtype -= 16
        print("Enabling gyro data streaming")

    if streamtype >= 8 :
        enable_accelero = True
        streamtype -= 8
        print("Enabling accelero data streaming")

    if streamtype >= 4 :
        enable_telemetry = True
        streamtype -= 4
        print("Enabling telemetry data streaming")

    if streamtype >= 2 :
        enable_ppg = True
        streamtype -= 2
        print("Enabling PPG data streaming")

    if streamtype >= 1 :
        enable_eeg = True
        streamtype -= 1
        print("Enabling EEG data streaming")

    # EEG STREAM
    if enable_eeg :
        info_eeg = StreamInfo('Muse', 'EEG', MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_RATE, 'float32', 'Muse%s-EEG' % address)
        info_eeg.desc().append_child_value("manufacturer", "Muse")
        channels_eeg = info_eeg.desc().append_child("channels")

        for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
            channels_eeg.append_child("channel") \
	            .append_child_value("label", c) \
	            .append_child_value("unit", "microvolts") \
	            .append_child_value("type", "EEG")

        outlet_eeg = StreamOutlet(info_eeg, LSL_CHUNK)

    # PPG STREAM
    if enable_ppg :

        info_ppg = StreamInfo('Muse', 'PPG', MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_RATE, 'float32',
                          'Muse%s-PPG' % address)

        info_ppg.desc().append_child_value("manufacturer", "Muse")
        channels_ppg = info_ppg.desc().append_child("channels")

        for c in ['ambiant', 'infrared', 'red']:
            channels_ppg.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "PPG")

        outlet_ppg = StreamOutlet(info_ppg, LSL_CHUNK)

    # GYRO STREAM
    if enable_gyro :
        info_gyro = StreamInfo('Muse', 'GYRO', 3, 50, 'float32',
                          'Muse%s-GYRO' % address)

        info_gyro.desc().append_child_value("manufacturer", "Muse")
        channels_gyro = info_gyro.desc().append_child("channels")

        for c in ['X', 'Y', 'Z']:
            channels_gyro.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "?") \
                .append_child_value("type", "GYRO")

        outlet_gyro = StreamOutlet(info_gyro)

    # ACCELERO STREAM
    if enable_accelero :
        info_accelero = StreamInfo('Muse', 'ACCELERO', 3, 50, 'float32',
                          'Muse%s-ACCELERO' % address)

        info_accelero.desc().append_child_value("manufacturer", "Muse")
        channels_accelero = info_accelero.desc().append_child("channels")

        for c in ['X', 'Y', 'Z']:
            channels_accelero.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "?") \
                .append_child_value("type", "GYRO")

        outlet_accelero = StreamOutlet(info_accelero)

    # TELEMETRY STREAM
    if enable_telemetry :
        info_telemetry = StreamInfo('Muse', 'TELEMETRY', 4, 10, 'float32',
                          'Muse%s-TELEMETRY' % address)

        info_telemetry.desc().append_child_value("manufacturer", "Muse")
        channels_telemetry = info_telemetry.desc().append_child("channels")

        for c in ['battery', 'fuel_gauge', 'adc_volt', 'temperature']:
            channels_telemetry.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "?") \
                .append_child_value("type", "telemetry")

        outlet_telemetry = StreamOutlet(info_telemetry)


    def push_eeg(data, timestamps):
        if enable_eeg :
            for ii in range(len(data)):
                outlet_eeg.push_sample(data[:, ii], timestamps[ii])

    def push_ppg(data, timestamps):
        if enable_ppg :
            for ii in range(len(data)):
                outlet_ppg.push_sample(data[:, ii], timestamps[ii])

    def push_gyro(timestamps, data):
        if enable_gyro :
            for ii in range(len(data)):
                outlet_gyro.push_sample(data[ii], timestamps[ii])	

    def push_accelero(timestamps, data):
        if enable_accelero :
            for ii in range(len(data)):
                outlet_accelero.push_sample(data[ii], timestamps[ii])

    def push_telemetry(timestamps, data):
        if enable_telemetry :
            outlet_telemetry.push_sample(data, timestamps)

    muse = Muse(address=address, callback_eeg=push_eeg, callback_ppg=push_ppg, callback_telemetry=push_telemetry, callback_acc=push_accelero, callback_gyro=push_gyro,
                backend=backend, interface=interface, name=name)

    if(bluemuse):
        muse.connect()
        if not address and not name:
            print('Targeting first device BlueMuse discovers...')
        else:
            print('Targeting device: ' +
                  ':'.join(filter(None, [name, address])) + '...')
        print('\nBlueMuse will auto connect and stream when the device is found. \n*You can also use the BlueMuse interface to manage your stream(s).')
        muse.start()
        return

    didConnect = muse.connect()

    if(didConnect):
        print('Connected.')
        muse.start()
        print('Streaming...')

        while time() - muse.last_timestamp < AUTO_DISCONNECT_DELAY:
            try:
                sleep(1)
            except KeyboardInterrupt:
                muse.stop()
                muse.disconnect()
                break

        print('Disconnected.')
