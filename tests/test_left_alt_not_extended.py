"""Alt must reach Windows as the LEFT Alt key.

Every key path (SendKeys, SendKey, PressKey, ReleaseKey) adds KEYEVENTF_EXTENDEDKEY. For Alt that
means right Alt, which AltGr layouts (French AZERTY, German QWERTZ) turn into Ctrl+Alt: Alt+Left
and Alt+D did nothing in Explorer while Ctrl+L worked. Other keys keep their flags.
"""

from unittest.mock import MagicMock, patch

from windows_mcp.uia import core

EXTENDED, KEYUP = 0x1, 0x2


def _sent(*calls):
    user32 = MagicMock()
    with patch.object(core.ctypes, "windll", MagicMock(user32=user32), create=True):
        for vk, flags in calls:
            core.keybd_event(vk, 0, flags, 0)
    return [(c.args[0], c.args[2]) for c in user32.keybd_event.call_args_list]


def test_alt_and_left_alt_are_sent_without_the_extended_flag():
    assert _sent((0x12, EXTENDED), (0x12, KEYUP | EXTENDED), (0xA4, EXTENDED)) == [
        (0x12, 0),
        (0x12, KEYUP),
        (0xA4, 0),
    ]


def test_other_keys_keep_their_flags():
    # VK_LEFT is a real extended key; Ctrl (0x11) and right Alt (0xA5) are left as the caller sent them.
    assert _sent((0x25, EXTENDED), (0x11, EXTENDED), (0xA5, EXTENDED), (0x25, KEYUP | EXTENDED)) == [
        (0x25, EXTENDED),
        (0x11, EXTENDED),
        (0xA5, EXTENDED),
        (0x25, KEYUP | EXTENDED),
    ]
