"""Export the frozen M0 snapshot from the database, trimmed to what the eval needs.

The days are fixed in the M0 pre-registration issue: the first three weekdays
of the latest full scrape. Run once, from proj_2/, with DATABASE_URL set:

    python -m eval.export_snapshot

It only reads. It writes eval/data/snapshot.json; the eval reads only that
file, never the database, so anyone can reproduce its numbers.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.models import HoursDay, Location, Menu, MenuItem
from db.session import make_engine, make_session_factory

DAYS = [date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)]
OUT = Path(__file__).parent / "data" / "snapshot.json"


def to_snapshot(locations, hours, menus, days) -> dict:
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
        "hours_rows": len(snapshot["hours"]),
    }


def main():
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
        snapshot = to_snapshot(locations, hours, menus, DAYS)

    OUT.parent.mkdir(exist_ok=True)
    text = json.dumps(snapshot, indent=1, sort_keys=True, ensure_ascii=False)
    OUT.write_text(text + "\n", encoding="utf-8")
    for key, value in summary(snapshot).items():
        print(f"{key}: {value}")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
