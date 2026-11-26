"""The ingredient scan, on ingredient text written the way NC State's labels write it."""

import pytest

from eval.profiles import TEST_PROFILES
from eval.scan import scan
from eval.wordlist import WORDS


def terms(text, key):
    return scan(text, key).terms


def test_every_test_profile_has_a_word_list():
    assert set(WORDS) == set(TEST_PROFILES)
    assert len(TEST_PROFILES) == 11


@pytest.mark.parametrize(
    "text,key,expected",
    [
        ("Butter (Cream, Salt)", "avoid_dairy", ["butter", "cream"]),
        ("Parmesan Cheese (Cultured Milk, Salt, Enzymes)", "avoid_dairy",
         ["cheese", "milk", "parmesan"]),
        ("PENNE PASTA (SEMOLINA, ENRICHED FLOUR)", "avoid_gluten",
         ["flour", "semolina"]),
        ("Breaded With: Wheat Flour, Water", "avoid_gluten", ["flour", "wheat"]),
        ("Basil, Pine Nuts, Garlic", "avoid_nuts", ["nut", "pine nut"]),
        ("Eggs, Sugar", "avoid_egg", ["egg"]),
        ("Caesar Dressing (Anchovies, Oil)", "avoid_seafood", ["anchovies"]),
        ("Tahini, Lemon", "avoid_sesame", ["tahini"]),
        ("Soy Sauce (Water, Soybeans, Wheat)", "avoid_soy", ["soy", "soybean"]),
        ("Chicken Broth, Carrot", "diet_vegetarian", ["chicken"]),
        ("Honey, Oats", "diet_vegan", ["honey"]),
        ("Pork Sausage, Onion", "diet_halal", ["pork"]),
        ("Red Wine, Garlic", "diet_halal", ["wine"]),
    ],
)  # fmt: skip
def test_flags_real_ingredients(text, key, expected):
    assert terms(text, key) == expected


@pytest.mark.parametrize(
    "text,key",
    [
        ("Coconut Milk, Rice", "avoid_dairy"),
        ("Cocoa Butter, Sugar", "avoid_dairy"),
        ("Cream of Tartar", "avoid_dairy"),
        ("Rice Flour, Corn Flour", "avoid_gluten"),
        ("Gluten-Free Flour Blend", "avoid_gluten"),
        ("Maltodextrin, Salt", "avoid_gluten"),
        ("Nutmeg, Butternut Squash, Coconut, Doughnut Glaze", "avoid_nuts"),
        ("Eggplant, Tomato", "avoid_egg"),
        ("Graham Crackers, Hamburger Bun", "avoid_pork"),
        ("Turkey Bacon", "avoid_pork"),
        ("Soybean Oil, Salt", "avoid_soy"),
        ("Red Wine Vinegar, Oil", "diet_halal"),
        ("Halal Chicken (Chicken (Halal))", "diet_halal"),
        ("Dairy-Free Spread, Non-Dairy Creamer", "avoid_dairy"),
        ("Milk-Free Margarine", "avoid_dairy"),
        ("Egg-Free Dressing", "avoid_egg"),
        ("Soy Free Seasoning", "avoid_soy"),
    ],
)
def test_look_alikes_are_not_flagged(text, key):
    assert terms(text, key) == []


def test_free_of_phrase_does_not_hide_a_real_word_after_it():
    # "dairy-free" goes, but "cheese" is still a word for a person to check.
    assert terms("Dairy-Free Cheese Sauce", "avoid_dairy") == ["cheese"]


def test_matching_ignores_case_and_handles_plurals():
    assert terms("ALMONDS, CASHEWS", "avoid_nuts") == ["almond", "cashew"]


def test_cross_contact_warnings_are_kept_apart():
    hits = scan(
        "Oats, Sugar. Made in a facility that also processes peanuts and milk.",
        "avoid_nuts",
    )
    assert hits.terms == []
    assert hits.advisory == ["peanut"]


def test_may_contain_is_advisory():
    hits = scan("Chocolate Chips (Sugar, Cocoa). May contain tree nuts.", "avoid_nuts")
    assert (hits.terms, hits.advisory) == ([], ["nut"])


def test_ingredient_and_warning_both_count_once():
    hits = scan("Peanuts, Salt. May contain peanuts.", "avoid_nuts")
    assert (hits.terms, hits.advisory) == (["peanut"], [])


def test_vegan_includes_vegetarian_dairy_and_egg_words():
    for word in ["Beef", "Milk", "Egg", "Gelatin"]:
        assert terms(word, "diet_vegan"), word


def test_no_ingredient_text_gives_no_hits():
    assert scan(None, "avoid_dairy").terms == []
    assert scan("", "avoid_dairy").advisory == []
