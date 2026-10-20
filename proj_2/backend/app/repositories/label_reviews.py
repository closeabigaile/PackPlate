"""Queries for approved label reviews (#18). Read-only: ingestion writes them."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import LabelReview


def approved(db: Session) -> dict[tuple[int, str, str], tuple[list[str], str]]:
    """Approved reviews: (location_id, dish, ingredients_hash) -> (tags to remove, reason)."""
    rows = db.scalars(select(LabelReview).where(LabelReview.status == "approved"))
    return {
        (r.location_id, r.dish, r.ingredients_hash): (r.tags, r.reason or "")
        for r in rows
    }
