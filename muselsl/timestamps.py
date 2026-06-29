"""Host-time sample timestamping shared across Muse devices.

`RLSTimestampCorrector` maps a monotonic sample index to host time with a
recursive-least-squares regression, the same dejittering legacy `Muse` uses in
`_handle_eeg` (see muse.py). Athena multiplexes several streams at different
rates, so it keeps one corrector per stream rather than the single
EEG/PPG pair hard-coded on `Muse`.
"""

import numpy as np


class RLSTimestampCorrector:
    """Smooth, host-anchored per-sample timestamps for one fixed-rate stream.

    Each call to `timestamps` consumes the next `n_samples` indices, refits the
    regression against the packet's host arrival time, and returns the
    dejittered host timestamps for those samples.
    """

    def __init__(self, sampling_rate, time_func):
        if sampling_rate <= 0:
            raise ValueError(
                f'RLSTimestampCorrector: sampling_rate must be > 0, got {sampling_rate}'
            )
        self.sampling_rate = sampling_rate
        self.time_func = time_func
        self._sample_index = 0
        self._P = 1e-4
        # [intercept, slope]: intercept anchors index 0 at the first host time,
        # slope (~1/rate) is refit each packet to track real clock drift.
        self.reg_params = np.array([time_func(), 1.0 / sampling_rate])

    def timestamps(self, n_samples, host_time=None):
        if host_time is None:
            host_time = self.time_func()
        idxs = np.arange(n_samples) + self._sample_index
        self._sample_index += n_samples
        self._update(idxs[-1], host_time)
        return self.reg_params[1] * idxs + self.reg_params[0]

    def _update(self, t_source, t_receiver):
        """Recursive least squares step (see muse.py _update_timestamp_correction)."""
        t_receiver = t_receiver - self.reg_params[0]
        P = self._P
        R = self.reg_params[1]
        P = P - ((P ** 2) * (t_source ** 2)) / (1 - (P * (t_source ** 2)))
        R = R + P * t_source * (t_receiver - t_source * R)
        self.reg_params[1] = R
        self._P = P
