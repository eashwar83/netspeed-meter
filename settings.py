"""Persistent settings management."""

import json
import os
import sys

DEFAULTS = {
    "theme": "dark",
    "position": "top-right",
    "custom_x": None,
    "custom_y": None,
    "default_x": None,
    "default_y": None,
    "opacity": 0.85,
    "update_interval": 1.0,
    "compact": False,
    "click_through": False,
    "auto_start": False,
}

SETTINGS_DIR = os.path.join(os.environ.get("APPDATA", ""), "NetSpeedMeter")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")


def load() -> dict:
    """Load settings from disk, falling back to defaults."""
    settings = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r") as f:
            saved = json.load(f)
        settings.update(saved)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return settings


def save(settings: dict):
    """Persist settings to disk."""
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def get_exe_path() -> str:
    """Return the path to the running executable or script."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(sys.argv[0])
