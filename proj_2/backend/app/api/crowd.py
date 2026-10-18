"""Routes for student crowd reports (not busy / moderate / crowded).

Calls services.crowd; no aggregation logic lives here. The current level for
every location is also in GET /locations and /locations/{id} (`crowd`).
"""

import math
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.deps import get_db
from app.repositories import crowd_reports as crowd_repo
from app.repositories import locations as locations_repo
from app.schemas.crowd import Crowd, CrowdReportIn
from app.services.crowd import WINDOW, Throttle, aggregate
from app.services.hours import campus_time

REPORT_COOLDOWN_SECONDS = int(os.getenv("CROWD_REPORT_COOLDOWN_SECONDS", "60"))

router = APIRouter(prefix="/crowd", tags=["crowd"])

_throttle = Throttle(REPORT_COOLDOWN_SECONDS)


def get_throttle() -> Throttle:
    return _throttle


@router.post("/{location_id}", response_model=Crowd, status_code=201)
def report_crowd(
    location_id: int,
    report: CrowdReportIn,
    request: Request,
    db: Session = Depends(get_db),
    throttle: Throttle = Depends(get_throttle),
):
    """Report how busy a location is right now. Returns the location's crowd level after it.

    One report per location per client every CROWD_REPORT_COOLDOWN_SECONDS (429 otherwise).
    """
    if locations_repo.get_location(db, location_id) is None:
        raise HTTPException(status_code=404, detail=f"location {location_id} not found")
    client = request.client.host if request.client else None
    retry_after = throttle.hit((client, location_id))
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="you reported this location recently",
            headers={"Retry-After": str(math.ceil(retry_after))},
        )
    now = campus_time()
    crowd_repo.add_report(db, location_id, report.level, now)
    reports = crowd_repo.reports_between(db, now - WINDOW, now, location_id)
    return vars(aggregate(reports.get(location_id, []), now))
