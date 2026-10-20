"""Apply approved label reviews (#18): remove diet tags a person confirmed are contradicted.

NC State's data in the database is never changed. Each menu item is returned as
a view with the approved tags taken out of `diets` and the reasons in
`diets_removed`, e.g. {"vegan": "ingredients list chicken"}. A decision only
applies to the exact ingredient text it was made on, so if NC State changes the
ingredients, the tags come back until someone reviews the new text.

dish_name and ingredients_hash must match ingestion/label_reviews.py (a test
checks this).
"""

import hashlib
import re
from types import SimpleNamespace

Approved = dict[tuple[int, str, str], tuple[list[str], str]]


def dish_name(name: str) -> str:
    """How a dish is matched across menus: its name, lowercased, spaces collapsed."""
    return re.sub(r"\s+", " ", name).strip().casefold()


def ingredients_hash(ingredients: str | None) -> str:
    """Fingerprint of the ingredient text a decision was made on (sha256 hex)."""
    return hashlib.sha256((ingredients or "").encode("utf-8")).hexdigest()


def reviewed(item, location_id: int, approved: Approved) -> SimpleNamespace:
    """A read-only view of `item` with any approved diet tags removed."""
    label = item.nutrition
    ingredients = label.ingredients if label is not None else None
    tags, reason = approved.get(
        (location_id, dish_name(item.name), ingredients_hash(ingredients)), ([], "")
    )
    removed = {t: reason for t in item.diets if t in tags}
    return SimpleNamespace(
        id=item.id,
        name=item.name,
        course=item.course,
        serving_size=item.serving_size,
        allergens=item.allergens,
        diets=[d for d in item.diets if d not in removed],
        diets_removed=removed,
        unrecognized_traits=item.unrecognized_traits,
        nutrition=label,
    )


def reviewed_items(menu, approved: Approved) -> list[SimpleNamespace]:
    """A menu's items in id order, each with approved reviews applied."""
    return [
        reviewed(item, menu.location_id, approved)
        for item in sorted(menu.items, key=lambda i: i.id)
    ]
