"""Queries for crowd reports: the one table the API writes."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import CrowdReport


def add_report(db: Session, location_id: int, level: str, at: datetime) -> CrowdReport:
    """Store one report, timestamped `at` (the API's clock, so reads agree with it)."""
    report = CrowdReport(location_id=location_id, level=level, created_at=at)
    db.add(report)
    db.commit()
    return report


def reports_between(db: Session, start: datetime, end: datetime,
                    location_id: int | None = None) -> dict[int, list[tuple[str, datetime]]]:
    """(level, created_at) for reports with start < created_at <= end, keyed by location_id."""
    query = select(CrowdReport.location_id, CrowdReport.level, CrowdReport.created_at).where(
        CrowdReport.created_at > start, CrowdReport.created_at <= end
    )
    if location_id is not None:
        query = query.where(CrowdReport.location_id == location_id)
    reports: dict[int, list[tuple[str, datetime]]] = {}
    for loc, level, created in db.execute(query):
        reports.setdefault(loc, []).append((level, created))
    return reports
