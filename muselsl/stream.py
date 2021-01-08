import re
import subprocess
from sys import platform
from time import time
from functools import partial
from shutil import which

from pylsl import StreamInfo, StreamOutlet
import pygatt

from . import backends
from . import helper
from .muse import Muse
from .constants import MUSE_SCAN_TIMEOUT, AUTO_DISCONNECT_DELAY,  \
    MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, LSL_EEG_CHUNK,  \
    MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE, LSL_PPG_CHUNK, \
    MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE, LSL_ACC_CHUNK, \
    MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE, LSL_GYRO_CHUNK


def _print_muse_list(muses):
    for m in muses:
        print(f'Found device {m["name"]}, MAC Address {m["address"]}')
    if not muses:
        print('No Muses found.')


# Returns a list of available Muse devices.
def list_muses(backend='auto', interface=None):
    if backend == 'auto' and which('bluetoothctl') is not None:
        print("Backend was 'auto' and bluetoothctl was found, using to list muses...")
        return _list_muses_bluetoothctl(MUSE_SCAN_TIMEOUT)

    backend = helper.resolve_backend(backend)

    if backend == 'gatt':
        interface = interface or 'hci0'
        adapter = pygatt.GATTToolBackend(interface)
    elif backend == 'bluemuse':
        print('Starting BlueMuse, see BlueMuse window for interactive list of devices.')
        subprocess.call('start bluemuse:', shell=True)
        return
    elif backend == 'bleak':
        adapter = backends.BleakBackend()
    elif backend == 'bgapi':
        adapter = pygatt.BGAPIBackend(serial_port=interface)

    try:
        adapter.start()
        print('Searching for Muses, this may take up to 10 seconds...')
        devices = adapter.scan(timeout=MUSE_SCAN_TIMEOUT)
        adapter.stop()
    except pygatt.exceptions.BLEError as e:
        if backend == 'gatt':
            print('pygatt failed to scan for BLE devices. Trying with '
                  'bluetoothctl.')
            return _list_muses_bluetoothctl(MUSE_SCAN_TIMEOUT)
        else:
            raise e

    muses = [d for d in devices if d['name'] and 'Muse' in d['name']]
    _print_muse_list(muses)

    return muses


def _list_muses_bluetoothctl(timeout, verbose=False):
    """Identify Muse BLE devices using bluetoothctl.

    When using backend='gatt' on Linux, pygatt relies on the command line tool
    `hcitool` to scan for BLE devices. `hcitool` is however deprecated, and
    seems to fail on Bluetooth 5 devices. This function roughly replicates the
    functionality of `pygatt.backends.gatttool.gatttool.GATTToolBackend.scan()`
    using the more modern `bluetoothctl` tool.

    Deprecation of hcitool: https://git.kernel.org/pub/scm/bluetooth/bluez.git/commit/?id=b1eb2c4cd057624312e0412f6c4be000f7fc3617
    """
    try:
        import pexpect
    except (ImportError, ModuleNotFoundError):
        msg = ('pexpect is currently required to use bluetoothctl from within '
               'a jupter notebook environment.')
        raise ModuleNotFoundError(msg)

    # Run scan using pexpect as subprocess.run returns immediately in jupyter
    # notebooks
    print('Searching for Muses, this may take up to 10 seconds...')
    scan = pexpect.spawn('bluetoothctl scan on')
    try:
        scan.expect('foooooo', timeout=timeout)
    except pexpect.EOF:
        before_eof = scan.before.decode('utf-8', 'replace')
        msg = f'Unexpected error when scanning: {before_eof}'
        raise ValueError(msg)
    except pexpect.TIMEOUT:
        if verbose:
            print(scan.before.decode('utf-8', 'replace').split('\r\n'))

    # List devices using bluetoothctl
    list_devices_cmd = ['bluetoothctl', 'devices']
    devices = subprocess.run(
        list_devices_cmd, stdout=subprocess.PIPE).stdout.decode(
            'utf-8').split('\n')
    muses = [{
            'name': re.findall('Muse.*', string=d)[0],
            'address': re.findall(r'..:..:..:..:..:..', string=d)[0]
        } for d in devices if 'Muse' in d]
    _print_muse_list(muses)

    return muses


# Returns the address of the Muse with the name provided, otherwise returns address of first available Muse.
def find_muse(name=None, backend='auto'):
    muses = list_muses(backend)
    if name:
        for muse in muses:
            if muse['name'] == name:
                return muse
    elif muses:
        return muses[0]


