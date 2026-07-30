import ctypes

import gi

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk


def init_threads():
    """Initialize X11 threading so VLC can use X11-based hardware decoding.

    Required only on the X11/XWayland embedding path; `libX11.so.6` is the
    Fedora 33 fallback name for the same library.
    """
    for lib in ["libX11.so", "libX11.so.6"]:
        try:
            x11 = ctypes.cdll.LoadLibrary(lib)
        except OSError:
            continue
        x11.XInitThreads()
        break


def place_window(window, gdk_monitor):
    """Position a plain toplevel as an X11/XWayland desktop-hinted background window.

    Relies on the EWMH `_NET_WM_WINDOW_TYPE_DESKTOP` convention, which only
    applies to X11/XWayland-backed windows.
    """
    window.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
    rect = gdk_monitor.get_geometry()
    window.set_size_request(rect.width, rect.height)
    window.move(rect.x, rect.y)


def embed_video(vlc_player, drawing_area, _width, _height):
    """Embed a libvlc player into an X11/XWayland-backed GDK window via its XID.

    The XID is only available once the widget's GDK window is realized, so
    embedding is deferred to the widget's "realize" signal.
    """

    def handle_embed(*_args):
        vlc_player.set_xwindow(drawing_area.get_window().get_xid())
        return True

    drawing_area.connect("realize", handle_embed)
