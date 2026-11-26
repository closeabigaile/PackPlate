"""The icon-only baseline, and where it differs from PackPlate's filter."""

from types import SimpleNamespace

import pytest

from app.services import filter_engine
from app.services.filter_engine import CONFLICTS, FITS, INCOMPLETE, Profile
from eval import baseline
from ingestion.normalize import (
    ALLERGEN_TRAITS,
    DIET_TRAITS,
    split_contains,
    split_traits,
)

NO_NUTS = Profile(avoid=frozenset({"nuts"}))
VEGAN = Profile(diets=frozenset({"vegan"}))
VEGETARIAN = Profile(diets=frozenset({"vegetarian"}))


def packplate(icons, contains=None, has_label=True):
    """The same item through PackPlate's real engine, built the way ingestion does."""
    allergens, diets, unknown = split_traits(icons)
    if contains:
        extra, unknown_contains = split_contains(contains)
        allergens |= extra
        unknown += unknown_contains
    item = SimpleNamespace(
        allergens=sorted(allergens),
        diets=sorted(diets),
        unrecognized_traits=unknown,
        nutrition=(
            SimpleNamespace(protein_g=1, calories=1, sodium_mg=1) if has_label else None
        ),
    )
    return filter_engine.check(item, NO_NUTS).verdict


def test_allergen_icon_conflicts():
    assert baseline.check(["Contains Nuts"], NO_NUTS) == CONFLICTS


def test_no_icon_fits():
    assert baseline.check([], NO_NUTS) == FITS
    assert baseline.check(["Contains Dairy"], NO_NUTS) == FITS


def test_allergen_only_in_contains_line_still_fits_the_baseline():
    # The gap M0 measures: the label lists nuts, but there's no icon.
    assert baseline.check([], NO_NUTS) == FITS
    assert packplate([], contains=["Contains Nuts"]) == CONFLICTS


def test_missing_label_still_fits_the_baseline():
    assert baseline.check([], NO_NUTS) == FITS
    assert packplate([], has_label=False) == INCOMPLETE


def test_unknown_trait_still_fits_the_baseline():
    assert baseline.check(["Unknown"], NO_NUTS) == FITS
    assert packplate(["Unknown"]) == INCOMPLETE


def test_diet_needs_its_icon():
    assert baseline.check(["Vegan"], VEGAN) == FITS
    assert baseline.check([], VEGAN) == CONFLICTS
    assert baseline.check(["Vegetarian"], VEGAN) == CONFLICTS


def test_vegan_counts_as_vegetarian_like_packplate():
    assert baseline.check(["Vegan"], VEGETARIAN) == FITS
    assert filter_engine.DIET_SATISFIED_BY["vegetarian"] >= {"vegan"}


def test_needs_every_required_diet_and_no_avoided_allergen():
    both = Profile(avoid=frozenset({"soy"}), diets=frozenset({"vegan", "halal"}))
    assert baseline.check(["Vegan", "Halal (U)"], both) == FITS
    assert baseline.check(["Vegan"], both) == CONFLICTS
    assert baseline.check(["Vegan", "Halal (U)", "Soy"], both) == CONFLICTS


def test_goals_are_refused():
    with pytest.raises(ValueError):
        baseline.check([], Profile(min_protein_g=10))


def test_uses_the_same_keys_as_packplate():
    assert set(ALLERGEN_TRAITS.values()) == set(filter_engine.ALLERGEN_KEYS)
    assert set(filter_engine.DIET_KEYS) <= set(DIET_TRAITS.values())


@pytest.mark.parametrize("icon,key", sorted(ALLERGEN_TRAITS.items()))
def test_every_allergen_icon_is_recognized(icon, key):
    assert baseline.check([icon], Profile(avoid=frozenset({key}))) == CONFLICTS
