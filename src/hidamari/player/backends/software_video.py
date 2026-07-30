import ctypes

import cairo
import vlc


class _FrameBuffer:
    """Bridges a libvlc software (vmem) video callback to a Cairo-drawn Gtk.DrawingArea.

    Owns a single RGBA pixel buffer sized for the negotiated video dimensions
    and blits it into the widget's Cairo context on every `draw` signal,
    independent of the underlying window system (X11 or Wayland).
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.stride = width * 4
        self.buffer = (ctypes.c_ubyte * (self.stride * height))()
        self.buffer_ptr = ctypes.cast(self.buffer, ctypes.c_void_p)

        def lock(_opaque, planes):
            planes[0] = self.buffer_ptr
            return None

        def unlock(_opaque, _picture, _planes):
            return None

        def display(_opaque, _picture):
            self.widget.queue_draw()

        self.lock_cb = vlc.CallbackDecorators.VideoLockCb(lock)
        self.unlock_cb = vlc.CallbackDecorators.VideoUnlockCb(unlock)
        self.display_cb = vlc.CallbackDecorators.VideoDisplayCb(display)
        self.widget = None

    def draw(self, widget, cr):
        surface = cairo.ImageSurface.create_for_data(
            self.buffer, cairo.FORMAT_ARGB32, self.width, self.height, self.stride
        )
        cr.set_source_surface(surface, 0, 0)
        cr.paint()
        return False


def embed_video(vlc_player, drawing_area, width, height):
    """Embed a libvlc player into a Gtk.DrawingArea via software (vmem) callbacks.

    Works over both X11 and Wayland/EGL, at the cost of the CPU readback and
    blit that `VideoLockCb`/`VideoDisplayCb`-based rendering implies (see the
    libvlc `video_set_callbacks` docstring for the performance trade-off).
    """
    state = _FrameBuffer(width, height)
    state.widget = drawing_area
    vlc_player.video_set_callbacks(state.lock_cb, state.unlock_cb, state.display_cb, None)
    vlc_player.video_set_format("RV32", width, height, width * 4)
    drawing_area.connect("draw", state.draw)
    return state
