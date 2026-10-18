"""A long Type must not destroy a clipboard that holds files or an image.

Long text is pasted through the clipboard, which saves and restores TEXT only: files cut in Explorer
(CF_HDROP) were lost, and the following Ctrl+V pasted nothing. When the clipboard holds anything
else than text, the text is typed key by key instead.
"""

from unittest.mock import MagicMock, patch

from windows_mcp.desktop.service import Desktop

SERVICE = "windows_mcp.desktop.service"
TEXT = "a long enough text to be pasted"


def _type(formats, open_fails=False):
    def enum(fmt):
        if fmt == 0:
            return formats[0] if formats else 0
        i = formats.index(fmt)
        return formats[i + 1] if i + 1 < len(formats) else 0

    clipboard = MagicMock()
    clipboard.EnumClipboardFormats.side_effect = enum
    if open_fails:
        clipboard.OpenClipboard.side_effect = OSError("clipboard busy")
    uia = MagicMock()
    with (
        patch.object(Desktop, "__init__", lambda self: None),
        patch.object(Desktop, "_validate_screen_point", lambda self, x, y: None),
        patch.object(Desktop, "_paste_text") as paste,
        patch(f"{SERVICE}.win32clipboard", clipboard),
        patch(f"{SERVICE}.uia", uia),
    ):
        Desktop().type((10, 10), TEXT)
    typed = "".join(c.args[0] for c in uia.SendKeys.call_args_list)
    return paste.called, typed, clipboard


def test_text_only_or_empty_clipboard_is_still_pasted():
    for formats in ([13, 16, 1, 7], []):
        pasted, typed, clipboard = _type(formats)
        assert pasted and typed == ""
        clipboard.CloseClipboard.assert_called_once()


def test_files_or_image_on_the_clipboard_are_kept_and_the_text_is_typed():
    for formats in ([15], [49171, 15], [13, 2]):  # CF_HDROP, a registered format, CF_BITMAP after text
        pasted, typed, clipboard = _type(formats)
        assert not pasted
        assert typed == TEXT
        clipboard.CloseClipboard.assert_called_once()


def test_unreadable_clipboard_is_left_alone():
    pasted, typed, _ = _type([], open_fails=True)
    assert not pasted and typed == TEXT
