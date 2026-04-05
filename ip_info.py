"""Fetches external IP address and country via public geolocation APIs.

Tries multiple providers in order; the first one that responds wins.
This avoids hard dependency on a single service that may be blocked
or rate-limited on the user's network.
"""

import json
import threading
import time
import urllib.request
import urllib.error


# Providers are tried in order. Each entry maps an API URL to a parser
# that takes the decoded JSON dict and returns (ip, country, country_code).
def _parse_ipapi_co(data):
    return (
        data.get("ip"),
        data.get("country_name"),
        data.get("country_code"),
    )


def _parse_ipwho(data):
    if not data.get("success", True):
        raise ValueError(data.get("message", "API returned failure"))
    return (
        data.get("ip"),
        data.get("country"),
        data.get("country_code"),
    )


def _parse_ip_api(data):
    if data.get("status") and data["status"] != "success":
        raise ValueError(data.get("message", "API returned failure"))
    return (
        data.get("query"),
        data.get("country"),
        data.get("countryCode"),
    )


PROVIDERS = [
    ("https://ipapi.co/json/", _parse_ipapi_co),
    ("https://ipwho.is/", _parse_ipwho),
    ("http://ip-api.com/json/", _parse_ip_api),
]

REFRESH_INTERVAL = 300  # seconds between auto-refresh attempts (5 minutes)
REQUEST_TIMEOUT = 6  # seconds per provider


class IPInfoFetcher:
    """Background fetcher for external IP and country information."""

    def __init__(self, on_update=None):
        self.on_update = on_update
        self.ip = None
        self.country = None
        self.country_code = None
        self.error = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        """Start background thread that periodically fetches IP info."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background thread."""
        self._stop.set()

    def refresh(self):
        """Request an immediate refresh (runs in a new thread)."""
        t = threading.Thread(target=self._fetch_once, daemon=True)
        t.start()

    def _run(self):
        while not self._stop.is_set():
            self._fetch_once()
            for _ in range(REFRESH_INTERVAL):
                if self._stop.is_set():
                    return
                time.sleep(1)

    def _fetch_once(self):
        last_error = None
        for url, parser in PROVIDERS:
            if self._stop.is_set():
                return
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "NetSpeedMeter/1.0"},
                )
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                ip, country, country_code = parser(data)
                if not ip:
                    raise ValueError("No IP in response")

                with self._lock:
                    self.ip = ip
                    self.country = country
                    self.country_code = country_code
                    self.error = None

                if self.on_update:
                    try:
                        self.on_update()
                    except Exception:
                        pass
                return  # success, stop trying other providers
            except (urllib.error.URLError, TimeoutError, ValueError,
                    json.JSONDecodeError, OSError) as e:
                last_error = f"{type(e).__name__}: {e}"
                continue

        # All providers failed
        with self._lock:
            self.error = last_error or "All providers failed"

        if self.on_update:
            try:
                self.on_update()
            except Exception:
                pass

    def snapshot(self) -> dict:
        """Return a thread-safe copy of the current state."""
        with self._lock:
            return {
                "ip": self.ip,
                "country": self.country,
                "country_code": self.country_code,
                "error": self.error,
            }
