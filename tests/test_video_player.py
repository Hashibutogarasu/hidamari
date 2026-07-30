import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import gi

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

from hidamari.player.video_player import PlayerWindow


def _make_window():
    """Build a PlayerWindow instance without running __init__, which spawns
    a real VLC instance and GDK window unrelated to the button-press
    routing being tested."""
    window = PlayerWindow.__new__(PlayerWindow)
    window.menu = None
    return window


def _button_press_event(state=Gdk.ModifierType(0)):
    event = MagicMock()
    event.type = Gdk.EventType.BUTTON_PRESS
    event.button = 3
    event.state = state
    return event


class ButtonPressEventTest(unittest.TestCase):
    """Right-clicking the wallpaper always shows Hidamari's own context menu,
    which sits directly on the desktop and so is otherwise the only thing a
    user can right-click — permanently hiding the desktop environment's own
    context menu (KDE's "Configure Desktop and Wallpaper", GNOME's desktop
    menu, etc). Shift+right-click must let that event fall through instead
    of being swallowed by Hidamari's menu (see #33)."""

    def test_plain_right_click_shows_hidamari_menu(self):
        window = _make_window()
        event = _button_press_event()

        with patch("hidamari.player.video_player.build_menu") as mock_build_menu:
            handled = window._on_button_press_event(None, event)

        self.assertTrue(handled)
        mock_build_menu.return_value.popup_at_pointer.assert_called_once()

    def test_shift_right_click_falls_through_to_the_desktop_environment(self):
        window = _make_window()
        event = _button_press_event(state=Gdk.ModifierType.SHIFT_MASK)

        with patch("hidamari.player.video_player.build_menu") as mock_build_menu:
            handled = window._on_button_press_event(None, event)

        self.assertFalse(handled)
        mock_build_menu.assert_not_called()


if __name__ == "__main__":
    unittest.main()
