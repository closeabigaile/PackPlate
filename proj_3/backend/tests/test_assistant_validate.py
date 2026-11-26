"""Tests for checking a reply against its tool result (M3). No database needed."""

from app.services.assistant import answers, validate

ITEM = {
    "id": 7,
    "name": "Steamed Rice",
    "station": None,
    "serving_size": "1 cup",
    "calories": 200.0,
    "protein_g": 4.0,
    "sodium_mg": None,
    "nutrition_available": True,
    "meal": "Dinner",
    "verdict": "fits",
    "reasons": [],
}
FILTERED = {
    "location_id": 1,
    "date": "2026-10-06",
    "items_checked": 3,
    "fits": [ITEM],
    "incomplete": [
        {
            **ITEM,
            "id": 9,
            "name": "Chef's Special",
            "verdict": "incomplete",
            "reasons": ["no nutrition label"],
            "calories": None,
            "protein_g": None,
        }
    ],
    "conflicts": 1,
}
MENU = {
    "location_id": 1,
    "date": "2026-10-06",
    "menus": [
        {
            "meal": "Dinner",
            "scraped": True,
            "items": [{**ITEM, "name": "Mac and Cheese"}, ITEM],
        }
    ],
}
LOCATIONS = ["Fountain Dining Hall", "Case Dining Hall"]


def check(reply, result, warning=False):
    """Validate a reply as if it were for Fountain, the only location it may mention."""
    return validate.problems(
        reply,
        result,
        allowed_locations=["Fountain Dining Hall"],
        all_locations=LOCATIONS,
        require_warning=warning,
    )


def test_the_real_replies_pass_the_check():
    """Replies built by answers.py from a result are consistent with that result."""
    filtered, _ = answers.food_filtered(
        "Fountain Dining Hall", FILTERED, "today", "dinner"
    )
    menu, _ = answers.food_menu("Fountain Dining Hall", MENU, "today", None)
    status = {
        "is_open": True,
        "closes_at": "2026-10-06T21:00:00-04:00",
        "opens_next_at": None,
    }
    crowd = {
        "level": "crowded",
        "report_count": 2,
        "last_reported_at": "2026-10-06T11:57:00-04:00",
    }

    assert check(filtered, FILTERED, warning=True) == []
    assert check(menu, MENU, warning=True) == []
    assert check(answers.status_one("Fountain Dining Hall", status), status) == []
    assert check(answers.crowd("Fountain Dining Hall", crowd), crowd) == []


def test_a_number_the_result_does_not_have_is_caught():
    """A calorie figure that no tool returned is flagged."""
    reply = (
        "1 item at Fountain Dining Hall today fits your filters:\n- Steamed Rice (999 cal)\n"
        + answers.LABEL_WARNING
    )

    assert any("999" in p for p in check(reply, FILTERED, warning=True))


def test_a_dish_the_result_does_not_have_is_caught():
    """A listed dish that no tool returned is flagged, in both list and menu replies."""
    listed = "- Lobster Bisque (200 cal)\n" + answers.LABEL_WARNING
    menu_line = "Dinner: Mac and Cheese, Lobster Bisque\n" + answers.LABEL_WARNING

    assert any("Lobster" in p for p in check(listed, FILTERED, warning=True))
    assert any("Lobster" in p for p in check(menu_line, MENU, warning=True))


def test_dish_names_with_commas_or_brackets_are_accepted():
    """Names such as "Soup (Vegan)" or "Rice, Beans" are real dishes, not mismatches."""
    menu = {
        "menus": [
            {
                "meal": "Lunch",
                "scraped": True,
                "items": [
                    {**ITEM, "name": "Soup (Vegan)"},
                    {**ITEM, "name": "Rice, Beans"},
                ],
            }
        ]
    }
    reply, _ = answers.food_menu("Fountain Dining Hall", menu, "today", None)

    assert check(reply, menu, warning=True) == []


def test_claims_of_safety_are_banned():
    """Words that claim safety are flagged even if the numbers are right."""
    for phrase in ("This is safe for you.", "Totally allergy-free.", "Guaranteed."):
        assert any("banned" in p for p in check(phrase, FILTERED))


def test_a_different_location_and_a_missing_warning_are_caught():
    """Mentioning another location, or leaving out the label warning on food, is flagged."""
    other = check("Case Dining Hall has 1 item.", FILTERED)
    no_warning = check("- Steamed Rice (200 cal)", FILTERED, warning=True)

    assert any("Case Dining Hall" in p for p in other)
    assert any("warning" in p for p in no_warning)


def test_times_must_match_the_result():
    """The closing time in a reply must be the one in the tool result."""
    status = {
        "is_open": True,
        "closes_at": "2026-10-06T21:00:00-04:00",
        "opens_next_at": None,
    }

    assert check("Fountain Dining Hall is open until 9:00 pm.", status) == []
    assert any(
        "10" in p for p in check("Fountain Dining Hall is open until 10:00 pm.", status)
    )
