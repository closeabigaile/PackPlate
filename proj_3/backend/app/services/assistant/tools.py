"""Tools for the dining assistant (M3).

Each tool is a plain function over an existing service or repository. It takes
the database session and plain values and returns plain dicts, so the assistant
can only state what a tool returned. Tools only read.

Unknown stays unknown: a missing menu, label, hours row, or report comes back as
None or an empty list, never as zero, closed, or safe. Dietary verdicts come
from services.filter_engine and are never decided here.
"""

from datetime import date, datetime, timedelta
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.repositories import crowd_reports as crowd_repo
from app.repositories import label_reviews as reviews_repo
from app.repositories import location_points as points_repo
from app.repositories import locations as locations_repo
from app.repositories import menus as menus_repo
from app.services import filter_engine
from app.services.assistant import places
from app.services.crowd import WINDOW, aggregate
from app.services.hours import campus_time, open_state
from app.services.hours import periods as hours_periods
from app.services.label_reviews import reviewed_items
from app.services.menus import menu_sort_key

FUZZY_CUTOFF = 0.75  # how close a typed name must be to count as a spelling of one
MAX_CANDIDATES = 3


def _iso(moment: datetime | None) -> str | None:
    """A time as text like "2026-10-06T21:00:00-04:00", or None when there is no time."""
    return moment.isoformat() if moment is not None else None


def _brief(location) -> dict:
    """The short form of a location the assistant may state: just its id and name."""
    return {"id": location.id, "name": location.name}


def _similarity(query: str, name: str) -> float:
    """How close a typed name is to a location name: its best match against the
    whole name or any one word of it ("fountian" vs "fountain dining hall")."""
    return max(
        SequenceMatcher(None, query, part).ratio() for part in [name, *name.split()]
    )


def find_location(db: Session, name: str) -> dict:
    """Which location a typed name means.

    Returns {"match": {"id", "name"} or None, "candidates": [...]}. One clear
    match fills `match`. Several possible ones fill `candidates` (the assistant
    should ask which). Nothing close leaves both empty. Tries the exact name,
    then a part of the name ("fountain"), then a close spelling ("fountian").
    """
    query = " ".join(name.casefold().split())
    if not query:
        return {"match": None, "candidates": []}
    locations = locations_repo.list_locations(db)

    # First the exact name, then any name that contains what was typed. The first
    # group with a hit decides: one hit is the match, several are candidates.
    for found in (
        [loc for loc in locations if loc.name.casefold() == query],
        [loc for loc in locations if query in loc.name.casefold()],
    ):
        if len(found) == 1:
            return {"match": _brief(found[0]), "candidates": []}
        if found:
            return {
                "match": None,
                "candidates": [_brief(loc) for loc in found[:MAX_CANDIDATES]],
            }

    # Last resort, for typos: rank every location by spelling similarity and keep
    # only the ones above the cutoff.
    scored = sorted(
        ((_similarity(query, loc.name.casefold()), loc) for loc in locations),
        key=lambda pair: -pair[0],
    )
    close = [loc for score, loc in scored if score >= FUZZY_CUTOFF]
    if len(close) == 1:
        return {"match": _brief(close[0]), "candidates": []}
    return {
        "match": None,
        "candidates": [_brief(loc) for loc in close[:MAX_CANDIDATES]],
    }


def _item(item) -> dict:
    """An item as the assistant may state it. Numbers appear only when the label is usable."""
    label = item.nutrition
    # No label, or a placeholder one, means no numbers: they come back as None.
    usable = label is not None and not item.nutrition_unavailable
    return {
        "id": item.id,
        "name": item.name,
        "station": item.course,
        "serving_size": item.serving_size,
        "calories": label.calories if usable else None,
        "protein_g": label.protein_g if usable else None,
        "sodium_mg": label.sodium_mg if usable else None,
        "nutrition_available": usable,
    }


def _menus(db: Session, location_id: int, day: date, meal: str | None) -> list:
    """(menu, reviewed items) for a location on `day`, optionally one meal, in day order."""
    menus = sorted(menus_repo.menus_on(db, location_id, day), key=menu_sort_key)
    if meal:
        menus = [m for m in menus if m.meal.casefold() == meal.casefold()]
    approved = reviews_repo.approved(db)
    return [(menu, reviewed_items(menu, approved)) for menu in menus]


