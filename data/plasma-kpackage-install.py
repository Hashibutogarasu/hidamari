#!/usr/bin/env python3
"""Register the Hidamari Plasma wallpaper KPackage with kpackagetool5.

Meson's `install_subdir()` already copies the package into
`$prefix/share/plasma/wallpapers/`, which Plasma discovers by path alone.
This script is a best-effort addition on top of that: it asks
`kpackagetool5` to register (or, if already registered, upgrade) the
package, so its metadata cache stays in sync immediately after install.
"""

import shutil
import subprocess
import sys


def main():
    kpackagetool5 = shutil.which("kpackagetool5")
    if kpackagetool5 is None:
        return 0

    package_dir = sys.argv[1]
    install = subprocess.run(
        [kpackagetool5, "--type", "Plasma/Wallpaper", "--install", package_dir]
    )
    if install.returncode == 0:
        return 0

    upgrade = subprocess.run(
        [kpackagetool5, "--type", "Plasma/Wallpaper", "--upgrade", package_dir]
    )
    return upgrade.returncode


if __name__ == "__main__":
    sys.exit(main())
