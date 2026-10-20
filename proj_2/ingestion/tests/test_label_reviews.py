from datetime import UTC, date, datetime

from sqlalchemy import select

from db.models import LabelReview, Location, Menu, MenuItem, Nutrition
from ingestion.label_reviews import (
    DIET_RULED_OUT_BY,
    contradictions,
    dish_name,
    ingredients_hash,
    record,
)
from ingestion.normalize import DIET_KEYS

DAY = date(2026, 10, 23)
NOW = datetime(2026, 10, 19, tzinfo=UTC)
CHICKEN = "Tempura Chicken Bites (Tempura Chicken, Water, Salt), General Tso Sauce"
TOFU = "Tempura Battered Tofu (Tofu (Water, Soybeans)), General Tso Sauce"


def test_rules_cover_every_restricting_diet():
    assert set(DIET_RULED_OUT_BY) == set(DIET_KEYS) - {"sustainable"}


def test_contradictions_name_the_tags_and_words():
    assert contradictions(["vegan", "vegetarian"], CHICKEN) == {
        "vegan": ["chicken"],
        "vegetarian": ["chicken"],
    }
    assert contradictions(["vegan", "vegetarian"], TOFU) == {}
    # Halal is only contradicted by pork; "sausage" alone counts as meat.
    assert contradictions(["halal"], "Pork Sausage, Salt") == {"halal": ["pork"]}
    assert contradictions([], CHICKEN) == {}  # untagged: nothing to contradict


def test_dish_name_and_hash_are_stable():
    assert (
        dish_name("  General Tso's   Crispy Chicken ") == "general tso's crispy chicken"
    )
    assert ingredients_hash(CHICKEN) == ingredients_hash(CHICKEN)
    assert ingredients_hash(CHICKEN) != ingredients_hash(TOFU)


def add_item(db, menu_id, item_id, name, diets, ingredients):
    key = f"1|{dish_name(name)}|{item_id}"
    db.add(
        Nutrition(
            key=key,
            location_id=1,
            source_detail_oid=item_id,
            ingredients=ingredients,
            nutrients_raw={},
            contains=[],
            missing_fields=[],
            ingredient_flags={},
            fetched_at=NOW,
        )
    )
    db.flush()
    db.add(
        MenuItem(
            menu_id=menu_id,
            detail_oid=item_id,
            name=name,
            allergens=[],
            diets=diets,
            traits_raw=[],
            unrecognized_traits=[],
            nutrition_key=key,
        )
    )


def setup(db):
    db.add(Location(id=1, name="Dining Hall", updated_at=NOW))
    for menu_id, day in ((10, DAY), (11, date(2026, 10, 24))):
        db.add(Menu(id=menu_id, location_id=1, date=day, meal="Lunch", fetched_at=NOW))
    db.flush()


def test_record_queues_one_pending_review_per_dish(db):
    setup(db)
    # The same dish on two menus, plus a correctly tagged one.
    add_item(
        db, 10, 1, "General Tso's Crispy Chicken", ["vegan", "vegetarian"], CHICKEN
    )
    add_item(
        db, 11, 2, "General Tso's Crispy Chicken", ["vegan", "vegetarian"], CHICKEN
    )
    add_item(db, 10, 3, "Crispy General Tso's Tofu", ["vegan", "vegetarian"], TOFU)
    db.commit()

    assert record(db, DAY, date(2026, 10, 24), NOW) == (1, 1)
    db.commit()
    review = db.scalars(select(LabelReview)).one()
    assert (review.item_name, review.dish) == (
        "General Tso's Crispy Chicken",
        "general tso's crispy chicken",
    )
    assert (review.tags, review.words, review.status) == (
        ["vegan", "vegetarian"],
        ["chicken"],
        "pending",
    )

    # The next scrape finds it again but adds nothing.
    assert record(db, DAY, date(2026, 10, 24), NOW) == (0, 1)


def test_decided_reviews_are_not_queued_again(db):
    setup(db)
    add_item(db, 10, 1, "General Tso's Crispy Chicken", ["vegan"], CHICKEN)
    db.commit()
    record(db, DAY, DAY, NOW)
    review = db.scalars(select(LabelReview)).one()
    review.status = "approved"
    db.commit()
    assert record(db, DAY, DAY, NOW) == (0, 0)


def test_changed_ingredients_need_a_new_review(db):
    setup(db)
    add_item(db, 10, 1, "General Tso's Crispy Chicken", ["vegan"], CHICKEN)
    add_item(db, 11, 2, "General Tso's Crispy Chicken", ["vegan"], CHICKEN + ", Pork")
    db.commit()
    assert record(db, DAY, date(2026, 10, 24), NOW) == (2, 2)
