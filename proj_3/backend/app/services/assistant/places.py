"""Where things are on campus (M3), for "which dining hall is near ...?".

The student names a place ("I'm at Talley", "near Hunt Library"). This module
knows a list of campus places and their coordinates, read from
campus_places.json, and turns two points into a rough walking time. The dining
locations' own positions are in the database (location_points); one with no
saved position is simply not ranked: nothing here guesses a position.

Distance is the straight line between two points (haversine). A walk is longer
than that, so the walking time adds a winding factor. It is an estimate and the
replies say so.
"""

import json
import re
from difflib import SequenceMatcher
from functools import cache
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

PLACES_FILE = Path(__file__).with_name("campus_places.json")
EARTH_RADIUS_M = 6_371_000
WALK_M_PER_MIN = 80  # about 3 mph
WINDING = 1.25  # paths are longer than the straight line
WALKABLE_M = 3000  # farther than this from every hall is not a walk
METRES_PER_MILE = 1609.344
SPELLING_CUTOFF = 0.85  # how close a typed word must be to a one-word alias


@cache
def load() -> dict:
    """The campus places file: {"spots": {name: {"at": [lat, lng], "aliases": [...]}}}."""
    return json.loads(PLACES_FILE.read_text(encoding="utf-8"))


def distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Straight-line metres between two (latitude, longitude) points."""
    lat1, lng1, lat2, lng2 = map(radians, (*a, *b))
    h = (
        sin((lat2 - lat1) / 2) ** 2
        + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * asin(sqrt(h))


def walk_minutes(metres: float) -> int:
    """A rough walking time in whole minutes, at least 1."""
    return max(1, round(metres * WINDING / WALK_M_PER_MIN))


def miles(metres: float) -> float:
    """A straight-line distance in miles, to one decimal place (never less than 0.1)."""
    return max(0.1, round(metres / METRES_PER_MILE, 1))


def spot_names(data: dict | None = None) -> list[str]:
    """The campus places a student can say they are at."""
    return list((data or load())["spots"])


def find_spot(
    text: str, data: dict | None = None
) -> tuple[str, tuple[float, float]] | None:
    """The campus place a message names, as (name, point), or None.

    Matches an alias inside the text, or a close spelling of a one-word alias
    ("tally" for "talley"). If several places match, the longest alias wins.
    """
    spots = (data or load())["spots"]
    text = " ".join(text.casefold().split())
    words = re.findall(r"[a-z0-9.']+", text)
    best: tuple[int, str] | None = None
    for name, spot in spots.items():
        for alias in (name.casefold(), *spot["aliases"]):
            found = re.search(rf"\b{re.escape(alias)}\b", text) is not None or (
                " " not in alias
                and len(alias) >= 4
                and any(
                    len(w) >= 4
                    and SequenceMatcher(None, w, alias).ratio() >= SPELLING_CUTOFF
                    for w in words
                )
            )
            if found and (best is None or len(alias) > best[0]):
                best = (len(alias), name)
    if best is None:
        return None
    at = spots[best[1]]["at"]
    return best[1], (at[0], at[1])
