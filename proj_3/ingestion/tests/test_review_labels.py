from datetime import UTC, datetime

import pytest

from db.models import LabelReview, Location, Nutrition
from ingestion.label_reviews import dish_name, ingredients_hash
from ingestion.review_labels import decide, pending

NOW = datetime(2026, 10, 19, tzinfo=UTC)
LATER = datetime(2026, 10, 20, tzinfo=UTC)
CHICKEN = "Tempura Chicken Bites (Tempura Chicken, Water, Salt)"
NAME = "General Tso's Crispy Chicken"


def setup(db):
    db.add(Location(id=1, name="Dining Hall", updated_at=NOW))
    db.flush()
    db.add(
        Nutrition(
            key=f"1|{dish_name(NAME)}|serving",
            location_id=1,
            source_detail_oid=1,
            ingredients=CHICKEN,
            nutrients_raw={},
            contains=[],
            missing_fields=[],
            ingredient_flags={},
            fetched_at=NOW,
        )
    )
    review = LabelReview(
        location_id=1,
        dish=dish_name(NAME),
        item_name=NAME,
        tags=["vegan", "vegetarian"],
        words=["chicken"],
        ingredients_hash=ingredients_hash(CHICKEN),
        status="pending",
        first_seen_at=NOW,
    )
    db.add(review)
    db.commit()
    return review


def test_pending_lists_the_review_with_its_ingredients(db):
    review = setup(db)
    rows = pending(db)
    assert len(rows) == 1
    assert rows[0]["id"] == review.id
    assert (rows[0]["location"], rows[0]["item"]) == ("Dining Hall", NAME)
    assert rows[0]["ingredients"] == CHICKEN


def test_approve_records_who_when_and_why(db):
    review = setup(db)
    decide(db, review.id, "approved", "Morgan", "lists chicken", LATER)
    db.commit()
    db.expire_all()
    saved = db.get(LabelReview, review.id)
    assert (saved.status, saved.decided_by, saved.reason, saved.decided_at) == (
        "approved",
        "Morgan",
        "lists chicken",
        LATER,
    )
    assert pending(db) == []


def test_a_decision_needs_a_name_and_a_reason(db):
    review = setup(db)
    with pytest.raises(ValueError, match="--by and --reason"):
        decide(db, review.id, "approved", "Morgan", " ", LATER)


def test_only_pending_reviews_can_be_decided(db):
    review = setup(db)
    decide(db, review.id, "rejected", "Morgan", "plant-based", LATER)
    db.commit()
    with pytest.raises(ValueError, match="already rejected"):
        decide(db, review.id, "approved", "Morgan", "changed my mind", LATER)
    with pytest.raises(ValueError, match="no review"):
        decide(db, 999, "approved", "Morgan", "x", LATER)
