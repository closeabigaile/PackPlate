"""Dietary filter engine.

Checks menu items against one or more dietary profiles and labels each
result as fits, conflicts, or incomplete (data incomplete). Never treats
missing allergen data as safe. Pure functions, no database.

The rules, per profile (a wrong "fits" can hurt someone, so every gap in the
data makes a result incomplete, never fits):

Allergens the profile avoids
    the item lists one (icon, or its label's "Contains:")   conflicts
    the item has a trait or "Contains:" name we don't know  incomplete: it might be one
    the item has no nutrition label                         incomplete: icons alone may miss one
Diets the profile requires
    the item is tagged with it (vegan also counts as vegetarian)        fits
    the item lists an allergen the diet rules out (DIET_EXCLUDES)       conflicts
    otherwise                                                           incomplete: untagged
                                                                        doesn't prove either way
Goals (min protein, max calories, max sodium)
    no label, or the label doesn't give that nutrient       incomplete
    outside the limit                                       conflicts

Overall: any conflict -> conflicts, else any incomplete -> incomplete, else fits.
"""

from dataclasses import dataclass, field

# Keys ingestion/normalize.py writes to menu_items.allergens and .diets. A test
# checks these match, so a key added there can't be silently unfilterable here.
ALLERGEN_KEYS = ("dairy", "egg", "gluten", "nuts", "pork", "seafood", "sesame", "soy")
DIET_KEYS = (
    "halal",
    "vegan",
    "vegetarian",
)  # "sustainable" is a tag, not a restriction

# Diet tags that satisfy a required diet.
DIET_SATISFIED_BY = {
    "halal": {"halal"},
    "vegan": {"vegan"},
    "vegetarian": {"vegetarian", "vegan"},
}
# Allergen keys that prove an item isn't fit for a diet.
DIET_EXCLUDES = {
    "halal": {"pork"},
    "vegan": {"pork", "seafood", "dairy", "egg"},
    "vegetarian": {"pork", "seafood"},
}

FITS, CONFLICTS, INCOMPLETE = "fits", "conflicts", "incomplete"


@dataclass(frozen=True)
class Profile:
    """One person's dietary needs: allergens to avoid, required diets, and nutrition goals."""

    avoid: frozenset[str] = frozenset()  # allergen keys
    diets: frozenset[str] = frozenset()  # diet keys, all required
    min_protein_g: float | None = None
    max_calories: float | None = None
    max_sodium_mg: float | None = None


@dataclass
class Result:
    """One item's verdict for one profile (fits, conflicts, or incomplete), with reasons."""

    verdict: str
    reasons: list[str] = field(
        default_factory=list
    )  # why it isn't "fits"; empty when it is


def _num(value: float) -> str:
    return f"{value:g}"


def check(item, profile: Profile) -> Result:
    """One item against one profile.

    item is anything with .allergens, .diets, .unrecognized_traits (lists) and
    .nutrition (None, or something with .protein_g, .calories, .sodium_mg).
    """
    conflicts: list[str] = []
    incomplete: list[str] = []
    allergens = set(item.allergens)
    label = item.nutrition

    if profile.avoid:
        found = sorted(profile.avoid & allergens)
        conflicts += [f"contains {a}" for a in found]
        if not found:
            incomplete += [
                f"unrecognized trait {t!r}: can't rule out an allergen"
                for t in item.unrecognized_traits
            ]
            if label is None:
                incomplete.append("no nutrition label: allergens come from icons only")

    for diet in sorted(profile.diets):
        if DIET_SATISFIED_BY[diet] & set(item.diets):
            continue
        ruled_out = sorted(DIET_EXCLUDES[diet] & allergens)
        if ruled_out:
            conflicts.append(f"not {diet}: contains {', '.join(ruled_out)}")
        else:
            incomplete.append(f"not labeled {diet}")

    goals = [
        ("protein", "g", profile.min_protein_g, "protein_g", "below"),
        ("calories", "", profile.max_calories, "calories", "above"),
        ("sodium", "mg", profile.max_sodium_mg, "sodium_mg", "above"),
    ]
    for name, unit, limit, column, bad_side in goals:
        if limit is None:
            continue
        value = getattr(label, column) if label is not None else None
        if value is None:
            incomplete.append(
                f"{name} not published"
                if label is not None
                else f"no nutrition label: can't check {name}"
            )
        elif (value < limit) if bad_side == "below" else (value > limit):
            conflicts.append(
                f"{name} {_num(value)}{unit} {bad_side} {_num(limit)}{unit}"
            )

    if conflicts:
        return Result(CONFLICTS, conflicts + incomplete)
    if incomplete:
        return Result(INCOMPLETE, incomplete)
    return Result(FITS)


@dataclass
class Counts:
    """How many items fit, are incomplete, or conflict for one profile."""

    fits: int = 0
    incomplete: int = 0
    conflicts: int = 0


def count(items, profile: Profile) -> Counts:
    """How many of a location's items fit, conflict, or are incomplete for one profile."""
    counts = Counts()
    for item in items:
        verdict = check(item, profile).verdict
        setattr(counts, verdict, getattr(counts, verdict) + 1)
    return counts
