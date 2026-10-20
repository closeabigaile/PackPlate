"""Export loop 2's frozen snapshot from the database.

The days are fixed in #26: Tue Oct 20, Wed Oct 21, and Thu Oct 22, 2026, the
first three weekdays after #17 merged. Run once, from proj_2/, with
DATABASE_URL set:

    python -m eval_loop2.export_snapshot

It only reads, and it won't overwrite the snapshot once it exists. Loop 2 tests
PackPlate as students get it, so besides menus and hours it keeps every label
field the filter reads (ingredient flags as stored, missing nutrients, serving
size) and the approved label reviews the API applies.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.models import HoursDay, LabelReview, Location, Menu, MenuItem
from db.session import make_engine, make_session_factory

DAYS = [date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22)]
OUT = Path(__file__).parent / "data" / "snapshot.json"


def to_snapshot(locations, hours, menus, reviews, days) -> dict:
    """Plain, sorted data from database rows (or anything with the same fields).

    Labels are stored once and items point to them by key. Menus that were
    listed but never scraped (no items) are left out. Hours include the day
    before the first day, because late hours can run past midnight.
    """
    labels = {}
    out_menus = []
    for menu in sorted(menus, key=lambda m: (m.date, m.location_id, m.meal, m.id)):
        if menu.fetched_at is None or menu.date not in days:
            continue
        items = []
        for item in sorted(menu.items, key=lambda i: i.id):
            label = item.nutrition
            if label is not None:
                labels[label.key] = {
                    "calories": label.calories,
                    "protein_g": label.protein_g,
                    "sodium_mg": label.sodium_mg,
                    "contains": list(label.contains),
                    "ingredients": label.ingredients,
                    "ingredient_flags": {
                        k: list(v)
                        for k, v in sorted((label.ingredient_flags or {}).items())
                    },
                    "missing_fields": list(label.missing_fields or []),
                    "serving_size": label.serving_size,
                }
            items.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "course": item.course,
                    "icons": list(item.traits_raw),
                    "allergens": sorted(item.allergens),
                    "diets": sorted(item.diets),
                    "unrecognized_traits": sorted(item.unrecognized_traits),
                    "label": label.key if label is not None else None,
                }
            )
        out_menus.append(
            {
                "id": menu.id,
                "location_id": menu.location_id,
                "date": menu.date.isoformat(),
                "meal": menu.meal,
                "items": items,
            }
        )

    first_hours_day = days[0] - timedelta(days=1)
    return {
        "days": [d.isoformat() for d in days],
        "locations": [
            {"id": loc.id, "name": loc.name}
            for loc in sorted(locations, key=lambda loc: loc.id)
        ],
        "hours": [
            {
                "location_id": h.location_id,
                "date": h.date.isoformat(),
                "status": h.status,
                "windows": h.windows,
            }
            for h in sorted(hours, key=lambda h: (h.date, h.location_id))
            if first_hours_day <= h.date <= days[-1]
        ],
        "menus": out_menus,
        "labels": dict(sorted(labels.items())),
        "reviews": sorted(
            (
                {
                    "location_id": r.location_id,
                    "dish": r.dish,
                    "ingredients_hash": r.ingredients_hash,
                    "tags": sorted(r.tags),
                    "reason": r.reason or "",
                }
                for r in reviews
            ),
            key=lambda r: (r["location_id"], r["dish"], r["ingredients_hash"]),
        ),
    }


def summary(snapshot: dict) -> dict:
    """Counts worth eyeballing after an export."""
    items = [i for m in snapshot["menus"] for i in m["items"]]
    labels = snapshot["labels"].values()
    return {
        "days": snapshot["days"],
        "locations_with_menus": len({m["location_id"] for m in snapshot["menus"]}),
        "menus": len(snapshot["menus"]),
        "items": len(items),
        "items_without_label": sum(1 for i in items if i["label"] is None),
        "labels": len(snapshot["labels"]),
        "labels_without_ingredients": sum(1 for lb in labels if not lb["ingredients"]),
        "labels_with_ingredient_flags": sum(
            1 for lb in labels if lb["ingredient_flags"]
        ),
        "approved_reviews": len(snapshot["reviews"]),
        "hours_rows": len(snapshot["hours"]),
    }


def main() -> int:
    """Read loop 2's days from the database and write its snapshot, unless it exists."""
    if OUT.exists():
        print(f"{OUT} already exists; it's frozen, so it isn't overwritten.",
              file=sys.stderr)  # fmt: skip
        return 1
    engine = make_engine()
    with make_session_factory(engine)() as db:
        locations = db.scalars(select(Location)).all()
        hours = db.scalars(
            select(HoursDay).where(
                HoursDay.date.between(DAYS[0] - timedelta(days=1), DAYS[-1])
            )
        ).all()
        menus = db.scalars(
            select(Menu)
            .where(Menu.date.in_(DAYS))
            .options(selectinload(Menu.items).selectinload(MenuItem.nutrition))
        ).all()
        reviews = db.scalars(
            select(LabelReview).where(LabelReview.status == "approved")
        ).all()
        snapshot = to_snapshot(locations, hours, menus, reviews, DAYS)

    OUT.parent.mkdir(exist_ok=True)
    text = json.dumps(snapshot, indent=1, sort_keys=True, ensure_ascii=False)
    OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
    for key, value in summary(snapshot).items():
        print(f"{key}: {value}")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
