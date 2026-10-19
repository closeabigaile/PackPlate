"""Discrepancy report: labels whose ingredients name an allergen NC State's label leaves out.

Read-only. One row per label (dishes share labels), for items on menus between
--start and --end, as CSV for NC State Dining to check:
- an allergen the ingredients mention that isn't in the item's allergens, or
- an item tagged vegetarian/vegan whose ingredients mention something that diet
  rules out.
A row is a possible label gap, not a confirmed one: a person should check it.

Usage (from proj_2/, with DATABASE_URL set):
    python -m ingestion.discrepancy_report --start 2026-10-19 --end 2026-10-25 > report.csv
"""

import argparse
import csv
import sys
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Location, Menu, MenuItem, Nutrition
from db.session import make_engine, make_session_factory
from ingestion.config import CAMPUS_TZ
from ingestion.ingredients import matched_terms
from ingestion.normalize import ALLERGEN_KEYS

DIET_DOUBTED_BY = {  # same rule as backend/app/services/filter_engine.py
    "vegan": {"meat", "pork", "seafood", "dairy", "egg", "honey"},
    "vegetarian": {"meat", "pork", "seafood"},
}
COLUMNS = ["location", "item", "nc_state_allergens", "nc_state_diets", "issue", "words"]


def rows(db: Session, start: date, end: date) -> list[dict]:
    query = (
        select(Location.name, MenuItem, Nutrition.key, Nutrition.ingredients)
        .join(Menu, Menu.id == MenuItem.menu_id)
        .join(Location, Location.id == Menu.location_id)
        .join(Nutrition, Nutrition.key == MenuItem.nutrition_key)
        .where(Menu.date.between(start, end))
        .order_by(Location.name, MenuItem.name)
    )
    out, seen = [], set()
    for location, item, key, ingredients in db.execute(query):
        if key in seen:
            continue
        seen.add(key)
        flags = matched_terms(ingredients)
        issues = []
        for allergen in sorted(set(flags) & set(ALLERGEN_KEYS) - set(item.allergens)):
            issues.append((f"may contain {allergen}", flags[allergen]))
        for diet in sorted(set(item.diets) & set(DIET_DOUBTED_BY)):
            doubted = sorted(DIET_DOUBTED_BY[diet] & set(flags))
            if doubted:
                words = sorted({w for k in doubted for w in flags[k]})
                issues.append((f"tagged {diet}", words))
        for issue, words in issues:
            out.append(
                {
                    "location": location,
                    "item": item.name,
                    "nc_state_allergens": ", ".join(item.allergens),
                    "nc_state_diets": ", ".join(item.diets),
                    "issue": issue,
                    "words": ", ".join(words),
                }
            )
    return out


def main(argv: list[str] | None = None) -> int:
    today = datetime.now(CAMPUS_TZ).date()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--start", type=date.fromisoformat, default=today)
    p.add_argument("--end", type=date.fromisoformat, default=today + timedelta(days=6))
    a = p.parse_args(argv)
    try:
        db = make_session_factory(make_engine())()
    except RuntimeError as e:
        print(f"not started: {e}", file=sys.stderr)
        return 2
    report = rows(db, a.start, a.end)
    db.close()
    writer = csv.DictWriter(sys.stdout, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(report)
    print(f"{len(report)} possible label gaps", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
