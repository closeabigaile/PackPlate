"""Tests for the saved positions of dining locations (M3)."""

from datetime import date, datetime

from sqlalchemy import select

from app.repositories import location_points
from app.services.assistant import chat
from app.services.hours import campus_time
from db import seed_location_points
from db.assistant_models import LocationPoint
from db.models import Location

DAY = date(2026, 10, 6)
NOON = campus_time(datetime(2026, 10, 6, 12, 0))


def test_seeding_saves_the_locations_that_exist_and_reports_the_rest(db, seed):
    """Positions are matched by name; a name with no location in the database is returned."""
    seed.location(1)
    points = {
        "Fountain Dining Hall": (35.78547, -78.67764),
        "Nowhere Hall": (35.7, -78.6),
    }

    missing = seed_location_points.seed(db, points)

    assert missing == ["Nowhere Hall"]
    assert location_points.points(db) == {1: (35.78547, -78.67764)}


def test_seeding_twice_updates_instead_of_duplicating(db, seed):
    """Running the script again with a corrected position replaces the old one."""
    seed.location(1)
    seed_location_points.seed(db, {"Fountain Dining Hall": (35.78, -78.67)})

    seed_location_points.seed(db, {"Fountain Dining Hall": (35.79, -78.68)})

    assert location_points.points(db) == {1: (35.79, -78.68)}


def test_a_position_goes_when_its_location_goes(db, seed):
    """Deleting a location deletes its position with it (no orphans)."""
    seed.location(1)
    seed.point(1, 35.78, -78.67)

    db.delete(db.get(Location, 1))
    db.commit()

    assert db.scalars(select(LocationPoint)).all() == []


def test_the_real_seed_data_is_in_range():
    """Every position in the seed script is a latitude and longitude near Raleigh."""
    for name, (lat, lng) in seed_location_points.POINTS.items():
        assert 35.7 < lat < 35.9 and -78.8 < lng < -78.5, name


def test_with_no_saved_positions_the_assistant_says_it_cannot_tell(db, seed):
    """A location nobody has a position for can't be ranked, and the reply says so."""
    seed.location(1, name="Nowhere Dining Hall", slug="nowhere")
    seed.menu(11, 1, DAY, "Dinner")
    seed.item(11, "Steamed Rice")

    reply = chat.respond(db, "I'm at Talley, which dining hall is close?", None, NOON)[
        "reply"
    ]

    assert "I can't tell which dining hall is closest" in reply


def test_positions_fill_themselves_in_the_first_time_they_are_needed(db, seed):
    """No one runs the seed script: asking "which hall is close?" saves the known positions."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Dinner")
    seed.item(11, "Steamed Rice")
    assert location_points.points(db) == {}

    reply = chat.respond(db, "I'm at Talley, which dining hall is close?", None, NOON)[
        "reply"
    ]

    assert "- Fountain Dining Hall (about " in reply
    assert 1 in location_points.points(db)


def test_filling_in_never_changes_a_position_that_is_already_saved(db, seed):
    """A corrected position stays; only the missing ones are added."""
    seed.location(1)
    seed.point(1, 35.5, -78.5)  # hand-corrected

    seed_location_points.ensure(db)

    assert location_points.points(db) == {1: (35.5, -78.5)}
