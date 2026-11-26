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
    a placeholder label (a prepared food per 1 gram, or a   incomplete
      dish of the day with no ingredients), or NC State
      flags that nutrient as incomplete
    outside the limit                                       conflicts

Overall: any conflict -> conflicts, else any incomplete -> incomplete, else fits.
"""

import re
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

# Ingredient-flag keys (ingestion/ingredients.py) that cast doubt on a diet tag.
# A flag is only a possibility, so it makes a result incomplete, never conflicts.
DIET_DOUBTED_BY = {
    "halal": {"pork"},
    "vegan": {"meat", "pork", "seafood", "dairy", "egg", "honey"},
    "vegetarian": {"meat", "pork", "seafood"},
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


_PER_GRAM = re.compile(r"\(\s*1\s*g\s*\)", re.I)
_OF_THE_DAY = re.compile(r"\b(du jour|of the day)\b", re.I)


def is_placeholder(label, name: str = "") -> bool:
    """A label whose numbers can't be used for goals.

    - A prepared food listed per 1 gram ("Gram (1g)": a bagel at 0 calories).
      A plain item per gram (black pepper, lettuce: one ingredient or none)
      really is about zero, so it's left alone.
    - A dish of the day ("Soup Du Jour") with no ingredients listed: the recipe
      changes daily, so its label is a stand-in.
    Small vegetable portions that read all zeros are real and left alone.
    """
    ingredients = getattr(label, "ingredients", None) or ""
    if _OF_THE_DAY.search(name) and not ingredients.strip():
        return True
    if not _PER_GRAM.search(getattr(label, "serving_size", None) or ""):
        return False
    return "," in ingredients


def nutrition_unavailable(label, name: str = "") -> bool:
    """Whether to show an item's label as "nutrition info unavailable" instead of its numbers.

    True for a placeholder label, or one whose calories NC State itself flags
    as incomplete. Other flagged nutrients (often just protein) leave the rest
    of the label usable, so they don't hide it.
    """
    if label is None:
        return False
    flagged = getattr(label, "missing_fields", None) or []
    return is_placeholder(label, name) or "Calories" in flagged


def check(item, profile: Profile) -> Result:
    """One item against one profile.

    item is anything with .allergens, .diets, .unrecognized_traits (lists) and
    .nutrition (None, or something with .protein_g, .calories, .sodium_mg and
    optionally .ingredient_flags, e.g. {"dairy": ["whey"]}).
    """
    conflicts: list[str] = []
    incomplete: list[str] = []
    allergens = set(item.allergens)
    label = item.nutrition
    flags = (getattr(label, "ingredient_flags", None) or {}) if label else {}

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
            incomplete += [
                f"ingredients mention {', '.join(flags[a])}: may contain {a}"
                for a in sorted(profile.avoid & set(flags))
            ]

    for diet in sorted(profile.diets):
        if DIET_SATISFIED_BY[diet] & set(item.diets):
            doubted = sorted(DIET_DOUBTED_BY[diet] & set(flags))
            if doubted:
                words = sorted({w for k in doubted for w in flags[k]})
                incomplete.append(
                    f"tagged {diet}, but ingredients mention {', '.join(words)}"
                )
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
    placeholder = label is not None and is_placeholder(label, getattr(item, "name", ""))
    flagged = set(getattr(label, "missing_fields", None) or []) if label else set()
    for name, unit, limit, column, bad_side in goals:
        if limit is None:
            continue
        value = getattr(label, column) if label is not None else None
        # NC State's own label flags this nutrient as incomplete, or the whole
        # label is a placeholder: its number can't be trusted.
        if placeholder or name.capitalize() in flagged:
            if "nutrition info unavailable" not in incomplete:
                incomplete.append("nutrition info unavailable")
        elif value is None:
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
