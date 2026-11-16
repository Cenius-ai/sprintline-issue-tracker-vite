"""Small in-process, windowed rate limiter for the login endpoint.

Single-process deployment: a dict of counters keyed by ``(scope, window)``. The
window resets by construction because the key embeds the window index, and the
map is pruned so it cannot grow without bound.
"""

from __future__ import annotations

import threading
import time

_lock = threading.Lock()
_counters: dict[tuple[str, int], int] = {}
_MAX_KEYS = 4096


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = max(limit, 1)
        self.window_seconds = max(window_seconds, 1)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window = int(now // self.window_seconds)
        with _lock:
            bucket_key = (key, window)
            count = _counters.get(bucket_key, 0) + 1
            _counters[bucket_key] = count
            if len(_counters) > _MAX_KEYS:
                for stale in [k for k in _counters if k[1] < window]:
                    _counters.pop(stale, None)
            return count <= self.limit

    def retry_after(self) -> int:
        now = time.monotonic()
        return max(int(self.window_seconds - (now % self.window_seconds)), 1)

    def reset(self) -> None:
        with _lock:
            _counters.clear()
