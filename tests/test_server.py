import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hidamari.commons import CONFIG_KEY_DATA_SOURCE, CONFIG_KEY_MODE, CONFIG_KEY_SYSTRAY, MODE_VIDEO
from hidamari.server import HidamariServer


def _make_server(config):
    """Build a HidamariServer instance without running __init__, which spawns
    GTK/D-Bus/subprocess side effects unrelated to _setup_player()'s config
    handling."""
    server = HidamariServer.__new__(HidamariServer)
    server.config = config
    server._prev_mode = None
    server._player_count = 0
    server.player_process = None
    server.sys_icon_process = None
    server.localedir = "/usr/share/locale"
    return server


class SetupPlayerConfigPersistenceTest(unittest.TestCase):
    """A newly spawned player process reads config.json from disk on its own
    (ConfigUtil().load() in its own __init__), independent of the server's
    in-memory self.config. Any data_source change made through
    _setup_player() must therefore be written to disk before the new process
    starts, or the new process silently plays the stale source instead of
    the one just requested (e.g. via the Plasma config panel's file picker,
    which only talks to the server over D-Bus and never touches
    config.json itself).

    ConfigUtil is patched in setUp() for every test in this class, never
    per-test: _setup_player() calling the real ConfigUtil().save() would
    overwrite the current user's actual ~/.config/hidamari/config.json.
    """

    def setUp(self):
        config_util_patcher = patch("hidamari.server.ConfigUtil")
        self.mock_config_util = config_util_patcher.start()
        self.addCleanup(config_util_patcher.stop)

        process_patcher = patch("hidamari.server.Process")
        process_patcher.start()
        self.addCleanup(process_patcher.stop)

        quit_player_patcher = patch.object(HidamariServer, "_quit_player")
        quit_player_patcher.start()
        self.addCleanup(quit_player_patcher.stop)

    def _base_config(self):
        return {
            CONFIG_KEY_MODE: MODE_VIDEO,
            CONFIG_KEY_DATA_SOURCE: {"Default": "/old/default.mp4", "eDP-1": "/old/edp1.mp4"},
            CONFIG_KEY_SYSTRAY: False,
        }

    def test_new_data_source_is_persisted_to_disk(self):
        server = _make_server(self._base_config())
        server.video("/new/video.mp4", "Default")
        self.mock_config_util.return_value.save.assert_called_once()
        saved_config = self.mock_config_util.return_value.save.call_args[0][0]
        self.assertEqual(saved_config[CONFIG_KEY_DATA_SOURCE]["Default"], "/new/video.mp4")

    def test_reload_with_no_data_source_does_not_clear_default(self):
        server = _make_server(self._base_config())
        server.video()
        self.assertEqual(server.config[CONFIG_KEY_DATA_SOURCE]["Default"], "/old/default.mp4")

    def test_specific_monitor_update_does_not_touch_other_monitors(self):
        server = _make_server(self._base_config())
        server.video("/new/video.mp4", "eDP-1")
        self.assertEqual(server.config[CONFIG_KEY_DATA_SOURCE]["eDP-1"], "/new/video.mp4")

    def test_feeling_lucky_style_call_does_not_touch_other_monitors(self):
        """feeling_lucky() sets each monitor's data_source itself, then calls
        self.video(video_path) with no monitor argument purely to trigger a
        player restart. That call must not clobber the per-monitor sources
        feeling_lucky() just set."""
        server = _make_server(self._base_config())
        server.video("/new/video.mp4")
        self.assertEqual(server.config[CONFIG_KEY_DATA_SOURCE]["eDP-1"], "/old/edp1.mp4")

    def test_default_monitor_update_applies_to_all_monitors(self):
        """The Plasma config panel's file picker has no per-monitor concept
        and always calls video(path, "Default") (see plasma_bridge.py). Since
        VideoPlayer.data_source prefers a monitor's own key over "Default"
        whenever that key exists and is non-empty, an explicit "Default"
        request must update every monitor's entry too, or the picked file
        never actually reaches any monitor that already has its own key."""
        server = _make_server(self._base_config())
        server.video("/new/video.mp4", "Default")
        self.assertEqual(server.config[CONFIG_KEY_DATA_SOURCE]["eDP-1"], "/new/video.mp4")


if __name__ == "__main__":
    unittest.main()
