from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from db.models import Location, Nutrition
from ingestion.backfill_flags import backfill
from ingestion.run import LOCK_KEY, AlreadyRunning

SAVED = datetime(2026, 10, 1, tzinfo=UTC)


def add_label(db, key, ingredients, flags):
    if db.get(Location, 1) is None:
        db.add(Location(id=1, name="Fountain", updated_at=SAVED))
    db.add(
        Nutrition(
            key=key,
            location_id=1,
            source_detail_oid=1,
            ingredients=ingredients,
            nutrients_raw={},
            contains=[],
            missing_fields=[],
            ingredient_flags=flags,
            fetched_at=SAVED,
        )
    )
    db.commit()


def test_preview_changes_nothing(db, pg_engine):
    add_label(db, "1|pancake|1 each", "Flour, Whey", {})
    assert backfill(pg_engine, write=False) == {"labels": 1, "changed": 1}
    db.expire_all()
    assert db.get(Nutrition, "1|pancake|1 each").ingredient_flags == {}


def test_write_fills_flags_from_stored_ingredients(db, pg_engine):
    add_label(db, "1|pancake|1 each", "Flour, Whey", {})
    add_label(db, "1|apple|1 each", "Apple", {})
    assert backfill(pg_engine, write=True) == {"labels": 2, "changed": 1}
    db.expire_all()
    assert db.get(Nutrition, "1|pancake|1 each").ingredient_flags == {
        "dairy": ["whey"],
        "gluten": ["flour"],
    }
    assert db.get(Nutrition, "1|apple|1 each").ingredient_flags == {}


def test_refuses_to_run_during_a_scrape(db, pg_engine):
    with pg_engine.connect() as other:
        other.scalar(text("SELECT pg_advisory_lock(:k)"), {"k": LOCK_KEY})
        other.commit()
        with pytest.raises(AlreadyRunning):
            backfill(pg_engine, write=True)
        other.scalar(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})
        other.commit()
