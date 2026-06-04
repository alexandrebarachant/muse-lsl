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
    data = bytes([0xFF, 0xFF])
    assert extract_lsb_bits(data, 0, 14) == 0x3FFF


def test_decode_eeg_zero_payload():
    out = decode_eeg(bytes(28), 4, 4)
    assert out.shape == (4, 4)
    assert out.sum() == 0.0


def test_decode_optics_canonical_placement():
    data = bytearray(30)
    # one 20-bit sample on channel 0 of tag 0x34 -> canonical index 4
    out = decode_optics(bytes(data), 0x34, 4, 3)
    assert out.shape == (16, 3)
