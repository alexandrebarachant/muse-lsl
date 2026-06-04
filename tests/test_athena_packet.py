import struct

from muselsl.athena import (
    iter_sensor_blocks,
    split_packets,
    decode_acc_gyro,
    decode_battery,
    optics_canonical_index,
)


def _build_eeg_packet(device_tick=1000, payload=None):
    payload = payload or bytes(28)
    packet_len = 14 + len(payload)
    pkt = bytearray(packet_len)
    pkt[0] = packet_len
    struct.pack_into('<H', pkt, 1, 7)
    struct.pack_into('<I', pkt, 2, device_tick)
    pkt[9] = 0x11
    pkt[10] = 0
    pkt[14:] = payload
    return bytes(pkt)


def test_split_packets_single():
    pkt = _build_eeg_packet()
    assert split_packets(pkt) == [pkt]


def test_split_packets_concatenated():
    p1 = _build_eeg_packet(device_tick=1)
    p2 = _build_eeg_packet(device_tick=2)
    both = p1 + p2
    assert split_packets(both) == [p1, p2]


def test_split_packets_rejects_bad_length():
    bad = bytes([5, 0, 0, 0, 0])
    assert split_packets(bad) == []


def test_iter_sensor_blocks_primary_eeg():
    pkt = _build_eeg_packet(device_tick=12345)
    blocks = list(iter_sensor_blocks(pkt))
    assert len(blocks) == 1
    tag, _pkg, tick, payload = blocks[0]
    assert tag == 0x11
    assert tick == 12345
    assert len(payload) == 28


def test_iter_sensor_blocks_subpacket():
    primary = bytes(28)
    sub_hdr = bytes([0x47, 1, 0, 0, 0])
    sub_payload = bytes(36)
    payload = primary + sub_hdr + sub_payload
    pkt = _build_eeg_packet(payload=payload)
    # primary tag 0x11 consumes 28 bytes; subpacket 0x47 follows
    pkt = bytearray(pkt)
    pkt[0] = 14 + len(payload)
    pkt = bytes(pkt)
    blocks = list(iter_sensor_blocks(pkt))
    tags = [b[0] for b in blocks]
    assert tags == [0x11, 0x47]


def test_decode_acc_gyro_shapes():
    data = bytearray(36)
    for i in range(18):
        struct.pack_into('<h', data, i * 2, i - 5)
    acc, gyro = decode_acc_gyro(bytes(data), 3)
    assert acc.shape == (3, 3)
    assert gyro.shape == (3, 3)
    assert gyro[0, 0] < 0 or acc[0, 0] != 0


def test_decode_battery():
    assert decode_battery(struct.pack('<H', 256)) == 1.0


def test_optics_canonical_index():
    assert optics_canonical_index(0x34, 0) == 4
    assert optics_canonical_index(0x35, 3) == 3
    assert optics_canonical_index(0x36, 15) == 15
