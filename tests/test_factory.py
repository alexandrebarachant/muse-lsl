from muselsl.athena import Athena
from muselsl.devices import create_device, probe_athena, probe_legacy_eeg
from muselsl.muse import Muse


class _MockDevice:
    def __init__(self, chars):
        self._chars = {c.lower() for c in chars}

    def has_characteristic(self, uuid):
        return uuid.lower() in self._chars


def test_probe_athena_true():
    dev = _MockDevice(['273e0013-4c4d-454d-96be-f03bac821358'])
    assert probe_athena(dev) is True


def test_probe_athena_false_on_legacy():
    dev = _MockDevice(['273e0003-4c4d-454d-96be-f03bac821358'])
    assert probe_athena(dev) is False


def test_probe_legacy_eeg():
    dev = _MockDevice(['273e0003-4c4d-454d-96be-f03bac821358'])
    assert probe_legacy_eeg(dev) is True


def test_create_device_legacy():
    d = create_device('00:11:22:33:44:55', model='legacy')
    assert isinstance(d, Muse)


def test_create_device_athena():
    d = create_device('00:11:22:33:44:55', model='athena')
    assert isinstance(d, Athena)


def test_create_device_auto_type():
    d = create_device('00:11:22:33:44:55', model='auto')
    assert type(d).__name__ == '_AutoSelectingDevice'
