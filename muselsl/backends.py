import asyncio
import atexit
import sys
import time
from typing import Any
try:
    import bleak
except ModuleNotFoundError as error:
    # Defer the import failure until a Bleak backend is actually used (see scan()).
    bleak = error  # type: ignore[assignment]
from .constants import RETRY_SLEEP_TIMEOUT

_loop = None

def _get_event_loop():
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop

def _wait(coroutine):
    return _get_event_loop().run_until_complete(coroutine)

def sleep(seconds):
    time.sleep(seconds)

class BleakBackend:
    def __init__(self):
        self.connected = set()
        atexit.register(self.stop)
        # run the event loop when sleeping
        global sleep
        sleep = self.pump
    def start(self):
        pass
    def pump(self, seconds=1):
        _wait(asyncio.sleep(seconds))
    def stop(self):
        for device in [*self.connected]:
            device.disconnect()
    def scan(self, timeout=10):
        if isinstance(bleak, ModuleNotFoundError):
            raise bleak
        start = time.monotonic()
        print(f'[0.0s] Scanning for BLE devices ({timeout}s)...')
        devices = _wait(bleak.BleakScanner.discover(timeout))
        print(f'[{time.monotonic() - start:.1f}s] Scan complete, {len(devices)} devices found.')
        return [{'name':device.name, 'address':device.address} for device in devices]
    def connect(self, address, retries, name=None):
        result = BleakDevice(self, address, name=name)
        if not result.connect(retries):
            return None
        return result

class BleakDevice:
    def __init__(self, adapter, address, name=None):
        self._adapter = adapter
        self._address = address
        self._name = name
        self._client: Any = None

    def _elapsed(self, start):
        return time.monotonic() - start

    def _refresh_address(self, start):
        if not self._name:
            return
        print(f'[{self._elapsed(start):.1f}s] Scanning for {self._name}...')
        devices = _wait(bleak.BleakScanner.discover(5.0))
        for device in devices:
            if device.name and self._name in device.name:
                if device.address != self._address:
                    print(f'[{self._elapsed(start):.1f}s] Updated address: {device.address}')
                self._address = device.address
                return
        print(f'[{self._elapsed(start):.1f}s] {self._name} not seen during scan')

    # Use retries=-1 to continue attempting to reconnect forever
    def connect(self, retries):
        start = time.monotonic()
        attempts = 1
        connect_errors = (
            bleak.exc.BleakDeviceNotFoundError,
            bleak.exc.BleakError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        while True:
            if attempts == 1:
                print(f'[{self._elapsed(start):.1f}s] Connecting to {self._address}...')
            else:
                self._refresh_address(start)
                print(f'[{self._elapsed(start):.1f}s] Connection attempt {attempts}...')
            client = bleak.BleakClient(self._address, timeout=30.0)
            try:
                _wait(client.connect())
            except connect_errors as err:
                print(f'[{self._elapsed(start):.1f}s] Failed to connect: {err}', file=sys.stderr)
                try:
                    _wait(client.disconnect())
                except Exception:
                    pass
                if attempts == 1 + retries:
                    return False
                sleep(RETRY_SLEEP_TIMEOUT)
                attempts += 1
            else:
                print(f'[{self._elapsed(start):.1f}s] BLE connected.')
                self._client = client
                break
        self._adapter.connected.add(self)
        return True
    def disconnect(self):
        _wait(self._client.disconnect())
        self._adapter.connected.remove(self)
    # Characteristics have two handles: the declaration handle and the value handle.
    # Pygatt seems to use the value handle, which appears less common.  Bleak uses the
    # declaration handle used by d-bus.
    # With the muse, the declaration and value handles happen to be sequential.
    # So, we subtract 1 to get the declaration handle, and add 1 to get the value handle.
    def char_write_handle(self, value_handle, value, wait_for_response=True, timeout=30):
        declaration_handle = value_handle - 1
        _wait(self._client.write_gatt_char(
            declaration_handle,
            bytearray(value),
            wait_for_response))
    def subscribe(self, uuid, callback=None, indication=False, wait_for_response=True):
        def wrap(gatt_characteristic, data):
            value_handle = gatt_characteristic.handle + 1
            callback(value_handle, data)
        _wait(self._client.start_notify(uuid, wrap))
