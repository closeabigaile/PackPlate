"""services/filter_engine.py: no database."""

import typing
from dataclasses import dataclass, field

import pytest

from app.schemas.filters import Allergen, Diet
from app.services.filter_engine import (
    ALLERGEN_KEYS,
    CONFLICTS,
    DIET_DOUBTED_BY,
    DIET_EXCLUDES,
    DIET_KEYS,
    DIET_SATISFIED_BY,
    FITS,
    INCOMPLETE,
    Profile,
    check,
    count,
)


@dataclass
class Label:
    protein_g: float | None = 20
    calories: float | None = 300
    sodium_mg: float | None = 400
    ingredient_flags: dict = field(default_factory=dict)


@dataclass
class Item:
    allergens: list = field(default_factory=list)
    diets: list = field(default_factory=list)
    unrecognized_traits: list = field(default_factory=list)
    nutrition: Label | None = field(default_factory=Label)


NUTS = Profile(avoid=frozenset({"nuts"}))


def test_no_constraints_fits_anything():
    assert (
        check(Item(nutrition=None, unrecognized_traits=["?"]), Profile()).verdict
        == FITS
    )


def test_labelled_item_without_the_allergen_fits():
    result = check(Item(allergens=["gluten"]), NUTS)
    assert (result.verdict, result.reasons) == (FITS, [])


def test_listed_allergen_conflicts():
    result = check(
        Item(allergens=["nuts", "dairy"]),
        Profile(avoid=frozenset({"nuts", "dairy", "soy"})),
    )
    assert result.verdict == CONFLICTS
    assert result.reasons == ["contains dairy", "contains nuts"]


def test_no_label_is_incomplete_for_allergies_never_fits():
    result = check(Item(nutrition=None), NUTS)
    assert result.verdict == INCOMPLETE
    assert result.reasons == ["no nutrition label: allergens come from icons only"]


def test_unrecognized_trait_is_incomplete_never_fits():
    result = check(
        Item(unrecognized_traits=["Contains Shellfish"]),
        Profile(avoid=frozenset({"seafood"})),
    )
    assert result.verdict == INCOMPLETE
    assert "Contains Shellfish" in result.reasons[0]


def test_known_allergen_beats_missing_data():
    assert (
        check(
            Item(allergens=["nuts"], nutrition=None, unrecognized_traits=["?"]), NUTS
        ).verdict
        == CONFLICTS
    )


def test_missing_data_doesnt_matter_without_allergies():
    vegan = Profile(diets=frozenset({"vegan"}))
    assert (
        check(
            Item(diets=["vegan"], nutrition=None, unrecognized_traits=["?"]), vegan
        ).verdict
        == FITS
    )


def test_diet_tag_fits_and_vegan_counts_as_vegetarian():
    vegetarian = Profile(diets=frozenset({"vegetarian"}))
    assert check(Item(diets=["vegetarian"]), vegetarian).verdict == FITS
    assert check(Item(diets=["vegan"]), vegetarian).verdict == FITS


def test_vegetarian_does_not_count_as_vegan_and_vegan_not_as_halal():
    assert (
        check(Item(diets=["vegetarian"]), Profile(diets=frozenset({"vegan"}))).verdict
        == INCOMPLETE
    )
    assert (
        check(Item(diets=["vegan"]), Profile(diets=frozenset({"halal"}))).verdict
        == INCOMPLETE
    )


def test_untagged_item_is_incomplete_for_a_diet():
    result = check(Item(), Profile(diets=frozenset({"halal"})))
    assert (result.verdict, result.reasons) == (INCOMPLETE, ["not labeled halal"])


@pytest.mark.parametrize(
    "diet, allergen",
    [
        ("halal", "pork"),
        ("vegetarian", "pork"),
        ("vegetarian", "seafood"),
        ("vegan", "pork"),
        ("vegan", "seafood"),
        ("vegan", "dairy"),
        ("vegan", "egg"),
    ],
)
def test_allergen_that_rules_out_a_diet_conflicts(diet, allergen):
    result = check(Item(allergens=[allergen]), Profile(diets=frozenset({diet})))
    assert result.verdict == CONFLICTS
    assert result.reasons == [f"not {diet}: contains {allergen}"]


def test_every_required_diet_must_hold():
    both = Profile(diets=frozenset({"halal", "vegetarian"}))
    assert check(Item(diets=["vegetarian"]), both).verdict == INCOMPLETE
    assert check(Item(diets=["halal", "vegetarian"]), both).verdict == FITS


def test_protein_goal():
    goal = Profile(min_protein_g=20)
    assert check(Item(nutrition=Label(protein_g=20)), goal).verdict == FITS
    result = check(Item(nutrition=Label(protein_g=6.5)), goal)
    assert (result.verdict, result.reasons) == (CONFLICTS, ["protein 6.5g below 20g"])


