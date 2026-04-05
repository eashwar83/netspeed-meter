"""Floating overlay window for displaying network speed."""

import tkinter as tk
from monitor import NetworkMonitor
from ip_info import IPInfoFetcher
import settings


THEMES = {
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "label": "#888888",
        "down_arrow": "#4fc3f7",
        "up_arrow": "#ef5350",
        "border": "#333333",
        "disconnected": "#ff9800",
    },
    "light": {
        "bg": "#f5f5f5",
        "fg": "#1e1e1e",
        "label": "#666666",
        "down_arrow": "#0277bd",
        "up_arrow": "#c62828",
        "border": "#cccccc",
        "disconnected": "#e65100",
    },
}

POSITIONS = {
    "top-left": (10, 10),
    "top-right": (-10, 10),
    "bottom-left": (10, -10),
    "bottom-right": (-10, -10),
}


class SpeedOverlay:
    """Transparent, always-on-top overlay showing network speeds."""

    def __init__(self, on_quit, on_settings_changed):
        self.on_quit = on_quit
        self.on_settings_changed = on_settings_changed
        self.cfg = settings.load()
        self.monitor = NetworkMonitor()
        self.ip_fetcher = IPInfoFetcher()
        self.ip_fetcher.start()
        self.dragging = False
        self.drag_x = 0
        self.drag_y = 0
        self.custom_position = False

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.cfg["opacity"])

        # Remove window from taskbar on Windows
        self.root.attributes("-toolwindow", True)

        self._build_ui()
        self._apply_theme()
        self._position_window()
        self._bind_events()

        self.root.deiconify()
        self._tick()

    def _build_ui(self):
        theme = THEMES[self.cfg["theme"]]

        self.frame = tk.Frame(
            self.root,
            bg=theme["bg"],
            highlightbackground=theme["border"],
            highlightthickness=1,
            padx=8,
            pady=4,
        )
        self.frame.pack(fill=tk.BOTH, expand=True)

        if self.cfg["compact"]:
            self._build_compact(theme)
        else:
            self._build_full(theme)

    def _build_full(self, theme):
        row_down = tk.Frame(self.frame, bg=theme["bg"])
        row_down.pack(fill=tk.X, pady=(2, 0))

        self.down_arrow = tk.Label(
            row_down, text="\u25bc", fg=theme["down_arrow"],
            bg=theme["bg"], font=("Segoe UI", 9),
        )
        self.down_arrow.pack(side=tk.LEFT, padx=(0, 4))

        self.down_label = tk.Label(
            row_down, text="0 B/s", fg=theme["fg"],
            bg=theme["bg"], font=("Segoe UI Semibold", 10),
            anchor="e", width=12,
        )
        self.down_label.pack(side=tk.LEFT)

        row_up = tk.Frame(self.frame, bg=theme["bg"])
        row_up.pack(fill=tk.X, pady=(0, 2))

        self.up_arrow = tk.Label(
            row_up, text="\u25b2", fg=theme["up_arrow"],
            bg=theme["bg"], font=("Segoe UI", 9),
        )
        self.up_arrow.pack(side=tk.LEFT, padx=(0, 4))

        self.up_label = tk.Label(
            row_up, text="0 B/s", fg=theme["fg"],
            bg=theme["bg"], font=("Segoe UI Semibold", 10),
            anchor="e", width=12,
        )
        self.up_label.pack(side=tk.LEFT)

        # IP + country row (separator + info)
        sep = tk.Frame(self.frame, bg=theme["border"], height=1)
        sep.pack(fill=tk.X, pady=(3, 2))

        self.ip_label = tk.Label(
            self.frame, text="Looking up IP\u2026", fg=theme["label"],
            bg=theme["bg"], font=("Segoe UI", 8),
            anchor="w",
        )
        self.ip_label.pack(fill=tk.X, pady=(0, 2))

        self.status_label = None

    def _build_compact(self, theme):
        row = tk.Frame(self.frame, bg=theme["bg"])
        row.pack(fill=tk.X)

        self.down_arrow = tk.Label(
            row, text="\u25bc", fg=theme["down_arrow"],
            bg=theme["bg"], font=("Segoe UI", 8),
        )
        self.down_arrow.pack(side=tk.LEFT)

        self.down_label = tk.Label(
            row, text="0 B/s", fg=theme["fg"],
            bg=theme["bg"], font=("Segoe UI", 9),
            anchor="e", width=10,
        )
        self.down_label.pack(side=tk.LEFT)

        self.up_arrow = tk.Label(
            row, text="\u25b2", fg=theme["up_arrow"],
            bg=theme["bg"], font=("Segoe UI", 8),
        )
        self.up_arrow.pack(side=tk.LEFT, padx=(6, 0))

        self.up_label = tk.Label(
            row, text="0 B/s", fg=theme["fg"],
            bg=theme["bg"], font=("Segoe UI", 9),
            anchor="e", width=10,
        )
        self.up_label.pack(side=tk.LEFT)

        # IP + country on the same row, separated by a thin divider
        self.ip_sep = tk.Label(
            row, text=" | ", fg=theme["label"],
            bg=theme["bg"], font=("Segoe UI", 9),
        )
        self.ip_sep.pack(side=tk.LEFT)

        self.ip_label = tk.Label(
            row, text="\u2026", fg=theme["label"],
            bg=theme["bg"], font=("Segoe UI", 8),
            anchor="w",
        )
        self.ip_label.pack(side=tk.LEFT)

        self.status_label = None

    def _apply_theme(self):
        theme = THEMES[self.cfg["theme"]]
        self.frame.config(bg=theme["bg"], highlightbackground=theme["border"])
        for widget in self.frame.winfo_children():
            self._apply_bg_recursive(widget, theme["bg"])

    def _apply_bg_recursive(self, widget, bg):
        try:
            widget.config(bg=bg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._apply_bg_recursive(child, bg)

    def _position_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        pos = self.cfg["position"]
        ox, oy = POSITIONS.get(pos, POSITIONS["top-right"])

        x = ox if ox >= 0 else sw + ox - w
        y = oy if oy >= 0 else sh + oy - h

        self.root.geometry(f"+{x}+{y}")

    def _bind_events(self):
        widgets = [self.frame, self.down_arrow, self.down_label,
                   self.up_arrow, self.up_label, self.ip_label]
        if hasattr(self, "ip_sep"):
            widgets.append(self.ip_sep)
        for widget in widgets:
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<ButtonRelease-1>", self._on_drag_end)
            widget.bind("<Button-3>", self._show_context_menu)

    def _on_drag_start(self, event):
        if self.cfg["click_through"]:
            return
        self.dragging = True
        self.drag_x = event.x_root - self.root.winfo_x()
        self.drag_y = event.y_root - self.root.winfo_y()

    def _on_drag_motion(self, event):
        if not self.dragging:
            return
        x = event.x_root - self.drag_x
        y = event.y_root - self.drag_y
        self.root.geometry(f"+{x}+{y}")
        self.custom_position = True

    def _on_drag_end(self, event):
        self.dragging = False

    def _show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        theme = self.cfg["theme"]

        # Theme submenu
        theme_menu = tk.Menu(menu, tearoff=0)
        for t in ("dark", "light"):
            label = f"{'* ' if theme == t else '  '}{t.title()}"
            theme_menu.add_command(label=label,
                                   command=lambda t=t: self._set_theme(t))
        menu.add_cascade(label="Theme", menu=theme_menu)

        # Position submenu
        pos_menu = tk.Menu(menu, tearoff=0)
        for p in POSITIONS:
            label = f"{'* ' if self.cfg['position'] == p else '  '}{p.replace('-', ' ').title()}"
            pos_menu.add_command(label=label,
                                 command=lambda p=p: self._set_position(p))
        menu.add_cascade(label="Position", menu=pos_menu)

        # Opacity submenu
        opacity_menu = tk.Menu(menu, tearoff=0)
        for val in (1.0, 0.9, 0.85, 0.75, 0.6):
            pct = int(val * 100)
            label = f"{'* ' if self.cfg['opacity'] == val else '  '}{pct}%"
            opacity_menu.add_command(label=label,
                                      command=lambda v=val: self._set_opacity(v))
        menu.add_cascade(label="Opacity", menu=opacity_menu)

        # Update interval submenu
        interval_menu = tk.Menu(menu, tearoff=0)
        for val in (0.5, 1.0, 2.0, 5.0):
            label = f"{'* ' if self.cfg['update_interval'] == val else '  '}{val}s"
            interval_menu.add_command(
                label=label,
                command=lambda v=val: self._set_interval(v),
            )
        menu.add_cascade(label="Update Interval", menu=interval_menu)

        menu.add_separator()

        # Toggle options
        menu.add_command(
            label=f"{'Disable' if self.cfg['compact'] else 'Enable'} Compact Mode",
            command=self._toggle_compact,
        )
        menu.add_command(
            label=f"{'Disable' if self.cfg['click_through'] else 'Enable'} Click-Through",
            command=self._toggle_click_through,
        )
        menu.add_command(
            label=f"{'Disable' if self.cfg.get('auto_start') else 'Enable'} Start with Windows",
            command=self._toggle_auto_start,
        )

        menu.add_separator()
        menu.add_command(label="Refresh IP", command=self.ip_fetcher.refresh)
        menu.add_command(label="Quit", command=self.on_quit)

        menu.tk_popup(event.x_root, event.y_root)

    def _set_theme(self, theme):
        self.cfg["theme"] = theme
        self._rebuild()

    def _set_position(self, pos):
        self.cfg["position"] = pos
        self.custom_position = False
        self._position_window()
        self._save()

    def _set_opacity(self, val):
        self.cfg["opacity"] = val
        self.root.attributes("-alpha", val)
        self._save()

    def _set_interval(self, val):
        self.cfg["update_interval"] = val
        self._save()

    def _toggle_compact(self):
        self.cfg["compact"] = not self.cfg["compact"]
        self._rebuild()

    def _toggle_click_through(self):
        self.cfg["click_through"] = not self.cfg["click_through"]
        self._save()

    def _toggle_auto_start(self):
        self.cfg["auto_start"] = not self.cfg["auto_start"]
        self._update_auto_start()
        self._save()

    def _update_auto_start(self):
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "NetSpeedMeter"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                winreg.KEY_SET_VALUE)
            if self.cfg["auto_start"]:
                exe = settings.get_exe_path()
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except OSError:
            pass

    def _rebuild(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.frame.destroy()
        if hasattr(self, "ip_sep"):
            del self.ip_sep
        self._build_ui()
        if not self.custom_position:
            self._position_window()
        self._bind_events()
        self._save()

    def _save(self):
        settings.save(self.cfg)
        self.on_settings_changed()

    def _tick(self):
        self.monitor.update()
        theme = THEMES[self.cfg["theme"]]

        if self.monitor.connected:
            self.down_label.config(
                text=NetworkMonitor.format_speed(self.monitor.download_speed),
                fg=theme["fg"],
            )
            self.up_label.config(
                text=NetworkMonitor.format_speed(self.monitor.upload_speed),
                fg=theme["fg"],
            )
        else:
            self.down_label.config(text="No connection", fg=theme["disconnected"])
            self.up_label.config(text="", fg=theme["disconnected"])

        self._update_ip_label(theme)

        interval_ms = int(self.cfg["update_interval"] * 1000)
        self.root.after(interval_ms, self._tick)

    def _update_ip_label(self, theme):
        """Update the IP/country label with the latest fetched info."""
        info = self.ip_fetcher.snapshot()
        if info["ip"]:
            if self.cfg["compact"]:
                cc = info["country_code"] or ""
                text = f"{info['ip']} {cc}".strip()
            else:
                country = info["country"] or info["country_code"] or ""
                text = f"{info['ip']}  \u00b7  {country}" if country else info["ip"]
            self.ip_label.config(text=text, fg=theme["label"])
        elif info["error"]:
            self.ip_label.config(
                text="IP lookup failed" if not self.cfg["compact"] else "\u2014",
                fg=theme["disconnected"],
            )
        else:
            self.ip_label.config(
                text="Looking up IP\u2026" if not self.cfg["compact"] else "\u2026",
                fg=theme["label"],
            )

    def run(self):
        self.root.mainloop()

    def quit(self):
        self.ip_fetcher.stop()
        self.root.quit()
        self.root.destroy()
