"""Save where each dining location is (M3), so the assistant can rank by distance.

    python -m db.seed_location_points

Matches by exact location name against the `locations` table and saves or updates
one row per match. Safe to run again. To add or fix a location, edit POINTS and
run it again. Names with no match in the database are listed and skipped (the
ingestion job may not have loaded that location yet).

Nobody has to run it for a new setup: the assistant calls ensure() the first time
it needs positions, which fills in any that are missing and never changes one that
exists. Run this script when you have corrected a coordinate in POINTS.

Coordinates came from Google Maps (Case, Clark, One Earth, On the Oval, Atrium)
and OpenStreetMap (the rest); check any of them on a map before relying on it.
"""

import os

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.assistant_models import LocationPoint
from db.models import Location
from db.session import make_engine, make_session_factory

# name -> (latitude, longitude)
POINTS: dict[str, tuple[float, float]] = {
    "Fountain Dining Hall": (35.78547, -78.67764),
    "Case Dining Hall": (35.782872, -78.669417),
    "Clark Dining Hall": (35.782159, -78.667066),
    "One Earth Dining Hall": (35.784381, -78.670271),
    "On the Oval": (35.770076, -78.674568),
    "Atrium – Brickyard Pizza": (35.787951, -78.670646),
    "Atrium – Smoothie U": (35.787862, -78.670737),
    "University Towers Dining Hall": (35.78835, -78.67522),
    "Talley – Tuffy’s Diner": (35.78397, -78.67092),
    "Talley – Los Lobos Global Kitchen": (35.78397, -78.67092),
    "Talley – Jason’s Deli": (35.78397, -78.67092),
    "Talley – 1887 Bistro": (35.78397, -78.67092),
    "Starbucks – Talley Student Union": (35.78397, -78.67092),
    "Port City Java – Talley Student Union": (35.78397, -78.67092),
    "Common Grounds Café – Hunt Library": (35.76935, -78.67638),
    "Hill of Beans Café – D.H. Hill Jr. Library": (35.78753, -78.66971),
}


def seed(db: Session, points: dict[str, tuple[float, float]] = POINTS) -> list[str]:
    """Save the positions of the locations that exist; return the names that don't."""
    ids = {name: id_ for id_, name in db.execute(select(Location.id, Location.name))}
    missing = []
    for name, (lat, lng) in points.items():
        if name not in ids:
            missing.append(name)
            continue
        row = insert(LocationPoint).values(
            location_id=ids[name], latitude=lat, longitude=lng
        )
        db.execute(
            row.on_conflict_do_update(
                index_elements=[LocationPoint.location_id],
                set_={"latitude": lat, "longitude": lng},
            )
        )
    db.commit()
    return missing


def ensure(db: Session, points: dict[str, tuple[float, float]] = POINTS) -> None:
    """Fill in positions that are missing, leaving any saved one as it is.

    Cheap when nothing is missing (one query). Does not commit: the caller's
    transaction does, so a request that seeds saves them with its own work.
    """
    have = set(db.scalars(select(LocationPoint.location_id)))
    for id_, name in db.execute(select(Location.id, Location.name)):
        if id_ in have or name not in points:
            continue
        lat, lng = points[name]
        db.execute(
            insert(LocationPoint)
            .values(location_id=id_, latitude=lat, longitude=lng)
            .on_conflict_do_nothing(index_elements=[LocationPoint.location_id])
        )
    db.flush()


if __name__ == "__main__":
    session = make_session_factory(make_engine(os.environ["DATABASE_URL"]))()
    skipped = seed(session)
    print(f"saved {len(POINTS) - len(skipped)} positions")
    for name in skipped:
        print(f"  no such location in the database, skipped: {name}")
