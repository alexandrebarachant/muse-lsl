from time import time, sleep
from pylsl import StreamInfo, StreamOutlet
import pygatt
import subprocess
from sys import platform
from . import helper
from .muse import Muse
from .constants import MUSE_NB_CHANNELS, MUSE_SAMPLING_RATE, MUSE_SCAN_TIMEOUT, LSL_CHUNK, AUTO_DISCONNECT_DELAY


# Returns a list of available Muse devices.
def list_muses(backend='auto', interface=None):
    backend = helper.resolve_backend(backend)

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
            print('Found device %s, MAC Address %s' %
                  (muse['name'], muse['address']))
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
def stream(address, backend='auto', interface=None, name=None):
    bluemuse = backend == 'bluemuse'
    if not bluemuse:
        if not address:
            found_muse = find_muse(name)
            if not found_muse:
                return
            else:
                address = found_muse['address']
                name = found_muse['name']

    info = StreamInfo('Muse', 'EEG', MUSE_NB_CHANNELS, MUSE_SAMPLING_RATE, 'float32',
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
                backend=backend, interface=interface, name=name)

    if(bluemuse):
        muse.connect()
        if not address and not name:
            print('Targeting first device BlueMuse discovers...')
        else:
            print('Targeting device: ' +
                  ':'.join(filter(None, [name, address])) + '...')
        print('\n*BlueMuse will auto connect and stream when the device is found. \n*You can also use the BlueMuse interface to manage your stream(s).')
        muse.start()
        return
    
    # Muse 2014 refactor --------------------------------------------------------------------------------------------
    # TODO: as noted in muse.py of the 2014 refactor, need to add start, stop, disconnect, and timestamp methods for the below code to work
    # TODO: integrate muse_2014 with the list_muses and find_muse method above

    # put muse_2014 imports here for now for clarity
    from .muse import Muse_2014

    # obviously better to integrate if statements into above code, but for now temporarily keep seperate
    muse_2014 = backend == 'muse_2014'
    if muse_2014:
        PORT = '1234'
        info = StreamInfo('Muse', 'EEG', 4, 220, 'float32',
                          'MuseName')

        info.desc().append_child_value("manufacturer", "Muse")
        channels = info.desc().append_child("channels")

        for c in ['TP9-l_ear', 'FP1-l_forehead', 'FP2-r_forehead', 'TP10-r_ear']:
            channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "EEG")

        # create a pylsl outlet; specify info, chunk size (each push yields one chunk), and maximum buffered data
        outlet = StreamOutlet(info, 1, 360)

        def push_eeg(data, timestamp, index, outlet):
            """Callback function for pushing data to an lsl outlet.

            Args:
                data: The data being pushed through the lsl outlet. Must be an array with size specified by the number of
                    channels in pylsl.StreamInfo.
                timestamp: The time at which the data sample occurred, such as through pylsl.local_clock(), etc.
                index: For testing purposes; index at which the sample occurred.
                outlet: pylsl outlet to which data is pushed.
            """
            outlet.push_sample(data, timestamp)

        # connect to the server; start pushing muse data to the pylsl outlet
        try:
            muse = Muse_2014(PORT, push_eeg, outlet)
        except Muse_2014.ServerError:
            raise ValueError('Cannot create PylibloServer Object.')
    # ----------------------------------------------------------------------------------------------------------------

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
