import numpy as np

from muselsl.timestamps import RLSTimestampCorrector


def _corrector(rate=256.0, t0=100.0):
    return RLSTimestampCorrector(rate, lambda: t0)


def test_timestamps_length_and_uniform_spacing():
    ts = _corrector().timestamps(4, host_time=100.0)
    assert len(ts) == 4
    diffs = np.diff(ts)
    assert np.allclose(diffs, diffs[0])          # uniformly spaced
    assert abs(diffs[0] - 1.0 / 256.0) < 1e-4    # close to nominal period


def test_timestamps_advance_across_packets():
    c = _corrector()
    ts0 = c.timestamps(2, host_time=100.0)
    ts1 = c.timestamps(2, host_time=100.1)
    assert ts1[0] > ts0[-1]


def test_rejects_nonpositive_rate():
    try:
        RLSTimestampCorrector(0, lambda: 0.0)
    except ValueError:
        return
    raise AssertionError('expected ValueError for non-positive sampling_rate')
