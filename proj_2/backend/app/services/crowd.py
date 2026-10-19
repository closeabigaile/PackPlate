"""Crowd aggregation.

Combines recent student reports into a crowd level per location.
Kept separate from filter_engine so the two features don't share a file.

Reports are only stored, never updated; the level is worked out here on
every read, so two students reporting at once can't corrupt it. Only reports
from the last CROWD_WINDOW_MINUTES count, and newer ones count more: a report
weighs 1 when new and falls linearly to 0 at the end of the window. No
reports in the window means the level is unknown (None), not "not busy".
"""

import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

LEVELS = ("not_busy", "moderate", "crowded")
WINDOW = timedelta(minutes=int(os.getenv("CROWD_WINDOW_MINUTES", "30")))


@dataclass
class Crowd:
    """A location's crowd level from the reports in the window."""

    level: str | None  # None = no reports in the window
    report_count: int  # reports in the window
    last_reported_at: datetime | None


def aggregate(reports, at: datetime) -> Crowd:
    """reports: (level, created_at) pairs for one location. Only those in (at - WINDOW, at] count."""
    recent = [
        (level, created) for level, created in reports if at - WINDOW < created <= at
    ]
    if not recent:
        return Crowd(None, 0, None)
    total = weights = 0.0
    for level, created in recent:
        weight = 1 - (at - created) / WINDOW
        total += weight * LEVELS.index(level)
        weights += weight
    mean = total / weights
    level = LEVELS[0] if mean < 0.5 else LEVELS[1] if mean < 1.5 else LEVELS[2]
    return Crowd(level, len(recent), max(created for _, created in recent))


class Throttle:
    """At most one report per key (client address + location) every `seconds`.

    Kept in memory only, so no reporter data is stored. The API is a single
    process, so one dict is enough; it resets on restart.
    """

    def __init__(self, seconds: float, clock=time.monotonic):
        self.seconds = seconds
        self._clock = clock
        self._last: dict = {}
        self._lock = threading.Lock()

    def hit(self, key) -> float:
        """Record a report for key. Returns 0 if allowed, else seconds until it would be."""
        now = self._clock()
        with self._lock:
            last = self._last.get(key)
            if last is not None and now - last < self.seconds:
                return self.seconds - (now - last)
            self._last[key] = now
            if len(self._last) > 10_000:
                self._last = {
                    k: t for k, t in self._last.items() if now - t < self.seconds
                }
            return 0.0
