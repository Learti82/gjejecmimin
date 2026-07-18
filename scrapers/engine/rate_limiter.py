"""Per-host rate limiter. Minimum 2 seconds between requests to the same host
(build spec section 4). Shared across the process so parallel configs hitting
the same site still cooperate."""

from __future__ import annotations

import threading
import time
from urllib.parse import urlparse


class RateLimiter:
    def __init__(self, min_interval_seconds: float = 2.0):
        self.min_interval = max(2.0, float(min_interval_seconds))
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, url: str) -> None:
        host = urlparse(url).netloc.lower()
        with self._lock:
            now = time.monotonic()
            last = self._last.get(host)
            if last is not None:
                elapsed = now - last
                if elapsed < self.min_interval:
                    time.sleep(self.min_interval - elapsed)
            self._last[host] = time.monotonic()
