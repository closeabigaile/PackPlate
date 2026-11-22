"""Find where a typed place is (M3), for places campus_places.json doesn't list.

Only the typed place (a few words such as "Cox Hall") is sent to OpenStreetMap's
free search, never an account, a profile, or the rest of the message. The NC State
campus is searched first, so "Cox Hall" can't turn into another city's Cox Hall;
if nothing is found there, the Raleigh-Durham-Cary area is searched, which finds
an apartment or street off campus. Results (and misses) are cached, and calls are
spaced at least a second apart, as OpenStreetMap's usage policy asks.

Anything that goes wrong (switched off, slow, down, nothing found) returns None
and the assistant asks the student where they are instead.
"""

import json
import threading
import time
import urllib.parse
import urllib.request

from app.services.assistant import settings

USER_AGENT = "PackPlate/0.1 (NC State CSC 510 student project)"
# West, north, east, south edges of the areas searched. Campus first (main campus
# and Centennial), then the wider area (Raleigh, Durham, Cary, Chapel Hill).
CAMPUS_BOX = ("-78.71,35.80,-78.64,35.75", "Raleigh, NC")
REGION_BOX = ("-79.3,36.2,-78.2,35.5", "North Carolina")
MIN_SECONDS_BETWEEN_CALLS = 1.1
MAX_CACHED = 500
MAX_PHRASE_CHARS = 80
NAME_CHARS = 60  # how much of the found name is shown back to the student


class Geocoder:
    """Looks places up in the NC State area. `lookup` never raises."""

    def __init__(
        self, url: str, timeout: float, clock=time.monotonic, sleep=time.sleep
    ):
        if not url.startswith(("http://", "https://")):
            raise ValueError("the geocoder URL must start with http:// or https://")
        self.url = url.rstrip("/")
        self.timeout = timeout
        self._clock = clock
        self._sleep = sleep
        self._last_call = float("-inf")
        self._cache: dict[str, tuple[str, tuple[float, float]] | None] = {}
        self._lock = threading.Lock()

    def _fetch(self, phrase: str, area: tuple[str, str]) -> list:
        """Ask the search service for matches in one area; raises OSError or ValueError on trouble."""
        box, place = area
        query = urllib.parse.urlencode(
            {
                "q": f"{phrase}, {place}",
                "format": "json",
                "limit": 1,
                "viewbox": box,
                "bounded": 1,
            }
        )
        request = urllib.request.Request(
            f"{self.url}/search?{query}", headers={"User-Agent": USER_AGENT}
        )
        # Straight to the service, never through a system proxy (slow to look up on macOS).
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=self.timeout) as response:
            return json.load(response)

    def lookup(self, phrase: str) -> tuple[str, tuple[float, float]] | None:
        """(name, (latitude, longitude)) for a typed place, or None."""
        phrase = " ".join(phrase.split())
        if not phrase or len(phrase) > MAX_PHRASE_CHARS:
            return None
        key = phrase.casefold()
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            try:
                found = None
                for area in (CAMPUS_BOX, REGION_BOX):
                    # One call at a time, spaced out. Holding the lock spaces them.
                    wait = MIN_SECONDS_BETWEEN_CALLS - (self._clock() - self._last_call)
                    if wait > 0:
                        self._sleep(wait)
                    self._last_call = self._clock()
                    found = self._parse(self._fetch(phrase, area))
                    if found:
                        break
            except (OSError, ValueError, KeyError, TypeError):
                return None  # not cached: the service may be back next time
            if len(self._cache) >= MAX_CACHED:
                self._cache.clear()
            self._cache[key] = found
            return found

    @staticmethod
    def _parse(results) -> tuple[str, tuple[float, float]] | None:
        """The first result as (short name, point), or None if there is none."""
        if not isinstance(results, list) or not results:
            return None
        top = results[0]
        lat, lng = float(top["lat"]), float(top["lon"])
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return None
        name = top.get("name")
        if not name:
            # An address has no name: "3843, Cary Glen Boulevard, ..." becomes "3843 Cary Glen Boulevard".
            parts = [p.strip() for p in str(top["display_name"]).split(",")]
            name = (
                f"{parts[0]} {parts[1]}"
                if parts[0].isdigit() and len(parts) > 1
                else parts[0]
            )
        return (str(name).strip()[:NAME_CHARS] or "that place"), (lat, lng)


_shared: Geocoder | None = None


def default() -> Geocoder | None:
    """The geocoder from the settings, or None while the lookup is switched off.

    One shared object, so its cache and its spacing between calls last across requests.
    """
    global _shared
    if not settings.geocode_enabled():
        return None
    url, timeout = settings.geocode_url(), settings.geocode_timeout()
    if _shared is None or (_shared.url, _shared.timeout) != (url, timeout):
        _shared = Geocoder(url, timeout)
    return _shared
