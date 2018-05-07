from muse import Muse
from constants import NB_CHANNELS, SAMPLING_RATE, SCAN_TIMEOUT, LSL_CHUNK
from time import sleep
from pylsl import StreamInfo, StreamOutlet, local_clock
import pygatt
from sys import platform


def list_devices():
    interface = None
    if platform == "linux" or platform == "linux2":
        backend = 'gatt'
    else:
        backend = 'bgapi'

    if backend == 'gatt':
        interface = interface or 'hci0'
        adapter = pygatt.GATTToolBackend(interface)
    else:
        adapter = pygatt.BGAPIBackend(serial_port=interface)
 
    print('Searching for Muses, this may take up to 10 seconds...')
    devices = adapter.scan(timeout=SCAN_TIMEOUT)
    muses = []

    for device in devices:
        if device['name'] and 'Muse' in device['name']:
            muses = muses + [device]

    return muses

def stream(address, backend, interface, name):
    info = info = StreamInfo('Muse', 'EEG', NB_CHANNELS, SAMPLING_RATE, 'float32',
                             'Muse%s' % address)

    info.desc().append_child_value("manufacturer", "Muse")
    channels = info.desc().append_child("channels")

    for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
        channels.append_child("channel") \
            .append_child_value("label", c) \
            .append_child_value("unit", "microvolts") \
            .append_child_value("type", "EEG")

    outlet = StreamOutlet(info, LSL_CHUNK)

    def push_eeg(data, timestamps):
        for ii in range(LSL_CHUNK):
            outlet.push_sample(data[:, ii], timestamps[ii])
    
    muse = Muse(address=address, callback_eeg=push_eeg,
                backend=backend, time_func=local_clock,
                interface=interface, name=name)

    muse.connect()
    print('Connected')
    muse.start()
    print('Streaming')

    while 1:
        try:
            sleep(1)
        except:
            break

    muse.stop()
    muse.disconnect()
    print('Disonnected')
