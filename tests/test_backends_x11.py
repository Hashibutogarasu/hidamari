import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hidamari.player.backends.x11 import _set_hint_if_supported


class SetHintIfSupportedTest(unittest.TestCase):
    """_set_hint_if_supported() must decide purely from what the running
    window manager advertises via EWMH `_NET_SUPPORTED`
    (Gdk.Screen.supports_net_wm_hint), never from which desktop environment
    is detected: some WMs accept `_NET_WM_WINDOW_TYPE_DESKTOP` without
    treating it as reason enough to hide the window from the taskbar/pager,
    and there's no reliable way to special-case that by DE name alone."""

    def test_applies_hint_when_wm_advertises_support(self):
        screen = MagicMock()
        screen.supports_net_wm_hint.return_value = True
        setter = MagicMock()

        _set_hint_if_supported(screen, "_NET_WM_STATE_SKIP_TASKBAR", setter)

        setter.assert_called_once_with(True)

    def test_does_not_apply_hint_when_wm_does_not_advertise_support(self):
        screen = MagicMock()
        screen.supports_net_wm_hint.return_value = False
        setter = MagicMock()

        _set_hint_if_supported(screen, "_NET_WM_STATE_SKIP_TASKBAR", setter)

        setter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