def get_menu(db: Session, location_id: int, day: date, meal: str | None = None) -> dict:
    """Every menu at a location on `day` (or just `meal`), with each item's numbers.

    `scraped` False means NetNutrition lists the menu but its items were never
    fetched. An empty `menus` list means there is no menu for that day.
    """
    return {
        "location_id": location_id,
        "date": day.isoformat(),
        "menus": [
            {
                "meal": menu.meal,
                "scraped": menu.fetched_at is not None,
                "items": [_item(item) for item in items],
            }
            for menu, items in _menus(db, location_id, day, meal)
        ],
    }


def filter_items(
    db: Session,
    location_id: int,
    day: date,
    profile: filter_engine.Profile,
    meal: str | None = None,
) -> dict:
    """A location's items on `day` checked against one profile by the filter engine.

    `fits` holds only items the engine says fit. `incomplete` holds items it
    can't confirm (with the reasons). Conflicts are only counted. Nothing is
    ever moved into `fits` because data is missing.
    """
    fits, incomplete, conflicts, checked = [], [], 0, 0
    for menu, items in _menus(db, location_id, day, meal):
        for item in items:
            checked += 1
            # The filter engine alone decides the verdict; this function only sorts.
            result = filter_engine.check(item, profile)
            entry = {
                **_item(item),
                "meal": menu.meal,
                "verdict": result.verdict,
                "reasons": result.reasons,
            }
            if result.verdict == filter_engine.FITS:
                fits.append(entry)
            elif result.verdict == filter_engine.INCOMPLETE:
                incomplete.append(entry)
            else:
                conflicts += 1
    return {
        "location_id": location_id,
        "date": day.isoformat(),
        "items_checked": checked,
        "fits": fits,
        "incomplete": incomplete,
        "conflicts": conflicts,
    }


def get_status(db: Session, location_id: int, at: datetime | None = None) -> dict:
    """Whether a location is open at `at` (default now), and when it closes or next opens.

    `is_open` None means the hours are unknown, not closed.
    """
    at = campus_time(at)
    # Today's and yesterday's hours: a late closing yesterday can still be open now.
    hours = locations_repo.hours_between(
        db, at.date() - timedelta(days=1), at.date(), location_id
    )
    state = open_state(
        at,
        hours.get((location_id, at.date())),
        hours.get((location_id, at.date() - timedelta(days=1))),
    )
    return {
        "location_id": location_id,
        "at": at.isoformat(),
        "is_open": state.is_open,
        "closes_at": _iso(state.closes_at),
        "opens_next_at": _iso(state.opens_next_at),
    }


def get_hours(db: Session, location_id: int, day: date) -> dict:
    """When a location is open on `day`: its opening periods, as times.

    `status` is "open", "closed" (all day), or "unknown" (no hours stored for that
    day). `periods` is empty unless it is open.
    """
    row = locations_repo.hours_between(db, day, day, location_id).get(
        (location_id, day)
    )
    if row is None or row.status not in ("open", "closed"):
        return {
            "location_id": location_id,
            "date": day.isoformat(),
            "status": "unknown",
            "periods": [],
        }
    periods = hours_periods(day, row.windows) if row.status == "open" else []
    return {
        "location_id": location_id,
        "date": day.isoformat(),
        "status": row.status,
        "periods": [
            {"opens_at": _iso(opens), "closes_at": _iso(closes)}
            for opens, closes in periods
        ],
    }


def get_crowd(db: Session, location_id: int, at: datetime | None = None) -> dict:
    """The crowd level from recent student reports. `level` None means no recent
    reports: unknown, not "not busy"."""
    at = campus_time(at)
    # Only reports inside the recent window count; newer ones count more.
    reports = crowd_repo.reports_between(db, at - WINDOW, at, location_id)
    crowd = aggregate(reports.get(location_id, []), at)
    return {
        "location_id": location_id,
        "level": crowd.level,
        "report_count": crowd.report_count,
        "last_reported_at": _iso(crowd.last_reported_at),
    }


def list_locations(db: Session) -> dict:
    """Every dining location that has a menu, by name.

    Locations without any menu items are left out, as everywhere else in the app.
    An empty list means no menus have been loaded yet.
    """
    return {
        "locations": [_brief(loc) for loc in locations_repo.list_locations(db)],
    }


CROWD_RANK = {"not_busy": 0, "moderate": 1, "crowded": 2}
MAX_PICKS = 3
SAME_BUILDING_M = 75  # outlets closer together than this are listed once


def _has_filters(profile: filter_engine.Profile) -> bool:
    return bool(
        profile.avoid
        or profile.diets
        or profile.min_protein_g is not None
        or profile.max_calories is not None
        or profile.max_sodium_mg is not None
    )


