"""Label reviews: find diet tags that an item's own ingredients contradict (#18).

After each scrape, every item tagged vegan, vegetarian, or halal is checked
against its label's ingredients. A contradiction becomes a `pending` row in
label_reviews for a person to approve or reject. One row per dish and
ingredient text: a repeat scrape adds nothing, and new ingredient text needs a
new decision.

The diet rules follow the sources in ingestion/ingredients.py (Vegetarian
Society, Vegan Society; pork for halal) and match DIET_DOUBTED_BY in
backend/app/services/filter_engine.py.
"""

import hashlib
import re
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import LabelReview, Menu, MenuItem, Nutrition
from ingestion.ingredients import matched_terms

DIET_RULED_OUT_BY = {
    "halal": {"pork"},
    "vegan": {"meat", "pork", "seafood", "dairy", "egg", "honey"},
    "vegetarian": {"meat", "pork", "seafood"},
}


def dish_name(name: str) -> str:
    """How a dish is matched across menus: its name, lowercased, spaces collapsed."""
    return re.sub(r"\s+", " ", name).strip().casefold()


def ingredients_hash(ingredients: str | None) -> str:
    """Fingerprint of the ingredient text a decision is made on (sha256 hex)."""
    return hashlib.sha256((ingredients or "").encode("utf-8")).hexdigest()


def contradictions(diets: list[str], ingredients: str | None) -> dict[str, list[str]]:
    """Diet tags the ingredients contradict, with the words why: {"vegan": ["chicken"]}."""
    flags = matched_terms(ingredients)
    out = {}
    for diet in sorted(set(diets) & set(DIET_RULED_OUT_BY)):
        words = sorted(
            {w for k in DIET_RULED_OUT_BY[diet] & set(flags) for w in flags[k]}
        )
        if words:
            out[diet] = words
    return out


def record(db: Session, start: date, end: date, now: datetime) -> tuple[int, int]:
    """Add pending reviews for contradicted items on scraped menus from start to end.

    Returns (new reviews added, reviews pending in total). The caller commits.
    """
    query = (
        select(Menu.location_id, MenuItem.name, MenuItem.diets, Nutrition.ingredients)
        .join(MenuItem, MenuItem.menu_id == Menu.id)
        .join(Nutrition, Nutrition.key == MenuItem.nutrition_key)
        .where(Menu.date.between(start, end), Menu.fetched_at.is_not(None))
    )
    new = 0
    seen = set()
    for location_id, name, diets, ingredients in db.execute(query):
        found = contradictions(diets, ingredients)
        key = (location_id, dish_name(name), ingredients_hash(ingredients))
        if not found or key in seen:
            continue
        seen.add(key)
        result = db.execute(
            insert(LabelReview)
            .values(
                location_id=location_id,
                dish=key[1],
                item_name=name,
                tags=sorted(found),
                words=sorted({w for ws in found.values() for w in ws}),
                ingredients_hash=key[2],
                status="pending",
                first_seen_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=["location_id", "dish", "ingredients_hash"]
            )
            .returning(LabelReview.id)
        )
        new += result.first() is not None  # no row back = already reviewed
    pending = db.scalar(
        select(func.count())
        .select_from(LabelReview)
        .where(LabelReview.status == "pending")
    )
    return new, pending
