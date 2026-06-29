import numpy as np
import pytest

from muselsl.athena import decode_eeg, decode_optics, extract_lsb_bits


@pytest.mark.skip(reason='needs Athena capture')
def test_athena_eeg_decode():
    payload = bytes(28)
    out = decode_eeg(payload, 4, 4)
    assert out.shape == (4, 4)


@pytest.mark.skip(reason='needs Athena capture')
def test_athena_accgyro_decode():
    pass


@pytest.mark.skip(reason='needs Athena capture')
def test_athena_optics_decode():
    pass


def test_extract_lsb_bits_known_pattern():
    # bits 0-13 set -> 0x3FFF
    assert extract_lsb_bits(bytes([0xFF, 0xFF]), 0, 14) == 0x3FFF
    # LSB-first within each byte: bit 0 is the LSB of byte 0 (not the MSB)
    assert extract_lsb_bits(bytes([0x01, 0x00]), 0, 14) == 1
    # bit 8 is the LSB of byte 1
    assert extract_lsb_bits(bytes([0x00, 0x01]), 0, 14) == 1 << 8
    # a 2-bit window straddling the byte boundary (bit 7 = MSB of byte 0, bit 8 = LSB of byte 1)
    assert extract_lsb_bits(bytes([0x80, 0x01]), 7, 2) == 0b11


def test_decode_eeg_is_zero_centered():
    from muselsl.athena import EEG_MIDPOINT
    from muselsl.constants import MUSE_ATHENA_EEG_SCALE
    # all-zero raw decodes to -midpoint*scale (DC removed, like legacy Muse)
    out = decode_eeg(bytes(28), 4, 4)
    assert out.shape == (4, 4)
    assert np.allclose(out, -EEG_MIDPOINT * MUSE_ATHENA_EEG_SCALE)


def test_decode_optics_canonical_placement():
    data = bytearray(30)
    # one 20-bit sample on channel 0 of tag 0x34 -> canonical index 4
    out = decode_optics(bytes(data), 0x34, 4, 3)
    assert out.shape == (16, 3)