def recommend(
    db: Session,
    profile: filter_engine.Profile,
    at: datetime | None = None,
    meal: str | None = None,
) -> dict:
    """The best open locations right now, as plain facts to rank by.

    Only locations known to be open at `at` are considered. With a profile, those
    with nothing confirmed to fit it come last. After that the quietest comes
    first (no recent reports counts as in between, not as quiet), then the one
    with more items that fit. The ranking uses only the same tools as the
    answers above: hours, crowd reports, and the filter engine.
    """
    at = campus_time(at)
    filtered = _has_filters(profile)
    picks = []
    for location in locations_repo.list_locations(db):
        status = get_status(db, location.id, at)
        if status["is_open"] is not True:
            continue
        crowd = get_crowd(db, location.id, at)
        found = filter_items(db, location.id, at.date(), profile, meal)
        picks.append(
            {
                "name": location.name,
                "closes_at": status["closes_at"],
                "items_checked": found["items_checked"],
                "fits": len(found["fits"]),
                "crowd": crowd["level"],
                "reports": crowd["report_count"],
            }
        )
    picks.sort(
        key=lambda pick: (
            filtered and pick["fits"] == 0,
            CROWD_RANK.get(pick["crowd"], 1),
            -pick["fits"],
            pick["name"],
        )
    )
    return {"filtered": filtered, "open_count": len(picks), "picks": picks[:MAX_PICKS]}


def nearest(
    db: Session,
    origin_name: str,
    origin: tuple[float, float],
    profile: filter_engine.Profile,
    at: datetime | None = None,
    meal: str | None = None,
    router=None,
) -> dict:
    """The dining locations closest to a place the student named, with rough walking times.

    From too far to walk, `router` (if any) gives the driving distance and time, and
    the ranking uses the driving time; without it, straight-line miles are shown.

    Only locations with a saved position (the location_points table) are ranked; `unplaced`
    counts the ones left out. Locations in the same building count once, keeping
    the better of them. Open places come first, then (with a profile) those with
    something that fits, then the shorter walk. Walking times come from the
    straight-line distance and are estimates.
    """
    at = campus_time(at)
    filtered = _has_filters(profile)
    ranked, unplaced = [], 0
    known = points_repo.points(db)
    for location in locations_repo.list_locations(db):
        point = known.get(location.id)
        if point is None:
            unplaced += 1
            continue
        metres = places.distance_m(origin, point)
        status = get_status(db, location.id, at)
        found = filter_items(db, location.id, at.date(), profile, meal)
        ranked.append(
            {
                "name": location.name,
                "walk_minutes": places.walk_minutes(metres),
                "miles": places.miles(metres),
                "is_open": status["is_open"],
                "closes_at": status["closes_at"],
                "items_checked": found["items_checked"],
                "fits": len(found["fits"]),
                "_point": point,
                "_metres": metres,
                "_cost": metres,  # what the ranking compares: metres, or drive seconds
            }
        )
    # Too far to walk from every hall: the reply gives miles, not a walking time.
    far = min((pick["_metres"] for pick in ranked), default=0) > places.WALKABLE_M
    driving = False
    if far and router is not None and ranked:
        routes = router.driving(origin, [pick["_point"] for pick in ranked])
        if routes is not None:
            driving = True
            kept = []
            for pick, route in zip(ranked, routes, strict=True):
                if route is None:
                    continue  # no road to it
                metres_by_road, seconds = route
                pick["drive_miles"] = places.miles(metres_by_road)
                pick["drive_minutes"] = max(1, round(seconds / 60))
                pick["_cost"] = seconds
                kept.append(pick)
            ranked = kept
    ranked.sort(
        key=lambda pick: (
            pick["is_open"] is not True,
            filtered and pick["fits"] == 0,
            pick["_cost"],
            -pick["fits"],
            pick["name"],
        )
    )
    # Outlets in the same building (within SAME_BUILDING_M) count once: keep the best.
    picks, seen = [], []
    for pick in ranked:
        if any(places.distance_m(pick["_point"], p) < SAME_BUILDING_M for p in seen):
            continue
        seen.append(pick["_point"])
        picks.append({k: v for k, v in pick.items() if not k.startswith("_")})
    return {
        "origin": origin_name,
        "filtered": filtered,
        "unplaced": unplaced,
        "far": far,
        "driving": driving,
        "picks": picks[:MAX_PICKS],
    }
