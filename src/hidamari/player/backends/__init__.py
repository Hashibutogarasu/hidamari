def get_window_backend():
    """Return the (placement, video) backend module pair for the current session.

    Both modules expose the same `place_window(window, gdk_monitor)` and
    `embed_video(...)` signatures, so callers never need to branch on which
    backend was chosen.
    """
    from hidamari.utils import should_use_layer_shell

    if should_use_layer_shell():
        from hidamari.player.backends import layer_shell, software_video

        return layer_shell, software_video
    from hidamari.player.backends import x11

    return x11, x11
