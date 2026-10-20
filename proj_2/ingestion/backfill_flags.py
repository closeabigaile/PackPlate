"""Recompute nutrition.ingredient_flags from the ingredient text already stored.

Labels are only re-fetched every LABEL_MAX_AGE_DAYS, so labels saved before the
column existed (or before a word-list change) keep old flags until then. This
recomputes them from the stored text. No requests to NC State.

Usage (from proj_2/, with DATABASE_URL set and migrations applied):
    python -m ingestion.backfill_flags           preview: how many labels would change
    python -m ingestion.backfill_flags --write   save the new flags

Takes the ingestion lock, so it never runs during a scrape.
"""

import argparse
import sys

from sqlalchemy import Engine, select, text

from db.migrate import check_current
from db.models import Nutrition
from db.session import make_engine, make_session_factory
from ingestion.ingredients import matched_terms
from ingestion.run import LOCK_KEY, AlreadyRunning


def backfill(engine: Engine, write: bool) -> dict:
    """Returns {"labels": checked, "changed": would change or did change}."""
    check_current(engine)
    with engine.connect() as lock:
        if not lock.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY}):
            raise AlreadyRunning("an ingestion run is in progress")
        lock.commit()
        try:
            db = make_session_factory(engine)()
            labels = db.scalars(select(Nutrition)).all()
            changed = 0
            for label in labels:
                flags = matched_terms(label.ingredients)
                if flags != label.ingredient_flags:
                    changed += 1
                    label.ingredient_flags = flags
            if write:
                db.commit()
            else:
                db.rollback()
            db.close()
            return {"labels": len(labels), "changed": changed}
        finally:
            lock.scalar(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
            lock.commit()


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point: preview or save the flags and print how many changed."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true", help="save (default: preview only)")
    a = p.parse_args(argv)
    try:
        result = backfill(make_engine(), write=a.write)
    except (AlreadyRunning, RuntimeError) as e:
        print(f"not started: {e}", file=sys.stderr)
        return 2
    verb = "updated" if a.write else "would update"
    print(f"{result['labels']} labels checked; {verb} {result['changed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
