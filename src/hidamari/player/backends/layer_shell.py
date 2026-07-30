import gi


def is_supported() -> bool:
    """Check whether gtk-layer-shell is installed and the compositor supports it."""
    try:
        gi.require_version("GtkLayerShell", "0.1")
        from gi.repository import GtkLayerShell

        return GtkLayerShell.is_supported()
    except (ValueError, ImportError):
        return False


def place_window(window, gdk_monitor):
    """Anchor a toplevel to the background layer of the given output via gtk-layer-shell.

    This is the wlr-layer-shell (`zwlr_layer_shell_v1`) equivalent of the X11
    DESKTOP window-type hint: the surface is anchored to all four edges of
    `gdk_monitor`, placed on the background layer below normal windows, marked
    non-exclusive, and excluded from keyboard focus. Safe to call again on an
    already-initialized window (e.g. to reassign its monitor).
    """
    from gi.repository import GtkLayerShell

    if not GtkLayerShell.is_layer_window(window):
        GtkLayerShell.init_for_window(window)
        GtkLayerShell.set_layer(window, GtkLayerShell.Layer.BACKGROUND)
        GtkLayerShell.set_namespace(window, "hidamari-wallpaper")
        for edge in (
            GtkLayerShell.Edge.TOP,
            GtkLayerShell.Edge.BOTTOM,
            GtkLayerShell.Edge.LEFT,
            GtkLayerShell.Edge.RIGHT,
        ):
            GtkLayerShell.set_anchor(window, edge, True)
        GtkLayerShell.set_exclusive_zone(window, -1)
        GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.NONE)
    GtkLayerShell.set_monitor(window, gdk_monitor)