# Begins LSL stream(s) from a Muse with a given address with data sources determined by arguments
def stream(
    address,
    backend='auto',
    interface=None,
    name=None,
    ppg_enabled=False,
    acc_enabled=False,
    gyro_enabled=False,
    eeg_disabled=False,
    preset=None,
    disable_light=False,
    timeout=AUTO_DISCONNECT_DELAY,
):
    # If no data types are enabled, we warn the user and return immediately.
    if eeg_disabled and not ppg_enabled and not acc_enabled and not gyro_enabled:
        print('Stream initiation failed: At least one data source must be enabled.')
        return

    # For any backend except bluemuse, we will start LSL streams hooked up to the muse callbacks.
    if backend != 'bluemuse':
        if not address:
            found_muse = find_muse(name, backend)
            if not found_muse:
                return
            else:
                address = found_muse['address']
                name = found_muse['name']

        if not eeg_disabled:
            eeg_info = StreamInfo('Muse', 'EEG', MUSE_NB_EEG_CHANNELS, MUSE_SAMPLING_EEG_RATE, 'float32',
                                'Muse%s' % address)
            eeg_info.desc().append_child_value("manufacturer", "Muse")
            eeg_channels = eeg_info.desc().append_child("channels")

            for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
                eeg_channels.append_child("channel") \
                    .append_child_value("label", c) \
                    .append_child_value("unit", "microvolts") \
                    .append_child_value("type", "EEG")

            eeg_outlet = StreamOutlet(eeg_info, LSL_EEG_CHUNK)

        if ppg_enabled:
            ppg_info = StreamInfo('Muse', 'PPG', MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE,
                                'float32', 'Muse%s' % address)
            ppg_info.desc().append_child_value("manufacturer", "Muse")
            ppg_channels = ppg_info.desc().append_child("channels")

            for c in ['PPG1', 'PPG2', 'PPG3']:
                ppg_channels.append_child("channel") \
                    .append_child_value("label", c) \
                    .append_child_value("unit", "mmHg") \
                    .append_child_value("type", "PPG")

            ppg_outlet = StreamOutlet(ppg_info, LSL_PPG_CHUNK)

        if acc_enabled:
            acc_info = StreamInfo('Muse', 'ACC', MUSE_NB_ACC_CHANNELS, MUSE_SAMPLING_ACC_RATE,
                                'float32', 'Muse%s' % address)
            acc_info.desc().append_child_value("manufacturer", "Muse")
            acc_channels = acc_info.desc().append_child("channels")

            for c in ['X', 'Y', 'Z']:
                acc_channels.append_child("channel") \
                    .append_child_value("label", c) \
                    .append_child_value("unit", "g") \
                    .append_child_value("type", "accelerometer")

            acc_outlet = StreamOutlet(acc_info, LSL_ACC_CHUNK)

        if gyro_enabled:
            gyro_info = StreamInfo('Muse', 'GYRO', MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE,
                                'float32', 'Muse%s' % address)
            gyro_info.desc().append_child_value("manufacturer", "Muse")
            gyro_channels = gyro_info.desc().append_child("channels")

            for c in ['X', 'Y', 'Z']:
                gyro_channels.append_child("channel") \
                    .append_child_value("label", c) \
                    .append_child_value("unit", "dps") \
                    .append_child_value("type", "gyroscope")

            gyro_outlet = StreamOutlet(gyro_info, LSL_GYRO_CHUNK)

        def push(data, timestamps, outlet):
            for ii in range(data.shape[1]):
                outlet.push_sample(data[:, ii], timestamps[ii])

        push_eeg = partial(push, outlet=eeg_outlet) if not eeg_disabled else None
        push_ppg = partial(push, outlet=ppg_outlet) if ppg_enabled else None
        push_acc = partial(push, outlet=acc_outlet) if acc_enabled else None
        push_gyro = partial(push, outlet=gyro_outlet) if gyro_enabled else None

        muse = Muse(address=address, callback_eeg=push_eeg, callback_ppg=push_ppg, callback_acc=push_acc, callback_gyro=push_gyro,
                    backend=backend, interface=interface, name=name, preset=preset, disable_light=disable_light)

        didConnect = muse.connect()

        if(didConnect):
            print('Connected.')
            muse.start()

            eeg_string = " EEG" if not eeg_disabled else ""
            ppg_string = " PPG" if ppg_enabled else ""
            acc_string = " ACC" if acc_enabled else ""
            gyro_string = " GYRO" if gyro_enabled else ""

            print("Streaming%s%s%s%s..." %
                (eeg_string, ppg_string, acc_string, gyro_string))

            while time() - muse.last_timestamp < timeout:
                try:
                    backends.sleep(1)
                except KeyboardInterrupt:
                    muse.stop()
                    muse.disconnect()
                    break

            print('Disconnected.')

    # For bluemuse backend, we don't need to create LSL streams directly, since these are handled in BlueMuse itself.
    else:
        # Toggle all data stream types in BlueMuse.
        subprocess.call('start bluemuse://setting?key=eeg_enabled!value={}'.format('false' if eeg_disabled else 'true'), shell=True)
        subprocess.call('start bluemuse://setting?key=ppg_enabled!value={}'.format('true' if ppg_enabled else 'false'), shell=True)
        subprocess.call('start bluemuse://setting?key=accelerometer_enabled!value={}'.format('true' if acc_enabled else 'false'), shell=True)
        subprocess.call('start bluemuse://setting?key=gyroscope_enabled!value={}'.format('true' if gyro_enabled else 'false'), shell=True)

        muse = Muse(address=address, callback_eeg=None, callback_ppg=None, callback_acc=None, callback_gyro=None,
                    backend=backend, interface=interface, name=name)
        muse.connect()

        if not address and not name:
            print('Targeting first device BlueMuse discovers...')
        else:
            print('Targeting device: '
                  + ':'.join(filter(None, [name, address])) + '...')
        print('\n*BlueMuse will auto connect and stream when the device is found. \n*You can also use the BlueMuse interface to manage your stream(s).')
        muse.start()
