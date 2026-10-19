from ingestion.ingredients import WORDS, matched_terms, possible_allergens
from ingestion.normalize import ALLERGEN_KEYS


def test_keys_match_the_filter_allergen_keys_plus_diet_keys():
    assert set(WORDS) == set(ALLERGEN_KEYS) | {"meat", "honey"}


def test_same_text_always_gives_the_same_sorted_keys():
    text = "Wheat Flour, Milk, Sesame Seeds, Peanuts"
    assert possible_allergens(text) == possible_allergens(text)
    assert possible_allergens(text) == ["dairy", "gluten", "nuts", "sesame"]


def test_matched_terms_names_the_words_that_matched():
    assert matched_terms("Enriched Flour, Blueberries, Whey, Butter") == {
        "dairy": ["butter", "whey"],
        "gluten": ["flour"],
    }
    assert matched_terms("Water, Salt") == {}
    assert matched_terms(None) == {}


def test_m0_false_fits_are_caught():
    # Real ingredient text from the six M0 false fits (issue #15), shortened.
    assert "dairy" in possible_allergens(
        "Enriched Flour, Blueberries, Sugar, Whey, Salt"
    )
    assert "sesame" in possible_allergens(
        "Bread (Wheat Flour, Water, Sesame Seeds if present)"
    )
    assert "meat" in possible_allergens(
        "Broccoli, Cheese Sauce, Seasoning (Cooked Chicken Fat, Salt)"
    )
    assert "nuts" in possible_allergens(
        "Sunflower Kernels, Vegetable Oil (Peanut, Cottonseed, Soybean and/or Sunflower Seed), Sea Salt"
    )


def test_look_alikes_are_not_flagged():
    assert possible_allergens("Coconut Milk, Cocoa Butter, Rice Flour") == []
    assert possible_allergens("Soybean Oil, Vinegar, Sugar") == []
    assert possible_allergens("Vegan Chorizo (Soy Protein), Peppers") == ["soy"]


def test_tree_nuts_follow_the_fda_2025_list():
    assert possible_allergens("Heartnut, Pinon") == ["nuts"]
    # Removed from the FDA tree nut list in 2025.
    assert possible_allergens("Chestnut, Coconut, Shea") == []


def test_fda_milk_and_egg_include_other_animals():
    assert possible_allergens("Chevre, Duck Eggs") == ["dairy", "egg"]


def test_gluten_grains_include_all_wheat_species():
    assert possible_allergens("Kamut, Einkorn") == ["gluten"]


def test_honey_is_flagged_for_vegan_checks():
    assert possible_allergens("Oats, Honey") == ["honey"]


def test_plant_based_imitations_are_not_flagged():
    # Real phrases from NC State's ingredient text.
    assert possible_allergens("Vegan Mozzarella (Coconut Oil, Potato Starch)") == []
    assert possible_allergens("Plant-Based Beef Strips (Water, Pea Protein)") == []
    assert possible_allergens("Impossible Sausage (Water, Sunflower Oil)") == []
    assert possible_allergens("Beyond Meat Burger Patty (Pea Protein)") == []
    assert possible_allergens("Dairy-Free Cheese (Cashews)") == ["nuts"]


def test_nc_state_vegan_mozzarella_is_not_dairy():
    text = (
        "Vegan Mozzarella (Mozzarella Style Shred (Filtered Water, Modified Potato "
        "Starch, Palm Oil, Sunflower Oil, Cassava Flour, Oat Fiber, Sea Salt))"
    )
    assert possible_allergens(text) == []
    # A real "-style" cheese is still flagged.
    assert possible_allergens("Parmesan-Style Cheese (Milk, Salt)") == ["dairy"]


def test_oyster_crackers_are_not_seafood():
    # Real text from NC State's "Ranch Oyster Crackers", shortened.
    text = "Oyster Crackers (Whole Grain Wheat Flour, Soybean Oil, Salt)"
    assert possible_allergens(text) == ["gluten"]
    assert possible_allergens("Smoked Oysters, Crackers") == ["seafood"]


def test_plant_based_rule_only_skips_the_next_word():
    assert possible_allergens("Vegan Pesto with Cheese") == ["dairy"]
    # Real allergens inside an imitation are still flagged.
    assert possible_allergens(
        "Plant-Based Beef Strips (Water, Vital Wheat Gluten, Soy Protein Isolate)"
    ) == ["gluten", "soy"]


def test_peanut_butter_is_still_a_nut():
    assert possible_allergens("Peanut Butter, Celery") == ["nuts"]


def test_free_of_phrases_are_not_flagged():
    assert possible_allergens("Gluten-Free Oats, Non-Dairy Creamer") == []


def test_cross_contact_warnings_are_ignored():
    text = (
        "Sunflower Seeds, Sea Salt. Processed in a facility that also processes "
        "peanuts, tree nuts, milk, egg, wheat, soybeans and sesame."
    )
    assert possible_allergens(text) == []


def test_no_text_means_no_flags():
    assert possible_allergens(None) == []
    assert possible_allergens("") == []
