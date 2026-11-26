"""Where the dining locations are (M3). Read-only queries; the table is filled by
db/seed_location_points.py, never by the ingestion job."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.assistant_models import LocationPoint


def points(db: Session) -> dict[int, tuple[float, float]]:
    """Every known position, as {location_id: (latitude, longitude)}."""
    rows = db.execute(
        select(
            LocationPoint.location_id, LocationPoint.latitude, LocationPoint.longitude
        )
    )
    return {location_id: (lat, lng) for location_id, lat, lng in rows}
