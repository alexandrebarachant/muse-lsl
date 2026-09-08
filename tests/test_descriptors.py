import pytest

from muselsl.athena import Athena
from muselsl.constants import (
    LSL_ACC_CHUNK,
    LSL_EEG_CHUNK,
    LSL_GYRO_CHUNK,
    LSL_PPG_CHUNK,
    MUSE_NB_ACC_CHANNELS,
    MUSE_NB_EEG_CHANNELS,
    MUSE_NB_GYRO_CHANNELS,
    MUSE_NB_PPG_CHANNELS,
    MUSE_SAMPLING_ACC_RATE,
    MUSE_SAMPLING_EEG_RATE,
    MUSE_SAMPLING_GYRO_RATE,
    MUSE_SAMPLING_PPG_RATE,
)
from muselsl.lsl_outlet import build_outlet
from muselsl.muse import Muse
from muselsl.stream import _descriptor_enabled


def _by_name(descriptors):
    return {d.name: d for d in descriptors}


def test_legacy_stream_descriptors_regression():
    desc = _by_name(Muse('addr').stream_descriptors())
    eeg = desc['EEG']
    assert eeg.n_channels == MUSE_NB_EEG_CHANNELS
    assert eeg.rate == MUSE_SAMPLING_EEG_RATE
    assert eeg.chunk == LSL_EEG_CHUNK
    assert eeg.channel_names == ('TP9', 'AF7', 'AF8', 'TP10', 'Right AUX')
    assert eeg.unit == 'microvolts'

    ppg = desc['PPG']
    assert ppg.n_channels == MUSE_NB_PPG_CHANNELS
    assert ppg.rate == MUSE_SAMPLING_PPG_RATE
    assert ppg.chunk == LSL_PPG_CHUNK
    assert ppg.channel_names == ('PPG1', 'PPG2', 'PPG3')

    acc = desc['ACC']
    assert acc.n_channels == MUSE_NB_ACC_CHANNELS
    assert acc.rate == MUSE_SAMPLING_ACC_RATE
    assert acc.chunk == LSL_ACC_CHUNK

    gyro = desc['GYRO']
    assert gyro.n_channels == MUSE_NB_GYRO_CHANNELS
    assert gyro.rate == MUSE_SAMPLING_GYRO_RATE
    assert gyro.chunk == LSL_GYRO_CHUNK


def test_athena_stream_descriptors():
    desc = _by_name(Athena('addr').stream_descriptors())
    assert desc['EEG'].n_channels == 4
    assert desc['EEG'].channel_names == ('TP9', 'AF7', 'AF8', 'TP10')
    # Athena PPG is delivered through the optics sensor; it is advertised as a PPG stream.
    optics = desc['OPTICS']
    assert optics.n_channels == 16
    assert optics.stype == 'PPG'


def test_ppg_flag_enables_athena_optics():
    # --ppg should enable the Athena optics/PPG stream.
    assert _descriptor_enabled('OPTICS', False, True, False, False, False)
    # --optics still works.
    assert _descriptor_enabled('OPTICS', False, False, False, False, True)
    # Disabled when neither flag is set.
    assert not _descriptor_enabled('OPTICS', False, False, False, False, False)


@pytest.mark.parametrize("descriptor", Muse('addr').stream_descriptors() + Athena('addr').stream_descriptors())
def test_build_outlet_smoke(descriptor):
    """Creating a StreamOutlet must not raise; guards against liblsl/pylsl packaging regressions."""
    outlet = build_outlet(descriptor, '00:00:00:00:00:00')
    assert outlet.get_info().type() == descriptor.stype
