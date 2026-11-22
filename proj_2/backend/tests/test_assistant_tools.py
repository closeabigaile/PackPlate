"""Tests for the assistant's tools (M3). They read the database and decide nothing themselves."""

from datetime import date, datetime, timedelta

from app.services import filter_engine
from app.services.assistant import tools
from app.services.hours import campus_time

DAY = date(2026, 10, 6)
NOON = campus_time(datetime(2026, 10, 6, 12, 0))


def listed(seed, loc_id, name, slug):
    """A location the API lists: it needs a menu with at least one item."""
    seed.location(loc_id, name, slug)
    seed.menu(loc_id * 10, loc_id, DAY, "Lunch")
    seed.item(loc_id * 10, "Soup")


def test_find_location_by_exact_name_part_and_misspelling(db, seed):
    """A full name, a part of a name, and a typo each find the right location."""
    listed(seed, 1, "Fountain Dining Hall", "fountain")
    listed(seed, 2, "Case Dining Hall", "case")

    assert tools.find_location(db, "Fountain Dining Hall")["match"]["id"] == 1
    assert tools.find_location(db, "  fountain ")["match"]["id"] == 1
    assert tools.find_location(db, "fountian")["match"]["id"] == 1


def test_find_location_asks_when_several_match(db, seed):
    """A name shared by several locations returns candidates and no single match."""
    listed(seed, 1, "Fountain Dining Hall", "fountain")
    listed(seed, 2, "Case Dining Hall", "case")

    found = tools.find_location(db, "dining hall")

    assert found["match"] is None
    assert {c["id"] for c in found["candidates"]} == {1, 2}


def test_find_location_finds_nothing_for_unrelated_text(db, seed):
    """Gibberish or blank text matches nothing, so the assistant can say it doesn't know."""
    listed(seed, 1, "Fountain Dining Hall", "fountain")

    assert tools.find_location(db, "zzzz") == {"match": None, "candidates": []}
    assert tools.find_location(db, "   ") == {"match": None, "candidates": []}


def test_get_menu_shows_numbers_only_when_there_is_a_label(db, seed):
    """Menus come back in meal order; an item without a label has no numbers; a meal can be picked."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Lunch")
    seed.menu(12, 1, DAY, "Dinner")
    seed.nutrition(
        "1|chicken|1 serving",
        location_id=1,
        serving_size="1 serving",
        calories=250.0,
        protein_g=38.0,
        sodium_mg=400.0,
    )
    seed.item(11, "Grilled Chicken", nutrition_key="1|chicken|1 serving")
    seed.item(11, "Mystery Stew")
    seed.item(12, "Rice")

    menu = tools.get_menu(db, 1, DAY)
    lunch = {i["name"]: i for i in menu["menus"][0]["items"]}

    assert [m["meal"] for m in menu["menus"]] == ["Lunch", "Dinner"]
    assert lunch["Grilled Chicken"]["protein_g"] == 38.0
    assert lunch["Grilled Chicken"]["nutrition_available"] is True
    assert lunch["Mystery Stew"]["protein_g"] is None
    assert lunch["Mystery Stew"]["nutrition_available"] is False
    assert [m["meal"] for m in tools.get_menu(db, 1, DAY, "dinner")["menus"]] == [
        "Dinner"
    ]


def test_get_menu_with_no_menu_is_empty_not_an_error(db, seed):
    """A day with no menu returns an empty list instead of failing."""
    seed.location(1)

    assert tools.get_menu(db, 1, DAY)["menus"] == []


def test_filter_items_never_puts_unconfirmed_items_in_fits(db, seed):
    """For a dairy-free profile: rice fits, mac and cheese conflicts, an unlabeled dish is unconfirmed."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Dinner")
    seed.nutrition("1|rice|1 cup", location_id=1, serving_size="1 cup", calories=200.0)
    seed.nutrition("1|mac|1 cup", location_id=1, serving_size="1 cup", calories=400.0)
    seed.item(11, "Steamed Rice", nutrition_key="1|rice|1 cup")
    seed.item(11, "Mac and Cheese", nutrition_key="1|mac|1 cup", allergens=["dairy"])
    seed.item(11, "Chef's Special")  # no label: can't be confirmed

    result = tools.filter_items(
        db, 1, DAY, filter_engine.Profile(avoid=frozenset({"dairy"}))
    )

    assert [i["name"] for i in result["fits"]] == ["Steamed Rice"]
    assert [i["name"] for i in result["incomplete"]] == ["Chef's Special"]
    assert result["incomplete"][0]["reasons"]
    assert result["conflicts"] == 1
    assert result["items_checked"] == 3


def test_get_status_open_closed_and_unknown(db, seed):
    """Open at noon, closed at 10pm, and unknown (not closed) on a day with no hours."""
    seed.location(1)
    seed.hours(1, DAY, "open", windows=[(420, 1260)])  # 7:00am to 9:00pm

    open_now = tools.get_status(db, 1, NOON)
    closed = tools.get_status(db, 1, NOON.replace(hour=22))
    unknown = tools.get_status(db, 1, NOON + timedelta(days=3))

    assert open_now["is_open"] is True
    assert open_now["closes_at"].startswith("2026-10-06T21:00")
    assert closed["is_open"] is False
    assert unknown["is_open"] is None


def test_get_crowd_uses_recent_reports_and_reports_none_when_empty(db, seed):
    """Recent reports set the level and the count; with none, the level is unknown (None)."""
    seed.location(1)
    seed.crowd(1, "crowded", NOON - timedelta(minutes=10))
    seed.crowd(1, "crowded", NOON - timedelta(minutes=3))
    seed.crowd(1, "not_busy", NOON - timedelta(hours=2))  # outside the window

    crowd = tools.get_crowd(db, 1, NOON)
    quiet = tools.get_crowd(db, 1, NOON - timedelta(days=1))

    assert crowd["level"] == "crowded"
    assert crowd["report_count"] == 2
    assert quiet == {
        "location_id": 1,
        "level": None,
        "report_count": 0,
        "last_reported_at": None,
    }


def test_list_locations_names_every_location_with_a_menu(db, seed):
    """Only locations that have menu items are listed, by name."""
    listed(seed, 1, "Fountain Dining Hall", "fountain")
    listed(seed, 2, "Case Dining Hall", "case")
    seed.location(3, "Empty Cafe", "empty")  # no menu, so not listed

    names = [loc["name"] for loc in tools.list_locations(db)["locations"]]

    assert names == ["Case Dining Hall", "Fountain Dining Hall"]
