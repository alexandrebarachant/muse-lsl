import atexit
try:
    import async_to_sync as sync
    import bleak
except ModuleNotFoundError:
    bleak = None

class BleakBackend:
    def __init__(self):
        self.connected = set()
        atexit.register(self.stop)
    def start(self):
        sync.start()
    def stop(self):
        for device in self.connected:
            device.disconnect()
        sync.stop()
    def scan(self, timeout=10):
        scanner = sync.methods(bleak.BleakScanner())
        devices = scanner.discover(timeout)
        return [{'name':device.name, 'address':device.address} for device in devices]
    def connect(self, address):
        result = BleakDevice(self, address)
        result.connect()
        return result

class BleakDevice:
    def __init__(self, adapter, address):
        self._adapter = adapter
        self._client = sync.methods(bleak.BleakClient(address))
    def connect(self):
        self._client.connect()
        self._adapter.connected.add(self)
    def disconnect(self):
        self._client.disconnect()
        self._adapter.connected.remove(self)
    # Characteristics have two handles: the declaration handle and the value handle.
    # Pygatt seems to use the value handle, which appears less common.  Bleak uses the
    # declaration handle used by d-bus.
    # With the muse, the declaration and value handles happen to be sequential.
    # So, we subtract 1 to get the declaration handle, and add 1 to get the value handle.
    def char_write_handle(self, value_handle, value, wait_for_response=True, timeout=30):
        declaration_handle = value_handle - 1
        self._client.write_gatt_char(declaration_handle, bytearray(value), wait_for_response)
    def subscribe(self, uuid, callback=None, indication=False, wait_for_response=True):
        def wrap(declaration_handle, data):
            value_handle = declaration_handle + 1
            callback(value_handle, data)
        self._client.start_notify(uuid, wrap)
