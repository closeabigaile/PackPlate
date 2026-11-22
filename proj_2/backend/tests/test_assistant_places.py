"""Tests for campus places and walking estimates (M3). No database."""

import pytest

from app.services.assistant import places

TALLEY = (35.78397, -78.67092)
FOUNTAIN = (35.78547, -78.67764)


def test_distance_between_two_known_points_is_about_right():
    """Talley to Fountain is a few hundred metres, and a point is zero metres from itself."""
    assert places.distance_m(TALLEY, TALLEY) == pytest.approx(0)
    assert 500 < places.distance_m(TALLEY, FOUNTAIN) < 700


def test_walking_time_adds_the_winding_factor_and_is_at_least_a_minute():
    """800 m straight is 10 minutes at 80 m/min, 12 with paths; nearly zero still says 1."""
    assert places.walk_minutes(800) == round(800 * 1.25 / 80)
    assert places.walk_minutes(0) == 1


@pytest.mark.parametrize(
    "text, spot",
    [
        ("I am in Talley Student Union", "Talley Student Union"),
        ("i'm at tally union", "Talley Student Union"),
        ("near Hunt Library please", "Hunt Library"),
        ("by dh hill", "D. H. Hill Library"),
        ("for example I am at Lampe", "Lampe Drive"),
        ("I live in Bragaw", "Bragaw Hall"),
        ("im at lee hall", "Lee Hall"),
        ("near the brickyard", "Brickyard"),
        ("by the belltower", "Memorial Belltower"),
        ("at EB1", "Engineering Building I"),
        ("a gold medal", None),
        ("main campus", None),
        ("I'm in the valley", None),
    ],
)
def test_a_campus_place_is_found_in_a_message(text, spot):
    """Names, aliases and a close misspelling find the place; vague or unrelated text finds none."""
    found = places.find_spot(text)
    assert (found[0] if found else None) == spot


def test_every_campus_place_in_the_file_has_a_valid_point():
    """Every coordinate in the file is a latitude and longitude near Raleigh."""
    points = [spot["at"] for spot in places.load()["spots"].values()]
    assert points
    for lat, lng in points:
        assert 35.7 < lat < 35.9 and -78.8 < lng < -78.5


def test_miles_are_rounded_to_one_decimal_and_never_zero():
    """16 km is about 10 miles; a few metres still reads as 0.1."""
    assert places.miles(16093) == 10.0
    assert places.miles(5) == 0.1
