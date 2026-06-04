"""Device factory: legacy Muse vs Muse S Athena."""

from .athena import Athena
from .constants import MUSE_ATHENA_GATT_DATA_1, MUSE_GATT_ATTR_TP9
from .muse import Muse


def probe_athena(device):
    """Return True if the connected GATT device exposes Athena DATA_1 (273e0013)."""
    if device is None:
        return False
    if hasattr(device, 'has_characteristic'):
        return device.has_characteristic(MUSE_ATHENA_GATT_DATA_1)
    return False


def probe_legacy_eeg(device):
    """Return True if legacy per-channel EEG characteristics are present."""
    if device is None:
        return False
    if hasattr(device, 'has_characteristic'):
        return device.has_characteristic(MUSE_GATT_ATTR_TP9)
    return True


def create_device(address, model='auto', **kwargs):
    """Return a Muse or Athena instance (not yet connected unless noted).

    Model selection (connect-time probe for ``auto``):

        connect(BLE)
              |
              v
        has 273e0013 ? ----yes----> Athena
              |
             no
              v
        has legacy EEG ? ---yes---> Muse (legacy)
              |
             no
              v
        RuntimeError (unrecognized Muse)

    ``model`` override:
      - ``legacy`` -> Muse (no probe)
      - ``athena`` -> Athena (fails connect if 273e0013 missing)
      - ``auto``   -> probe after first connect (see ``_AutoSelectingDevice``)
    """
    model = (model or 'auto').lower()
    if model == 'legacy':
        return Muse(address, **kwargs)
    if model == 'athena':
        return Athena(address, **kwargs)
    if model == 'auto':
        return _AutoSelectingDevice(address, **kwargs)
    raise ValueError(f"Unknown model {model!r}; use auto, athena, or legacy")


class _AutoSelectingDevice:
    """Connect once as Muse, probe GATT, then delegate to Muse or Athena."""

    _DELEGATED_ATTRS = (
        'callback_eeg', 'callback_ppg', 'callback_acc', 'callback_gyro',
        'callback_optics', 'callback_control', 'callback_telemetry',
        'enable_eeg', 'enable_ppg', 'enable_acc', 'enable_gyro',
        'enable_optics', 'enable_control', 'enable_telemetry',
    )

    def __init__(self, address, **kwargs):
        self.address = address
        self._kwargs = kwargs
        self._impl = None

    def __getattr__(self, name):
        if self._impl is None:
            raise RuntimeError('Device not connected; call connect() first')
        return getattr(self._impl, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name in self._DELEGATED_ATTRS:
            impl = object.__getattribute__(self, '_impl')
            if impl is not None:
                setattr(impl, name, value)

    def _sync_impl(self):
        if self._impl is None:
            return
        for name in self._DELEGATED_ATTRS:
            if hasattr(self, name):
                setattr(self._impl, name, getattr(self, name))

    def connect(self, interface=None, retries=0):
        probe = Muse(self.address, **self._kwargs)
        if not probe.connect(interface=interface, retries=retries):
            return False

        if probe_athena(probe.device):
            probe.disconnect()
            self._impl = Athena(self.address, **self._kwargs)
            if not self._impl.connect(interface=interface, retries=retries):
                return False
            self._sync_impl()
            return True

        if not probe_legacy_eeg(probe.device):
            probe.disconnect()
            raise RuntimeError(
                'Connected device has neither Athena data characteristic '
                f'({MUSE_ATHENA_GATT_DATA_1}) nor legacy EEG characteristics.'
            )

        self._impl = probe
        self._sync_impl()
        return True

    def stream_descriptors(self):
        if self._impl is not None:
            return self._impl.stream_descriptors()
        return Muse(self.address, **self._kwargs).stream_descriptors()
