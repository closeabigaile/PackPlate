"""Loop 2's snapshot export: what it keeps, drops, and refuses. No database."""

from datetime import date, datetime
from types import SimpleNamespace as Row

from eval_loop2 import export_snapshot
from eval_loop2.export_snapshot import DAYS, summary, to_snapshot

TUE, WED, THU = DAYS
FETCHED = datetime(2026, 10, 20, 0, 41)


def label(key, flags=None, missing=None, ingredients="Pancake Mix (Wheat, Whey)"):
    return Row(
        key=key,
        calories=100.0,
        protein_g=5.0,
        sodium_mg=None,
        contains=[],
        ingredients=ingredients,
        ingredient_flags=flags,
        missing_fields=missing,
        serving_size="1 each",
    )


def item(id, nutrition=None, **kw):
    fields = dict(name=f"item {id}", course="Grill", traits_raw=["Vegan"],
                  allergens=[], diets=["vegan"], unrecognized_traits=[])  # fmt: skip
    return Row(id=id, nutrition=nutrition, **{**fields, **kw})


def menu(id, day=TUE, location_id=1, items=(), fetched_at=FETCHED):
    return Row(id=id, date=day, location_id=location_id, meal="Lunch",
               items=list(items), fetched_at=fetched_at)  # fmt: skip


def review(location_id, dish, tags):
    return Row(location_id=location_id, dish=dish, ingredients_hash="abc",
               tags=tags, reason="ingredients list chicken")  # fmt: skip


def snap(menus=(), reviews=()):
    return to_snapshot([], [], list(menus), list(reviews), DAYS)


def test_days_are_the_pre_registered_ones():
    assert DAYS == [date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22)]


def test_labels_keep_every_field_todays_filter_reads():
    s = snap([menu(1, items=[item(1, label("k", {"dairy": ["whey"]}, ["Protein"]))])])
    assert s["labels"]["k"] == {
        "calories": 100.0,
        "protein_g": 5.0,
        "sodium_mg": None,
        "contains": [],
        "ingredients": "Pancake Mix (Wheat, Whey)",
        "ingredient_flags": {"dairy": ["whey"]},
        "missing_fields": ["Protein"],
        "serving_size": "1 each",
    }


def test_unset_flags_count_as_none_found():
    s = snap([menu(1, items=[item(1, label("k", None, None))])])
    assert s["labels"]["k"]["ingredient_flags"] == {}
    assert s["labels"]["k"]["missing_fields"] == []


def test_items_keep_their_name_for_reviews():
    s = snap([menu(1, items=[item(7, label("k"), name="Broccoli Cheese")])])
    assert s["menus"][0]["items"][0]["name"] == "Broccoli Cheese"


def test_unscraped_menus_and_other_days_are_dropped():
    s = snap([menu(1, items=[item(1)]), menu(2, fetched_at=None),
              menu(3, day=date(2026, 10, 19), items=[item(3)])])  # fmt: skip
    assert [m["id"] for m in s["menus"]] == [1]


def test_approved_reviews_are_kept_sorted():
    s = snap(reviews=[review(2, "b soup", ["vegan"]),
                      review(1, "a soup", ["vegetarian", "vegan"])])  # fmt: skip
    assert [r["dish"] for r in s["reviews"]] == ["a soup", "b soup"]
    assert s["reviews"][0]["tags"] == ["vegan", "vegetarian"]


def test_summary_counts_flags_and_reviews():
    s = snap(
        [
            menu(
                1, items=[item(1, label("a", {"dairy": ["whey"]})), item(2, label("b"))]
            )
        ],
        [review(1, "x", ["vegan"])],
    )
    out = summary(s)
    assert out["labels_with_ingredient_flags"] == 1
    assert out["approved_reviews"] == 1


def test_export_refuses_to_overwrite_the_frozen_snapshot(tmp_path, monkeypatch, capsys):
    frozen = tmp_path / "snapshot.json"
    frozen.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(export_snapshot, "OUT", frozen)
    assert export_snapshot.main() == 1
    assert "isn't overwritten" in capsys.readouterr().err
    assert frozen.read_text(encoding="utf-8") == "{}"
