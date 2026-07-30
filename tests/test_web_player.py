import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gi

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

from hidamari.player.web_player import WebWindow


def _make_window():
    """Build a WebWindow instance without running __init__, which spawns a
    real WebKit2.WebView unrelated to the button-press routing being
    tested."""
    window = WebWindow.__new__(WebWindow)
    window.menu = None
    return window


def _button_press_event(state=Gdk.ModifierType(0)):
    event = MagicMock()
    event.type = Gdk.EventType.BUTTON_PRESS
    event.button = 3
    event.state = state
    return event


class ButtonPressEventTest(unittest.TestCase):
    """Same rationale as tests/test_video_player.py: Shift+right-click must
    let the event fall through to the desktop environment's own context
    menu instead of being swallowed by Hidamari's (see #33)."""

    def test_plain_right_click_shows_hidamari_menu(self):
        window = _make_window()
        event = _button_press_event()

        with patch("hidamari.player.web_player.build_menu") as mock_build_menu:
            handled = window._on_button_press_event(None, event)

        self.assertTrue(handled)
        mock_build_menu.return_value.popup_at_pointer.assert_called_once()

    def test_shift_right_click_falls_through_to_the_desktop_environment(self):
        window = _make_window()
        event = _button_press_event(state=Gdk.ModifierType.SHIFT_MASK)

        with patch("hidamari.player.web_player.build_menu") as mock_build_menu:
            handled = window._on_button_press_event(None, event)

        self.assertFalse(handled)
        mock_build_menu.assert_not_called()


if __name__ == "__main__":
    unittest.main()
