"""Check continuous-mode _save appends each sample exactly once.

Regression test for the save-boundary bug where rows were duplicated/dropped
because the append cutoff was a timestamp in the wrong clock. Run: pytest.
"""
import os
import tempfile

import numpy as np
import pandas as pd

from muselsl.record import _save

CH = ["c0", "c1"]


def test_no_duplicate_or_dropped_rows_across_flush():
    # nonzero time_correction is what used to shift the boundary and dup a row
    tc = 1.5
    raw = np.arange(0, 30, dtype=float)            # 30 samples, 1 Hz raw
    res = [raw.reshape(-1, 1).repeat(2, axis=1)]   # (30, 2) data
    ts = list(raw)

    with tempfile.TemporaryDirectory() as d:
        fn = os.path.join(d, "rec.csv")

        # flush 1: first 20 samples (file does not exist -> whole write)
        n = _save(fn, [res[0][:20]], ts[:20], tc, False, False, [], CH, 0, n_written=0)
        assert n == 20

        # flush 2: full buffer of 30, only 10 new rows should be appended
        n = _save(fn, [res[0]], ts, tc, False, False, [], CH, 0, n_written=n)
        assert n == 30

        out = pd.read_csv(fn)
        assert len(out) == 30, "row count drifted -> duplicate or dropped sample"
        assert out["timestamps"].is_monotonic_increasing
        assert out["timestamps"].is_unique
        # timestamps carry the correction exactly once
        assert np.allclose(out["timestamps"].values, raw + tc)


if __name__ == "__main__":
    test_no_duplicate_or_dropped_rows_across_flush()
    print("ok")
