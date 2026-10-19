"""The icon-only baseline M0 compares PackPlate against.

It filters the way NetNutrition's own trait filter does: it reads only the
icons on the menu. Avoiding an allergen, an item is out only if it shows that
allergen's icon; no icon counts as safe, even with no nutrition label, an
"Unknown" trait, or the allergen listed only in the label's "Contains:" line.
Requiring a diet, an item fits only if it carries that diet's icon, with the
same rule as PackPlate (vegan also counts as vegetarian), so the comparison
isolates how missing allergen data is handled.

There is no "incomplete": every answer is fits or conflicts.
"""

from app.services.filter_engine import CONFLICTS, DIET_SATISFIED_BY, FITS, Profile
from ingestion.normalize import split_traits


def check(icons: list[str], profile: Profile) -> str:
    """One item, given its icon titles as published, against one profile."""
    if (
        profile.min_protein_g is not None
        or profile.max_calories is not None
        or profile.max_sodium_mg is not None
    ):
        raise ValueError("the icon-only baseline has no nutrition goals")
    allergens, diets, _unrecognized = split_traits(icons)
    if profile.avoid & allergens:
        return CONFLICTS
    for diet in profile.diets:
        if not DIET_SATISFIED_BY[diet] & diets:
            return CONFLICTS
    return FITS
