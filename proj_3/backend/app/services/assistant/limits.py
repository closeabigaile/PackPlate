"""A per-account limit on how often the assistant can be asked.

Kept in memory only, like the crowd-report throttle, so nothing about an account's
activity is stored. The API is a single process, so one dict is enough; it resets
on restart.
"""

import threading
import time
from collections import deque


class RateLimiter:
    """At most `max_calls` per key within any `seconds`-long window."""

    def __init__(self, max_calls: int, seconds: float, clock=time.monotonic):
        self.max_calls = max_calls
        self.seconds = seconds
        self._clock = clock
        self._calls: dict = {}
        self._lock = threading.Lock()

    def hit(self, key) -> float:
        """Record a call for key. Returns 0 if allowed, else seconds until it would be."""
        now = self._clock()
        with self._lock:
            calls = self._calls.setdefault(key, deque())
            while calls and now - calls[0] >= self.seconds:
                calls.popleft()  # forget calls that have left the window
            if len(calls) >= self.max_calls:
                return self.seconds - (now - calls[0])
            calls.append(now)
            return 0.0
