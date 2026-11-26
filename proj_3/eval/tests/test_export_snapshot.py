"""The snapshot export: what it keeps, drops, and how it orders things. No database."""

from datetime import date, datetime
from types import SimpleNamespace as Row

from eval.export_snapshot import DAYS, summary, to_snapshot

MON, TUE, WED = DAYS
SUN = date(2026, 10, 11)
FETCHED = datetime(2026, 10, 11, 18, 0)


def label(key, ingredients="water, salt"):
    return Row(
        key=key,
        calories=100.0,
        protein_g=5.0,
        sodium_mg=None,
        contains=["Milk"],
        ingredients=ingredients,
    )


def item(id, nutrition=None, **kw):
    fields = dict(
        name=f"item {id}",
        course="Grill",
        traits_raw=["Vegan"],
        allergens=[],
        diets=["vegan"],
        unrecognized_traits=[],
    )
    return Row(id=id, nutrition=nutrition, **{**fields, **kw})


def menu(id, day=MON, location_id=1, meal="Lunch", items=(), fetched_at=FETCHED):
    return Row(
        id=id,
        date=day,
        location_id=location_id,
        meal=meal,
        items=list(items),
        fetched_at=fetched_at,
    )


def hours(day, location_id=1):
    return Row(location_id=location_id, date=day, status="open", windows=[[420, 1260]])


def snap(menus=(), hrs=(), locations=()):
    return to_snapshot(list(locations), list(hrs), list(menus), DAYS)


def test_days_are_the_pre_registered_ones():
    assert DAYS == [date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)]


def test_item_keeps_only_what_the_eval_needs():
    m = menu(1, items=[item(7, allergens=["soy", "egg"])])
    out = snap([m])["menus"][0]["items"][0]
    assert out == {
        "id": 7,
        "name": "item 7",
        "course": "Grill",
        "icons": ["Vegan"],
        "allergens": ["egg", "soy"],
        "diets": ["vegan"],
        "unrecognized_traits": [],
        "label": None,
    }


def test_shared_label_is_stored_once():
    shared = label("1|soup|1 cup")
    s = snap([menu(1, items=[item(1, shared), item(2, shared)])])
    assert list(s["labels"]) == ["1|soup|1 cup"]
    assert [i["label"] for i in s["menus"][0]["items"]] == ["1|soup|1 cup"] * 2
    assert s["labels"]["1|soup|1 cup"] == {
        "calories": 100.0,
        "protein_g": 5.0,
        "sodium_mg": None,
        "contains": ["Milk"],
        "ingredients": "water, salt",
    }


def test_unscraped_menus_and_other_days_are_dropped():
    s = snap(
        [
            menu(1, items=[item(1)]),
            menu(2, fetched_at=None),  # listed, never scraped
            menu(3, day=SUN, items=[item(3)]),  # outside the days
        ]
    )
    assert [m["id"] for m in s["menus"]] == [1]


def test_hours_include_the_day_before_for_past_midnight():
    s = snap(hrs=[hours(date(2026, 10, 10)), hours(SUN), hours(WED)])
    assert [h["date"] for h in s["hours"]] == ["2026-10-11", "2026-10-14"]


def test_output_order_does_not_depend_on_input_order():
    menus = [
        menu(2, day=TUE, items=[item(5), item(4)]),
        menu(1, day=MON, location_id=3),
        menu(3, day=MON, location_id=1),
    ]
    a = snap(menus, locations=[Row(id=2, name="B"), Row(id=1, name="A")])
    b = snap(reversed(menus), locations=[Row(id=1, name="A"), Row(id=2, name="B")])
    assert a == b
    assert [m["id"] for m in a["menus"]] == [3, 1, 2]
    assert [i["id"] for i in a["menus"][2]["items"]] == [4, 5]


def test_summary_counts():
    s = snap(
        [
            menu(1, items=[item(1, label("a")), item(2)]),
            menu(2, location_id=2, items=[item(3, label("b", ingredients=None))]),
        ]
    )
    assert summary(s) == {
        "days": ["2026-10-12", "2026-10-13", "2026-10-14"],
        "locations_with_menus": 2,
        "menus": 2,
        "items": 3,
        "items_without_label": 1,
        "labels": 2,
        "labels_without_ingredients": 1,
        "hours_rows": 0,
    }
