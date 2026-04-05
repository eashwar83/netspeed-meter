"""Network speed monitoring logic."""

import psutil
import time


class NetworkMonitor:
    """Tracks network bytes sent/received and calculates speed."""

    def __init__(self):
        counters = psutil.net_io_counters()
        self._last_recv = counters.bytes_recv
        self._last_sent = counters.bytes_sent
        self._last_time = time.monotonic()
        self.download_speed = 0.0
        self.upload_speed = 0.0
        self.connected = True

    def update(self):
        """Sample current counters and compute bytes/sec."""
        try:
            counters = psutil.net_io_counters()
            now = time.monotonic()
            dt = now - self._last_time
            if dt <= 0:
                return

            self.download_speed = (counters.bytes_recv - self._last_recv) / dt
            self.upload_speed = (counters.bytes_sent - self._last_sent) / dt

            self._last_recv = counters.bytes_recv
            self._last_sent = counters.bytes_sent
            self._last_time = now
            self.connected = True
        except Exception:
            self.download_speed = 0.0
            self.upload_speed = 0.0
            self.connected = False

    @staticmethod
    def format_speed(bytes_per_sec: float) -> str:
        """Format bytes/sec into a human-readable string."""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1024 * 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"
