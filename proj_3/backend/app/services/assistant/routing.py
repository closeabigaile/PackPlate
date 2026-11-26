"""Driving distance and time from a faraway place to the dining locations (M3).

Used only when the student is too far from campus to walk. One request to the free
public OSRM server returns the road distance and time from the student's place to
every dining location at once. Only coordinates are sent: the student's place
(found from what they typed) and the dining locations' positions, nothing about the
account. Times are for light traffic; real trips can take longer.

Anything that goes wrong (switched off, slow, down, no route) returns None and the
reply shows straight-line distances instead. Answers are cached by place.
"""

import json
import threading
import time
import urllib.parse
import urllib.request

from app.services.assistant import settings

USER_AGENT = "PackPlate/0.1 (NC State CSC 510 student project)"
MIN_SECONDS_BETWEEN_CALLS = 1.1
MAX_CACHED = 200
MAX_DESTINATIONS = 25
METRES_PER_MILE = 1609.344


class Router:
    """Looks up driving distances. `driving` never raises."""

    def __init__(
        self, url: str, timeout: float, clock=time.monotonic, sleep=time.sleep
    ):
        if not url.startswith(("http://", "https://")):
            raise ValueError("the routing URL must start with http:// or https://")
        self.url = url.rstrip("/")
        self.timeout = timeout
        self._clock = clock
        self._sleep = sleep
        self._last_call = float("-inf")
        self._cache: dict[tuple, list[tuple[float, float] | None]] = {}
        self._lock = threading.Lock()

    def _fetch(self, origin, destinations) -> dict:
        """Ask for the road distances and times; raises OSError or ValueError on trouble."""
        points = ";".join(f"{lng},{lat}" for lat, lng in [origin, *destinations])
        query = urllib.parse.urlencode(
            {"sources": 0, "annotations": "distance,duration"}
        )
        request = urllib.request.Request(
            f"{self.url}/table/v1/driving/{points}?{query}",
            headers={"User-Agent": USER_AGENT},
        )
        # Straight to the service, never through a system proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=self.timeout) as response:
            return json.load(response)

    def driving(
        self, origin: tuple[float, float], destinations: list[tuple[float, float]]
    ) -> list[tuple[float, float] | None] | None:
        """For each destination, (metres, seconds) by road, or None if no route to it.

        Returns None for the whole list if the lookup failed.
        """
        if not destinations or len(destinations) > MAX_DESTINATIONS:
            return None
        key = (
            tuple(round(c, 4) for c in origin),
            tuple((round(a, 4), round(b, 4)) for a, b in destinations),
        )
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            wait = MIN_SECONDS_BETWEEN_CALLS - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
            self._last_call = self._clock()
            try:
                found = self._parse(
                    self._fetch(origin, destinations), len(destinations)
                )
            except (OSError, ValueError, KeyError, TypeError, IndexError):
                return None  # not cached: the service may be back next time
            if len(self._cache) >= MAX_CACHED:
                self._cache.clear()
            self._cache[key] = found
            return found

    @staticmethod
    def _parse(data: dict, count: int) -> list[tuple[float, float] | None]:
        """The table response as one (metres, seconds) per destination."""
        if data.get("code") != "Ok":
            raise ValueError("no route table")
        metres, seconds = data["distances"][0][1:], data["durations"][0][1:]
        if len(metres) != count or len(seconds) != count:
            raise ValueError("unexpected table size")
        return [
            (float(m), float(s)) if m is not None and s is not None and m >= 0 else None
            for m, s in zip(metres, seconds, strict=True)
        ]


_shared: Router | None = None


def default() -> Router | None:
    """The router from the settings, or None while the lookup is switched off.

    One shared object, so its cache and its spacing between calls last across requests.
    """
    global _shared
    if not settings.routing_enabled():
        return None
    url, timeout = settings.routing_url(), settings.routing_timeout()
    if _shared is None or (_shared.url, _shared.timeout) != (url, timeout):
        _shared = Router(url, timeout)
    return _shared
