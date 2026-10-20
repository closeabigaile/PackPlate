"""Scrape alerts: what the team should hear about after a scheduled run (#3).

Reads the latest ingest_runs rows and returns alerts as {"title", "body"}.
Titles are fixed, so the workflow can update one open issue per kind of alert:
- the latest run failed, or finished with errors (body: the run's errors);
- no run has completed in STALE_AFTER_HOURS, so menus are going stale;
- diet tags are waiting for review (body: a count only, never dish names, since
  alerts become public GitHub issues; details stay in `ingestion.review_labels`).

Usage (from proj_2/, with DATABASE_URL set):
    python -m ingestion.scrape_alerts     prints the alerts as JSON
"""

import json
import sys
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import IngestRun
from db.session import make_engine, make_session_factory
from ingestion.write import now

# Same rule as backend/app/services/freshness.py: a day plus slack for a late run.
STALE_AFTER_HOURS = 36
MAX_ERRORS_SHOWN = 20


def alerts(db: Session, at: datetime) -> list[dict]:
    """Alerts for the team, most important first. [] when all is well."""
    latest = db.scalars(
        select(IngestRun).order_by(IngestRun.id.desc()).limit(1)
    ).first()
    if latest is None:
        return [{"title": "Scraper has never run", "body": "No ingest_runs rows yet."}]

    out = []
    if latest.status in ("failed", "partial"):
        errors = latest.errors or []
        shown = "\n".join(f"- {e}" for e in errors[:MAX_ERRORS_SHOWN])
        more = len(errors) - MAX_ERRORS_SHOWN
        out.append(
            {
                "title": (
                    "Daily scrape failed"
                    if latest.status == "failed"
                    else "Daily scrape finished with errors"
                ),
                "body": f"Run {latest.id} ({latest.started_at:%Y-%m-%d %H:%M} UTC): "
                f"{latest.status}.\n\n{shown}"
                + (f"\n- ... and {more} more" if more > 0 else ""),
            }
        )

    last_done = db.scalar(
        select(IngestRun.finished_at)
        .where(IngestRun.status.in_(("ok", "partial")))
        .order_by(IngestRun.finished_at.desc())
        .limit(1)
    )
    if last_done is None or at - last_done > timedelta(hours=STALE_AFTER_HOURS):
        when = f"{last_done:%Y-%m-%d %H:%M} UTC" if last_done else "never"
        out.append(
            {
                "title": "Menu data is stale",
                "body": f"Last completed scrape: {when} "
                f"(stale after {STALE_AFTER_HOURS} hours).",
            }
        )

    pending = (latest.stats or {}).get("label_reviews_pending", 0)
    if pending:
        out.append(
            {
                "title": "Diet tags waiting for review",
                "body": f"{pending} diet tag{'s' * (pending != 1)} waiting. Run "
                "`python -m ingestion.review_labels` to see and decide them.",
            }
        )
    return out


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point: print the current alerts as a JSON list."""
    try:
        db = make_session_factory(make_engine())()
    except RuntimeError as e:
        print(f"not started: {e}", file=sys.stderr)
        return 2
    print(json.dumps(alerts(db, now()), indent=2))
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
