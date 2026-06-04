def _cmd_bytes(cmd):
    return [len(cmd) + 1, *(ord(c) for c in cmd), ord('\n')]


def test_command_framing_v6():
    assert _cmd_bytes('v6') == [3, ord('v'), ord('6'), ord('\n')]


def test_command_framing_dc001():
    assert _cmd_bytes('dc001') == [6, ord('d'), ord('c'), ord('0'), ord('0'), ord('1'), ord('\n')]


def test_command_framing_preset():
    assert _cmd_bytes('p1041') == [6, ord('p'), ord('1'), ord('0'), ord('4'), ord('1'), ord('\n')]
