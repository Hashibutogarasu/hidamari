import argparse
import sys

import pydbus
from gi.repository import GLib

from hidamari.commons import DBUS_NAME_SERVER

_PROPERTY_CONVERTERS = {
    "volume": int,
    "blur_radius": int,
    "is_mute": lambda v: v.lower() in ("1", "true", "yes", "on"),
    "is_paused_by_user": lambda v: v.lower() in ("1", "true", "yes", "on"),
    "is_static_wallpaper": lambda v: v.lower() in ("1", "true", "yes", "on"),
    "is_pause_when_maximized": lambda v: v.lower() in ("1", "true", "yes", "on"),
    "is_mute_when_maximized": lambda v: v.lower() in ("1", "true", "yes", "on"),
}


def _connect():
    """Connect to the running io.github.jeffshee.hidamari.server D-Bus service.

    Mirrors the fallback ControlPanel._connect_server() already uses: a
    server that isn't running (or hasn't started yet) is a normal, expected
    condition for a command-line caller, not an internal error.
    """
    try:
        return pydbus.SessionBus().get(DBUS_NAME_SERVER)
    except GLib.Error:
        return None


def cmd_get(server, name):
    print(getattr(server, name))


def cmd_set(server, name, raw_value):
    converter = _PROPERTY_CONVERTERS.get(name, str)
    setattr(server, name, converter(raw_value))


def cmd_call(server, method, args):
    getattr(server, method)(*args)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Command-line bridge to the running Hidamari D-Bus server, "
        "for use by the Plasma wallpaper plugin's QML config panel."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_parser = subparsers.add_parser("get", help="Read a server property")
    get_parser.add_argument("name")

    set_parser = subparsers.add_parser("set", help="Write a server property")
    set_parser.add_argument("name")
    set_parser.add_argument("value")

    call_parser = subparsers.add_parser("call", help="Call a server method")
    call_parser.add_argument("method")
    call_parser.add_argument("args", nargs="*")

    args = parser.parse_args(argv)

    server = _connect()
    if server is None:
        print("Hidamari server is not running", file=sys.stderr)
        return 1

    try:
        if args.command == "get":
            cmd_get(server, args.name)
        elif args.command == "set":
            cmd_set(server, args.name, args.value)
        elif args.command == "call":
            cmd_call(server, args.method, args.args)
    except GLib.Error as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
