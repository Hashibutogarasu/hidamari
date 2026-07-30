import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hidamari.player.base_player import set_click_passthrough


class SetClickPassthroughTest(unittest.TestCase):
    """set_click_passthrough() is how Shift+click reaches the desktop
    environment's own menu (see #35): an empty input region excludes the
    window from receiving clicks at the X11/Wayland level entirely, which a
    GTK signal handler returning False cannot do on its own (that only
    marks the event unhandled within this process, it doesn't redeliver the
    click to another top-level window)."""

    def test_enabling_passthrough_sets_an_empty_input_region(self):
        window = MagicMock()
        gdk_window = MagicMock()
        window.get_window.return_value = gdk_window

        set_click_passthrough(window, True)

        gdk_window.input_shape_combine_region.assert_called_once()
        region = gdk_window.input_shape_combine_region.call_args[0][0]
        self.assertEqual(region.num_rectangles(), 0)

    def test_disabling_passthrough_restores_the_full_window_region(self):
        window = MagicMock()
        gdk_window = MagicMock()
        window.get_window.return_value = gdk_window
        window.get_allocation.return_value = MagicMock(width=100, height=200)

        set_click_passthrough(window, False)

        gdk_window.input_shape_combine_region.assert_called_once()
        region = gdk_window.input_shape_combine_region.call_args[0][0]
        self.assertEqual(region.num_rectangles(), 1)

    def test_does_nothing_if_the_gdk_window_isnt_realized_yet(self):
        window = MagicMock()
        window.get_window.return_value = None

        set_click_passthrough(window, True)


if __name__ == "__main__":
    unittest.main()
