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
from muselsl.muse import Muse


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
    assert 'PPG' not in desc
    assert desc['OPTICS'].n_channels == 16
