"""Review contradicted diet tags: list pending reviews, then approve or reject each (#18).

Approving removes the review's tags from that dish in the API; rejecting keeps
NC State's tags. Every decision records who made it, when, and why.

Usage (from proj_2/, with DATABASE_URL set and migrations applied):
    python -m ingestion.review_labels
    python -m ingestion.review_labels --approve 1 --by "Morgan" --reason "lists chicken"
    python -m ingestion.review_labels --reject 2 --by "Morgan" --reason "plant-based"
"""

import argparse
import sys
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import LabelReview, Location, Nutrition
from db.session import make_engine, make_session_factory
from ingestion.config import CAMPUS_TZ
from ingestion.label_reviews import ingredients_hash
from ingestion.write import now


def pending(db: Session) -> list[dict]:
    """Pending reviews, oldest first, with the ingredient text each one is about."""
    out = []
    reviews = db.scalars(
        select(LabelReview)
        .where(LabelReview.status == "pending")
        .order_by(LabelReview.first_seen_at, LabelReview.id)
    )
    for r in reviews:
        labels = db.scalars(
            select(Nutrition.ingredients).where(
                Nutrition.location_id == r.location_id,
                Nutrition.key.startswith(f"{r.location_id}|{r.dish}|"),
            )
        )
        text = next(
            (t for t in labels if ingredients_hash(t) == r.ingredients_hash), None
        )
        out.append(
            {
                "id": r.id,
                "location": db.get(Location, r.location_id).name,
                "item": r.item_name,
                "tags": r.tags,
                "words": r.words,
                "first_seen": r.first_seen_at,
                "ingredients": text,
            }
        )
    return out


def decide(
    db: Session, review_id: int, status: str, by: str, reason: str, at: datetime
) -> LabelReview:
    """Approve or reject one pending review. The caller commits."""
    if status not in ("approved", "rejected"):
        raise ValueError(f"status must be approved or rejected, not {status!r}")
    if not by.strip() or not reason.strip():
        raise ValueError("a decision needs --by and --reason")
    review = db.get(LabelReview, review_id)
    if review is None:
        raise ValueError(f"no review #{review_id}")
    if review.status != "pending":
        raise ValueError(f"review #{review_id} is already {review.status}")
    review.status, review.decided_by, review.reason, review.decided_at = (
        status,
        by.strip(),
        reason.strip(),
        at,
    )
    return review


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point: list pending reviews, or record one decision."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = p.add_mutually_exclusive_group()
    action.add_argument("--approve", type=int, metavar="ID", help="remove the tags")
    action.add_argument("--reject", type=int, metavar="ID", help="keep the tags")
    p.add_argument("--by", default="", help="who decided")
    p.add_argument("--reason", default="", help="why")
    a = p.parse_args(argv)
    try:
        db = make_session_factory(make_engine())()
    except RuntimeError as e:
        print(f"not started: {e}", file=sys.stderr)
        return 2

    if a.approve is None and a.reject is None:
        rows = pending(db)
        print(f"{len(rows)} pending review{'s' * (len(rows) != 1)}")
        for r in rows:
            print(f"\n#{r['id']}  {r['location']} · {r['item']}")
            print(f"    NC State tags:       {', '.join(r['tags'])}")
            print(f"    Ingredients mention: {', '.join(r['words'])}")
            print(
                f"    First seen:          {r['first_seen'].astimezone(CAMPUS_TZ):%Y-%m-%d}"
            )
            if r["ingredients"]:
                print(f"    Ingredients:         {r['ingredients'][:100]}...")
        db.close()
        return 0

    review_id = a.approve if a.approve is not None else a.reject
    status = "approved" if a.approve is not None else "rejected"
    try:
        review = decide(db, review_id, status, a.by, a.reason, now())
        db.commit()
    except ValueError as e:
        print(f"not recorded: {e}", file=sys.stderr)
        db.close()
        return 2
    effect = (
        "will be removed" if status == "approved" else "stay as NC State lists them"
    )
    print(
        f"#{review.id} {status}: {', '.join(review.tags)} {effect} for {review.item_name}"
    )
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
