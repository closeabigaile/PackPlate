"""Approved label reviews remove diet tags from the menu and filter responses (#18)."""

from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from app.services.label_reviews import dish_name, ingredients_hash, reviewed
from db.models import LabelReview

TUE = date(2026, 10, 6)
CHICKEN = "Tempura Chicken Bites (Tempura Chicken, Water, Salt)"
NAME = "General Tso's Crispy Chicken"
VEGETARIAN = {"name": "Lee", "diets": ["vegetarian"]}


def item(ingredients=CHICKEN, diets=("vegan", "vegetarian")):
    return SimpleNamespace(
        id=1,
        name=NAME,
        course=None,
        serving_size=None,
        allergens=[],
        diets=list(diets),
        unrecognized_traits=[],
        nutrition=SimpleNamespace(ingredients=ingredients),
    )


APPROVED = {
    (1, dish_name(NAME), ingredients_hash(CHICKEN)): (
        ["vegan", "vegetarian"],
        "ingredients list chicken",
    )
}


def test_approved_tags_are_removed_with_the_reason():
    view = reviewed(item(), 1, APPROVED)
    assert view.diets == []
    assert view.diets_removed == {
        "vegan": "ingredients list chicken",
        "vegetarian": "ingredients list chicken",
    }


def test_decision_does_not_apply_to_changed_ingredients_or_other_locations():
    assert reviewed(item(ingredients="Tofu, Soy Sauce"), 1, APPROVED).diets == [
        "vegan",
        "vegetarian",
    ]
    assert reviewed(item(), 2, APPROVED).diets == ["vegan", "vegetarian"]


def test_matching_rules_agree_with_ingestion():
    pytest.importorskip("bs4")  # ingestion's own dependency
    from ingestion import label_reviews as ingestion_side

    for name in (NAME, "  Crispy   TOFU "):
        assert dish_name(name) == ingestion_side.dish_name(name)
    assert ingredients_hash(CHICKEN) == ingestion_side.ingredients_hash(CHICKEN)


@pytest.fixture
def one_earth(seed, db):
    seed.location(5, "One Earth Dining Hall", "one-earth")
    seed.menu(21, 5, TUE, "Lunch")
    seed.nutrition("5|general tso's crispy chicken|serving", 5, ingredients=CHICKEN)
    seed.item(
        21,
        NAME,
        nutrition_key="5|general tso's crispy chicken|serving",
        allergens=["gluten", "soy"],
        diets=["vegan", "vegetarian"],
    )

    def review(status):
        db.add(
            LabelReview(
                location_id=5,
                dish=dish_name(NAME),
                item_name=NAME,
                tags=["vegan", "vegetarian"],
                words=["chicken"],
                ingredients_hash=ingredients_hash(CHICKEN),
                status=status,
                first_seen_at=datetime(2026, 10, 5, tzinfo=UTC),
                reason="ingredients list chicken" if status == "approved" else None,
            )
        )
        db.commit()

    return review


def menu_item(client):
    menus = client.get("/locations/5/menus", params={"date": "2026-10-06"}).json()
    return menus[0]["items"][0]


def test_menu_keeps_nc_state_tags_until_a_review_is_approved(client, one_earth):
    one_earth("pending")
    got = menu_item(client)
    assert got["diets"] == ["vegan", "vegetarian"]
    assert got["diets_removed"] == {}


def test_menu_and_filter_drop_approved_tags(client, one_earth):
    one_earth("approved")
    got = menu_item(client)
    assert got["diets"] == []
    assert got["diets_removed"] == {
        "vegan": "ingredients list chicken",
        "vegetarian": "ingredients list chicken",
    }

    menus = client.post(
        "/filters/locations/5/menus",
        params={"date": "2026-10-06"},
        json={"profiles": [VEGETARIAN]},
    ).json()
    result = menus[0]["items"][0]["results"][0]
    assert result["verdict"] == "incomplete"
    assert result["reasons"] == ["not labeled vegetarian"]
