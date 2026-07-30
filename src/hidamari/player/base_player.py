import logging
import multiprocessing as mp
import sys
from abc import abstractmethod

import cairo
import gi
import setproctitle

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk
from pydbus import SessionBus

from hidamari.commons import DBUS_NAME_PLAYER, LOGGER_NAME, PROJECT
from hidamari.player.backends import get_window_backend
from hidamari.utils import gnome_desktop_icon_workaround

logger = logging.getLogger(LOGGER_NAME)

APP_ID = f"{PROJECT}.player"
SHIFT_POLL_INTERVAL_MS = 100


def is_shift_held():
    """Check whether Shift is currently held, independent of keyboard focus.

    DESKTOP-hinted/layer-shell background windows don't receive keyboard
    focus, so a regular `key-press-event` can't reliably report this;
    polling the pointer device's modifier state works regardless of focus.
    """
    display = Gdk.Display.get_default()
    seat = display.get_default_seat()
    pointer = seat.get_pointer()
    root = display.get_default_screen().get_root_window()
    state = root.get_device_position(pointer)
    return bool(state.mask & Gdk.ModifierType.SHIFT_MASK)


def set_click_passthrough(window, enabled):
    """Make `window` let every pointer click through to whatever is beneath it
    (enabled=True) or receive clicks normally again (enabled=False).

    Returning False from a GTK button-press handler only marks the event as
    unhandled within this process; it does not redeliver the same click to
    another top-level window (the desktop/compositor). An empty input
    region is what actually excludes the window from receiving the click at
    the X11/Wayland level, letting it reach the desktop environment's own
    context menu instead.
    """
    gdk_window = window.get_window()
    if gdk_window is None:
        return
    if enabled:
        gdk_window.input_shape_combine_region(cairo.Region(), 0, 0)
    else:
        alloc = window.get_allocation()
        full_region = cairo.Region(cairo.RectangleInt(0, 0, alloc.width, alloc.height))
        gdk_window.input_shape_combine_region(full_region, 0, 0)


class DummyWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BasePlayer(Gtk.Application):
    """
    <node>
    <interface name='io.github.jeffshee.hidamari.player'>
        <property name="mode" type="s" access="read"/>
        <property name="data_source" type="s" access="readwrite"/>
        <property name="volume" type="i" access="readwrite"/>
        <property name="is_mute" type="b" access="readwrite"/>
        <property name="is_playing" type="b" access="read"/>
        <method name='pause_playback'/>
        <method name='start_playback'/>
        <method name='quit_player'/>
    </interface>
    </node>
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs
        )
        setproctitle.setproctitle(mp.current_process().name)
        self.windows = dict()
        self._shift_held = False
        self._monitor_detect()
        GLib.timeout_add(SHIFT_POLL_INTERVAL_MS, self._poll_shift_state)

    def _poll_shift_state(self):
        shift_held = is_shift_held()
        if shift_held != self._shift_held:
            self._shift_held = shift_held
            for window in self.windows.values():
                if window:
                    set_click_passthrough(window, shift_held)
        return True

    def _monitor_detect(self):
        display = Gdk.Display.get_default()
        screen = display.get_default_screen()

        for i in range(display.get_n_monitors()):
            monitor = display.get_monitor(i)
            if monitor not in self.windows:
                self.windows[monitor] = None

        screen.connect("size-changed", self._on_size_changed)
        display.connect("monitor-added", self._on_monitor_added)
        display.connect("monitor-removed", self._on_monitor_removed)

    def new_window(self, gdk_monitor):
        # Override here for different window
        # NOTE: Don't forget to set the application=self, otherwise the application will quit immediately lol
        return DummyWindow(application=self)

    def _on_size_changed(self, *args):
        logger.info("[Player] size-changed")
        placement, _video = get_window_backend()
        for monitor, window in self.windows.items():
            if window:
                placement.place_window(window, monitor)

    def _on_monitor_added(self, _, gdk_monitor, *args):
        logger.info("[Player] monitor-added")
        self.windows[gdk_monitor] = None
        self.do_activate()

    def _on_monitor_removed(self, _, gdk_monitor, *args):
        logger.info("[Player] monitor-removed")
        del self.windows[gdk_monitor]

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        placement, _video = get_window_backend()
        for monitor in self.windows:
            if not self.windows[monitor]:
                window = self.new_window(monitor)
                placement.place_window(window, monitor)
                self.windows[monitor] = window
            self.windows[monitor].present()
        gnome_desktop_icon_workaround()

    @property
    @abstractmethod
    def mode(self):
        pass

    @property
    @abstractmethod
    def data_source(self):
        pass

    @data_source.setter
    def data_source(self, data_source):
        pass

    @property
    @abstractmethod
    def volume(self):
        pass

    @volume.setter
    def volume(self, volume):
        pass

    @property
    @abstractmethod
    def is_mute(self):
        pass

    @is_mute.setter
    def is_mute(self, is_mute):
        pass

    @property
    @abstractmethod
    def is_playing(self):
        pass

    @abstractmethod
    def pause_playback(self):
        pass

    @abstractmethod
    def start_playback(self):
        pass

    def quit_player(self):
        self.quit()


def main():
    bus = SessionBus()
    app = BasePlayer()
    try:
        bus.publish(DBUS_NAME_PLAYER, app)
    except RuntimeError as e:
        logger.error(e)
    app.run(sys.argv)


if __name__ == "__main__":
    main()
