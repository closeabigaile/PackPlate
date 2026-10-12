"""Routes for dietary filtering, single person and group.

Calls services.filter_engine; no filtering logic lives here. Profiles come in
the request body (POST) so dietary information never lands in URLs or logs,
and nothing about them is stored. One profile is the single-person case.
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.repositories import locations as locations_repo
from app.repositories import menus as menus_repo
from app.schemas.filters import FilteredMenu, FilterRequest, GroupLocation
from app.schemas.locations import MenuItem
from app.services import filter_engine
from app.services.hours import campus_time, open_state
from app.services.menus import menu_sort_key

router = APIRouter(prefix="/filters", tags=["filters"])


def _profiles(request: FilterRequest) -> list[filter_engine.Profile]:
    return [
        filter_engine.Profile(
            avoid=frozenset(p.avoid), diets=frozenset(p.diets), min_protein_g=p.min_protein_g,
            max_calories=p.max_calories, max_sodium_mg=p.max_sodium_mg,
        )
        for p in request.profiles
    ]


@router.post("/locations/{location_id}/menus", response_model=list[FilteredMenu])
def filter_menus(location_id: int, request: FilterRequest,
                 on: date | None = Query(None, alias="date"), db: Session = Depends(get_db)):
    """Every menu at a location on `date` (default today), each item checked against every profile."""
    if locations_repo.get_location(db, location_id) is None:
        raise HTTPException(status_code=404, detail=f"location {location_id} not found")
    profiles = _profiles(request)
    day = on or campus_time().date()
    menus = sorted(menus_repo.menus_on(db, location_id, day), key=menu_sort_key)
    return [
        {
            "id": menu.id, "date": menu.date, "meal": menu.meal, "scraped": menu.fetched_at is not None,
            "items": [
                {
                    **MenuItem.model_validate(item, from_attributes=True).model_dump(),
                    "results": [vars(filter_engine.check(item, p)) for p in profiles],
                }
                for item in sorted(menu.items, key=lambda i: i.id)
            ],
        }
        for menu in menus
    ]


@router.post("/group", response_model=list[GroupLocation])
def filter_group(request: FilterRequest, at: datetime | None = None, db: Session = Depends(get_db)):
    """Every location, ranked for a group: where everyone has something that fits on `at`'s day.

    Order: locations where everyone fits first, then those open at `at`, then by name.
    """
    at = campus_time(at)
    profiles = _profiles(request)
    items_by_location: dict[int, list] = {}
    for menu in menus_repo.all_menus_on(db, at.date()):
        items_by_location.setdefault(menu.location_id, []).extend(menu.items)
    hours = locations_repo.hours_between(db, at.date() - timedelta(days=1), at.date())

    results = []
    for location in locations_repo.list_locations(db):
        items = items_by_location.get(location.id, [])
        state = open_state(at, hours.get((location.id, at.date())),
                           hours.get((location.id, at.date() - timedelta(days=1))))
        counts = [filter_engine.count(items, p) for p in profiles]
        results.append({
            "id": location.id,
            "name": location.name,
            "is_open": state.is_open,
            "closes_at": state.closes_at,
            "opens_next_at": state.opens_next_at,
            "items_checked": len(items),
            "everyone_fits": all(c.fits > 0 for c in counts),
            "profiles": [{"name": p.name, **vars(c)} for p, c in zip(request.profiles, counts)],
        })
    results.sort(key=lambda r: (not r["everyone_fits"], r["is_open"] is not True, r["name"]))
    return results