def test_calorie_and_sodium_limits():
    assert (
        check(Item(nutrition=Label(calories=600)), Profile(max_calories=600)).verdict
        == FITS
    )
    assert check(
        Item(nutrition=Label(calories=601)), Profile(max_calories=600)
    ).reasons == ["calories 601 above 600"]
    assert check(
        Item(nutrition=Label(sodium_mg=900)), Profile(max_sodium_mg=800)
    ).reasons == ["sodium 900mg above 800mg"]


def test_goal_without_data_is_incomplete_not_zero():
    goal = Profile(
        min_protein_g=0
    )  # even a goal of 0 can't be checked without a number
    assert check(Item(nutrition=Label(protein_g=None)), goal).reasons == [
        "protein not published"
    ]
    assert check(Item(nutrition=None), goal).reasons == [
        "no nutrition label: can't check protein"
    ]
    assert check(Item(nutrition=None), goal).verdict == INCOMPLETE


def test_conflict_lists_every_reason_conflicts_first():
    profile = Profile(
        avoid=frozenset({"nuts"}), diets=frozenset({"vegan"}), min_protein_g=30
    )
    result = check(Item(allergens=["nuts"], nutrition=Label(protein_g=None)), profile)
    assert result.verdict == CONFLICTS
    assert result.reasons == [
        "contains nuts",
        "not labeled vegan",
        "protein not published",
    ]


def test_count():
    items = [Item(), Item(allergens=["nuts"]), Item(nutrition=None)]
    assert vars(count(items, NUTS)) == {"fits": 1, "incomplete": 1, "conflicts": 1}


def test_rule_tables_cover_every_diet():
    assert set(DIET_SATISFIED_BY) == set(DIET_EXCLUDES) == set(DIET_KEYS)
    assert all(excluded <= set(ALLERGEN_KEYS) for excluded in DIET_EXCLUDES.values())


def test_request_schema_accepts_exactly_the_engine_keys():
    assert set(typing.get_args(Allergen)) == set(ALLERGEN_KEYS)
    assert set(typing.get_args(Diet)) == set(DIET_KEYS)


DAIRY = Profile(avoid=frozenset({"dairy"}))


def test_avoided_allergen_in_ingredients_is_incomplete_not_fits():
    # M0 false fit: whey in the pancakes, no dairy icon.
    item = Item(
        allergens=["gluten"],
        nutrition=Label(ingredient_flags={"dairy": ["whey"], "gluten": ["flour"]}),
    )
    result = check(item, DAIRY)
    assert result.verdict == INCOMPLETE
    assert result.reasons == ["ingredients mention whey: may contain dairy"]


def test_ingredient_flag_never_makes_a_conflict_on_its_own():
    item = Item(nutrition=Label(ingredient_flags={"dairy": ["whey"]}))
    assert check(item, DAIRY).verdict != CONFLICTS


def test_confirmed_allergen_still_conflicts():
    item = Item(
        allergens=["dairy"], nutrition=Label(ingredient_flags={"dairy": ["whey"]})
    )
    result = check(item, DAIRY)
    assert (result.verdict, result.reasons) == (CONFLICTS, ["contains dairy"])


def test_flag_for_an_allergen_the_profile_allows_still_fits():
    item = Item(nutrition=Label(ingredient_flags={"gluten": ["flour"]}))
    assert check(item, DAIRY).verdict == FITS


def test_tagged_vegetarian_with_meat_in_ingredients_is_incomplete():
    # M0 false fit: chicken fat in a soup tagged Vegetarian.
    item = Item(
        diets=["vegetarian"],
        nutrition=Label(ingredient_flags={"dairy": ["cheese"], "meat": ["chicken"]}),
    )
    result = check(item, Profile(diets=frozenset({"vegetarian"})))
    assert result.verdict == INCOMPLETE
    assert result.reasons == ["tagged vegetarian, but ingredients mention chicken"]


def test_tagged_vegan_with_honey_in_ingredients_is_incomplete():
    item = Item(diets=["vegan"], nutrition=Label(ingredient_flags={"honey": ["honey"]}))
    result = check(item, Profile(diets=frozenset({"vegan"})))
    assert result.reasons == ["tagged vegan, but ingredients mention honey"]


def test_diet_doubt_keys_match_what_ingestion_scans():
    pytest.importorskip("bs4")  # ingestion's own dependency
    from ingestion.ingredients import WORDS

    for diet, keys in DIET_DOUBTED_BY.items():
        assert keys <= set(WORDS), diet


def test_engine_keys_match_what_ingestion_writes():
    pytest.importorskip("bs4")  # ingestion's own dependency
    from ingestion.normalize import ALLERGEN_KEYS as WRITTEN_ALLERGENS
    from ingestion.normalize import DIET_KEYS as WRITTEN_DIETS

    assert set(ALLERGEN_KEYS) == set(WRITTEN_ALLERGENS)
    assert set(DIET_KEYS) == set(WRITTEN_DIETS) - {"sustainable"}
