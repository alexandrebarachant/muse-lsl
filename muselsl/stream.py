import re
import subprocess
from functools import partial
from shutil import which
from sys import platform
from time import time

import pygatt
from pylsl import local_clock

from . import backends, helper
from .constants import (
    AUTO_DISCONNECT_DELAY,
    LIST_SCAN_TIMEOUT,
    RETRY_SLEEP_TIMEOUT,
)
from .devices import create_device
from .lsl_outlet import build_outlet
from .muse import Muse


def _print_muse_list(muses):
    for m in muses:
        print(f'Found device {m["name"]}, MAC Address {m["address"]}')
    if not muses:
        print('No Muses found.')


# Returns a list of available Muse devices.
def list_muses(backend='auto', interface=None):
    if backend == 'auto' and which('bluetoothctl') is not None:
        print("Backend was 'auto' and bluetoothctl was found, using to list muses...")
        return _list_muses_bluetoothctl(LIST_SCAN_TIMEOUT)

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
        devices = adapter.scan(timeout=LIST_SCAN_TIMEOUT)
        adapter.stop()
    except pygatt.exceptions.BLEError as e:
        if backend == 'gatt':
            print('pygatt failed to scan for BLE devices. Trying with '
                  'bluetoothctl.')
            return _list_muses_bluetoothctl(LIST_SCAN_TIMEOUT)
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
    except (pexpect.EOF, pexpect.TIMEOUT):
        # Both EOF and TIMEOUT mean the scan completed normally: bluetoothctl
        # may exit cleanly (EOF) after the scan starts at the Bluetooth stack
        # level, rather than timing out.
        if verbose:
            print(scan.before.decode('utf-8', 'replace').split('\r\n'))
    finally:
        scan.terminate(force=True)

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
def _descriptor_enabled(name, eeg_disabled, ppg_enabled, acc_enabled, gyro_enabled):
    if name == 'EEG':
        return not eeg_disabled
    if name == 'PPG':
        return ppg_enabled
    if name == 'ACC':
        return acc_enabled
    if name == 'GYRO':
        return gyro_enabled
    if name == 'OPTICS':
        return False
    return False


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
    lsl_time=False,
    retries=1,
    model='auto',
):
    # If no data types are enabled, we warn the user and return immediately.
    if eeg_disabled and not ppg_enabled and not acc_enabled and not gyro_enabled:
        print('Stream initiation failed: At least one data source must be enabled.')
        return

    # For any backend except bluemuse, we will start LSL streams hooked up to the muse callbacks.
    if backend != 'bluemuse':
        if not address:
            attempts = 0
            found_muse = None
            while found_muse is None and (retries < 0 or attempts <= retries):
                found_muse = find_muse(name, backend)
                if found_muse is None and (retries < 0 or attempts < retries):
                    print('Muse not found. Retrying scan...')
                    backends.sleep(RETRY_SLEEP_TIMEOUT)
                attempts += 1
            if not found_muse:
                return
            else:
                address = found_muse['address']
                name = found_muse['name']

        def push(data, timestamps, outlet):
            for ii in range(data.shape[1]):
                outlet.push_sample(data[:, ii], timestamps[ii])

        time_func = local_clock if lsl_time else time

        muse = create_device(
            address=address,
            model=model,
            backend=backend,
            interface=interface,
            name=name,
            preset=preset,
            disable_light=disable_light,
            time_func=time_func,
        )

        didConnect = muse.connect(retries=retries)

        if not didConnect:
            print('Failed to connect to Muse.')
            return

        enabled = {
            d.name: _descriptor_enabled(
                d.name, eeg_disabled, ppg_enabled, acc_enabled, gyro_enabled,
            )
            for d in muse.stream_descriptors()
        }
        outlets = {}
        for desc in muse.stream_descriptors():
            if enabled.get(desc.name):
                outlets[desc.name] = build_outlet(desc, address)

        push_eeg = partial(push, outlet=outlets['EEG']) if 'EEG' in outlets else None
        push_ppg = partial(push, outlet=outlets['PPG']) if 'PPG' in outlets else None
        push_acc = partial(push, outlet=outlets['ACC']) if 'ACC' in outlets else None
        push_gyro = partial(push, outlet=outlets['GYRO']) if 'GYRO' in outlets else None

        muse.callback_eeg = push_eeg
        muse.callback_ppg = push_ppg
        muse.callback_acc = push_acc
        muse.callback_gyro = push_gyro
        muse.enable_eeg = push_eeg is not None
        muse.enable_ppg = push_ppg is not None
        muse.enable_acc = push_acc is not None
        muse.enable_gyro = push_gyro is not None
        muse.refresh_subscriptions()

        if didConnect:
            print('Connected.')
            muse.start()

            eeg_string = " EEG" if not eeg_disabled else ""
            ppg_string = " PPG" if ppg_enabled else ""
            acc_string = " ACC" if acc_enabled else ""
            gyro_string = " GYRO" if gyro_enabled else ""

            print("Streaming%s%s%s%s..." %
                (eeg_string, ppg_string, acc_string, gyro_string))

            while time_func() - muse.last_timestamp < AUTO_DISCONNECT_DELAY:
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
        muse.connect(retries=retries)

        if not address and not name:
            print('Targeting first device BlueMuse discovers...')
        else:
            print('Targeting device: '
                  + ':'.join(filter(None, [name, address])) + '...')
        print('\n*BlueMuse will auto connect and stream when the device is found. \n*You can also use the BlueMuse interface to manage your stream(s).')
        muse.start()
