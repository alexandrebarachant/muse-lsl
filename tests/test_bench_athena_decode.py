import time

import pytest

from muselsl.athena import decode_eeg, decode_optics


@pytest.mark.benchmark
def test_bench_eeg_decode():
    payload = bytes(28)
    start = time.perf_counter()
    for _ in range(10000):
        decode_eeg(payload, 4, 4)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0


@pytest.mark.benchmark
def test_bench_optics_decode():
    payload = bytes(40)
    start = time.perf_counter()
    for _ in range(10000):
        decode_optics(payload, 0x36, 16, 1)
    elapsed = time.perf_counter() - start
    assert elapsed < 8.0
