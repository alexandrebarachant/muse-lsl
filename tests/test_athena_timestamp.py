import numpy as np

from muselsl.athena import device_tick_delta, sample_timestamps


def test_device_tick_delta_wraparound():
    assert device_tick_delta(10, 0xFFFFFFF0) == 26


def test_sample_timestamps_spacing():
    ts = sample_timestamps(
        device_tick=1000,
        n_samples=4,
        sampling_rate=256.0,
        t0_tick=1000,
        t0_host=100.0,
        time_func=None,
    )
    assert len(ts) == 4
    assert np.allclose(np.diff(ts), 1.0 / 256.0)


def test_sample_timestamps_advances_with_tick():
    ts0 = sample_timestamps(1000, 2, 256.0, 1000, 0.0, None)
    ts1 = sample_timestamps(2000, 2, 256.0, 1000, 0.0, None)
    assert ts1[0] > ts0[0]
