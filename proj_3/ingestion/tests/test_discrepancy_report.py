from datetime import UTC, date, datetime

from db.models import Location, Menu, MenuItem, Nutrition
from ingestion.discrepancy_report import rows

DAY = date(2026, 10, 20)
SAVED = datetime(2026, 10, 19, tzinfo=UTC)


def add_item(db, item_id, name, ingredients, allergens=(), diets=()):
    key = f"1|{name.lower()}|1 each"
    db.add(
        Nutrition(
            key=key,
            location_id=1,
            source_detail_oid=item_id,
            ingredients=ingredients,
            nutrients_raw={},
            contains=[],
            missing_fields=[],
            ingredient_flags={},
            fetched_at=SAVED,
        )
    )
    db.flush()
    db.add(
        MenuItem(
            menu_id=10,
            detail_oid=item_id,
            name=name,
            allergens=list(allergens),
            diets=list(diets),
            traits_raw=[],
            unrecognized_traits=[],
            nutrition_key=key,
        )
    )


def setup(db):
    db.add(Location(id=1, name="Fountain Dining Hall", updated_at=SAVED))
    db.add(Menu(id=10, location_id=1, date=DAY, meal="Breakfast", fetched_at=SAVED))
    db.flush()


def test_report_lists_allergens_and_diet_tags_the_label_leaves_out(db):
    setup(db)
    add_item(db, 1, "Blueberry Pancake", "Flour, Whey", allergens=["gluten"])
    add_item(db, 2, "Broccoli Cheese", "Broccoli, Chicken Fat", diets=["vegetarian"])
    add_item(db, 3, "Toast", "Wheat Flour", allergens=["gluten"])  # label agrees
    db.commit()

    report = rows(db, DAY, DAY)
    assert [(r["item"], r["issue"], r["words"]) for r in report] == [
        ("Blueberry Pancake", "may contain dairy", "whey"),
        ("Broccoli Cheese", "tagged vegetarian", "chicken"),
    ]
    assert report[0]["location"] == "Fountain Dining Hall"
    assert report[0]["nc_state_allergens"] == "gluten"


def test_report_ignores_menus_outside_the_dates(db):
    setup(db)
    add_item(db, 1, "Blueberry Pancake", "Flour, Whey", allergens=["gluten"])
    db.commit()
    assert rows(db, date(2026, 10, 21), date(2026, 10, 27)) == []
