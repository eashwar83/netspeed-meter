"""System tray icon with context menu."""

import threading
from PIL import Image, ImageDraw
import pystray


def _create_icon_image(color="#4fc3f7"):
    """Draw a small network-style icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Down arrow
    draw.polygon(
        [(10, 20), (30, 20), (20, 38)],
        fill="#4fc3f7",
    )
    # Up arrow
    draw.polygon(
        [(34, 38), (54, 38), (44, 20)],
        fill="#ef5350",
    )
    # Bottom bar
    draw.rectangle([8, 44, 56, 50], fill="#cccccc")

    return img


class TrayIcon:
    """System tray icon that provides show/hide and quit."""

    def __init__(self, on_quit):
        self.on_quit = on_quit
        self._icon = None
        self._thread = None

    def start(self):
        image = _create_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("NetSpeed Meter", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )
        self._icon = pystray.Icon("netspeed", image, "NetSpeed Meter", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def _on_quit(self, icon, item):
        self._icon.stop()
        self.on_quit()

    def stop(self):
        if self._icon:
            self._icon.stop()
