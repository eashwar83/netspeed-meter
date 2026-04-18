"""System tray icon with context menu."""

import threading
from PIL import Image, ImageDraw
import pystray


POSITIONS = ("top-left", "top-right", "bottom-left", "bottom-right")
OPACITIES = (1.0, 0.9, 0.85, 0.75, 0.6)
INTERVALS = (0.5, 1.0, 2.0, 5.0)


def _create_icon_image(color="#4fc3f7"):
    """Draw a small network-style icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.polygon([(10, 20), (30, 20), (20, 38)], fill="#4fc3f7")
    draw.polygon([(34, 38), (54, 38), (44, 20)], fill="#ef5350")
    draw.rectangle([8, 44, 56, 50], fill="#cccccc")

    return img


class TrayIcon:
    """System tray icon mirroring the widget's right-click menu."""

    def __init__(self, overlay, on_quit):
        self.overlay = overlay
        self.on_quit = on_quit
        self._icon = None
        self._thread = None

    def start(self):
        image = _create_icon_image()
        self._icon = pystray.Icon(
            "netspeed", image, "NetSpeed Meter", self._build_menu()
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def _invoke(self, fn, *args):
        """Marshal pystray callbacks onto the Tk mainloop thread."""
        self.overlay.root.after(0, lambda: fn(*args))

    # Factories — pystray validates action signatures via co_argcount, so we
    # return closures that take exactly (icon, item) and close over bound values.
    def _action(self, fn, *args):
        def cb(icon, item):
            self._invoke(fn, *args)
        return cb

    def _check(self, predicate):
        def cb(item):
            return predicate()
        return cb

    def _build_menu(self):
        cfg = self.overlay.cfg
        overlay = self.overlay

        theme_menu = pystray.Menu(
            pystray.MenuItem(
                "Dark",
                self._action(overlay._set_theme, "dark"),
                checked=self._check(lambda: cfg["theme"] == "dark"),
                radio=True,
            ),
            pystray.MenuItem(
                "Light",
                self._action(overlay._set_theme, "light"),
                checked=self._check(lambda: cfg["theme"] == "light"),
                radio=True,
            ),
        )

        position_menu = pystray.Menu(*[
            pystray.MenuItem(
                p.replace("-", " ").title(),
                self._action(overlay._set_position, p),
                checked=self._check(lambda p=p: cfg["position"] == p),
                radio=True,
            )
            for p in POSITIONS
        ])

        opacity_menu = pystray.Menu(*[
            pystray.MenuItem(
                f"{int(v * 100)}%",
                self._action(overlay._set_opacity, v),
                checked=self._check(lambda v=v: cfg["opacity"] == v),
                radio=True,
            )
            for v in OPACITIES
        ])

        interval_menu = pystray.Menu(*[
            pystray.MenuItem(
                f"{v}s",
                self._action(overlay._set_interval, v),
                checked=self._check(lambda v=v: cfg["update_interval"] == v),
                radio=True,
            )
            for v in INTERVALS
        ])

        return pystray.Menu(
            pystray.MenuItem("NetSpeed Meter", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Theme", theme_menu),
            pystray.MenuItem("Position", position_menu),
            pystray.MenuItem("Opacity", opacity_menu),
            pystray.MenuItem("Update Interval", interval_menu),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Compact Mode",
                self._action(overlay._toggle_compact),
                checked=self._check(lambda: cfg["compact"]),
            ),
            pystray.MenuItem(
                "Click-Through",
                self._action(overlay._toggle_click_through),
                checked=self._check(lambda: cfg["click_through"]),
            ),
            pystray.MenuItem(
                "Start with Windows",
                self._action(overlay._toggle_auto_start),
                checked=self._check(lambda: cfg.get("auto_start", False)),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Refresh IP",
                self._action(overlay.ip_fetcher.refresh),
            ),
            pystray.MenuItem(
                "Set Default Position",
                self._action(overlay._set_default_position),
            ),
            pystray.MenuItem(
                "Reset Position",
                self._action(overlay._reset_position),
            ),
            pystray.MenuItem("Quit", self._on_quit),
        )

    def _on_quit(self, icon, item):
        self._icon.stop()
        self.on_quit()

    def stop(self):
        if self._icon:
            self._icon.stop()
