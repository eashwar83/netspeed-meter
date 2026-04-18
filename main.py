"""NetSpeed Meter - A lightweight floating network speed overlay for Windows."""

import sys
import os

# Ensure the app directory is on the path when running as frozen exe
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

from overlay import SpeedOverlay
from tray import TrayIcon


def main():
    overlay = SpeedOverlay(
        on_quit=lambda: (tray.stop(), overlay.quit()),
        on_settings_changed=lambda: None,
    )
    tray = TrayIcon(overlay=overlay, on_quit=lambda: overlay.quit())
    tray.start()
    overlay.run()


if __name__ == "__main__":
    main()
