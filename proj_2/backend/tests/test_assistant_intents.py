"""Tests for understanding messages (M3). No database: the parser is pure text."""

import pytest

from app.services.assistant.intents import parse

NAMES = [
    "Fountain Dining Hall",
    "Case Dining Hall",
    "Atrium – Brickyard Pizza",
    "Atrium – Smoothie U",
]


@pytest.mark.parametrize(
    "text, kind",
    [
        ("What's for dinner at Fountain tonight?", "food"),
        ("vegan options at Fountain", "food"),
        ("high protein dinner under 600 calories", "food"),
        ("Is Fountain busy right now?", "crowd"),
        ("Where's the shortest line?", "crowd"),
        ("When does Clark close tonight?", "status"),
        ("What's open right now?", "status"),
        ("What's open for dinner?", "status"),
        ("Is this safe for my peanut allergy?", "safety"),
        ("What should I take for an allergic reaction?", "medical"),
        ("hello", "help"),
        ("What can you do?", "help"),
        ("tell me a joke", "unknown"),
        ("how many dinining hall are there", "locations"),
        ("list all dining halls", "locations"),
        ("which dinning hall do you recommend", "recommend"),
        ("what's the best dining hall?", "recommend"),
        ("what dining halls are open", "status"),
        ("where can I eat right now?", "recommend"),
        ("where should we eat tonight", "recommend"),
        ("where can I get lunch", "recommend"),
        ("how many calories in the rice", "food"),
        ("I am in main campus which dining hall is close", "nearby"),
        ("I am in Tally union which dining hall is close", "nearby"),
        ("which dining hall is closest to me", "nearby"),
        ("how far is fountain from here", "nearby"),
        ("which dining hall is near Talley", "nearby"),
        ("dining halls close to Hunt Library", "nearby"),
        ("when does fountain close tonight?", "status"),
    ],
)
def test_kind_of_question(text, kind):
    """Each example message is classified as the right kind of question."""
    assert parse(text, NAMES).kind == kind


@pytest.mark.parametrize(
    "text, meal, day_offset",
    [
        ("dinner tomorrow", "dinner", 1),
        ("breakfast", "breakfast", 0),
        ("what's for lunch", "lunch", 0),
        ("tonight", "dinner", 0),
        ("late night food", "late night", 0),
        ("this morning", "breakfast", 0),
        ("anything", None, 0),
    ],
)
def test_meal_and_day(text, meal, day_offset):
    """Meal words, "tonight", "this morning" and "tomorrow" become a meal and a day."""
    intent = parse(text)
    assert (intent.meal, intent.day_offset) == (meal, day_offset)


@pytest.mark.parametrize(
    "text, avoid",
    [
        ("no dairy and gluten free", {"dairy", "gluten"}),
        ("nut-free", {"nuts"}),
        ("I have a peanut allergy", {"nuts"}),
        ("without eggs", {"egg"}),
        ("I'm allergic to soy", {"soy"}),
        ("I'm fine with dairy", set()),
    ],
)
def test_allergens_to_avoid(text, avoid):
    """Ways of saying "avoid this allergen" are recognised, and a casual "fine with dairy" is not."""
    assert parse(text).avoid == avoid


def test_diets():
    """Diet words become required diets; a message without them has none."""
    assert parse("vegan and halal options").diets == {"vegan", "halal"}
    assert parse("anything").diets == frozenset()


@pytest.mark.parametrize(
    "text, protein, calories",
    [
        ("high protein", 30, None),
        ("at least 40 g protein", 40, None),
        ("40g of protein", 40, None),
        ("under 600 calories", None, 600),
        ("less than 450 cal", None, 450),
        ("below 700 kcal", None, 700),
        ("high-protein and under 500 calories", 30, 500),
        ("anything", None, None),
    ],
)
def test_nutrition_goals(text, protein, calories):
    """ "High protein", gram amounts and calorie limits become numbers for the filter."""
    intent = parse(text)
    assert (intent.min_protein_g, intent.max_calories) == (protein, calories)


@pytest.mark.parametrize(
    "text, location",
    [
        ("what's for dinner at Fountain tonight?", "Fountain Dining Hall"),
        ("is case busy?", "Case Dining Hall"),
        (
            "what high-protein items are at Atrium – Brickyard Pizza,",
            "Atrium – Brickyard Pizza",
        ),
        ("menu at atrium", "atrium"),  # fits two places: the assistant asks which
        ("menu at fountian", "fountian"),  # a typo: tools.find_location fixes it
        ("what's open at 9 pm", None),
        ("anything with at least 30 g protein", None),
        ("is it busy at lunch?", None),
    ],
)
def test_location_in_message(text, location):
    """A known name, a typo after "at", and text that isn't a place (a time, "at least") are told apart."""
    assert parse(text, NAMES).location_text == location
