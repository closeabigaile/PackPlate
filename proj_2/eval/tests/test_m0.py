"""The M0 eval on tiny hand-made data: each rule checked on its own."""

import csv
from datetime import datetime

import pytest

from app.services.filter_engine import Profile
from app.services.hours import CAMPUS_TZ
from eval import m0
from eval.simulate import Group

NOON = datetime(2026, 10, 12, 12, 30, tzinfo=CAMPUS_TZ)
NO_NUTS = Profile(avoid=frozenset({"nuts"}))
NO_DAIRY = Profile(avoid=frozenset({"dairy"}))
ANYONE = Profile()
CONFIG = {"all_day_menus": ["Daily"]}


def item(id, icons=(), allergens=(), unknown=()):
    return {"id": id, "name": f"dish {id}", "icons": list(icons),
            "allergens": list(allergens), "diets": [],
            "unrecognized_traits": list(unknown), "label": "k"}  # fmt: skip


def snapshot(menus, hours=None):
    return {
        "labels": {"k": {"calories": 1.0, "protein_g": 1.0, "sodium_mg": 1.0,
                         "contains": [], "ingredients": "x"}},  # fmt: skip
        "menus": menus,
        "hours": hours
        if hours is not None
        else [{"location_id": loc, "date": "2026-10-12", "status": "open",
               "windows": [[420, 1260]]} for loc in (1, 2)],  # fmt: skip
    }


def menu(loc, items, meal="Lunch"):
    return {"location_id": loc, "date": "2026-10-12", "meal": meal, "items": items}


def answered(monkeypatch, snap, *people, which="packplate"):
    monkeypatch.setattr(m0, "groups", lambda config: [Group(NOON, "Lunch", people)])
    return m0.useful(snap, CONFIG)[which]["answered"] == 1


def test_open_location_with_something_for_everyone(monkeypatch):
    assert answered(monkeypatch, snapshot([menu(1, [item(1)])]), ANYONE, NO_NUTS)


def test_nothing_fits_one_person(monkeypatch):
    nutty = item(1, icons=["Contains Nuts"], allergens=["nuts"])
    assert not answered(monkeypatch, snapshot([menu(1, [nutty])]), ANYONE, NO_NUTS)


def test_closed_location_does_not_count(monkeypatch):
    closed = [
        {"location_id": 1, "date": "2026-10-12", "status": "closed", "windows": []}
    ]
    assert not answered(monkeypatch, snapshot([menu(1, [item(1)])], closed), ANYONE)


def test_unknown_hours_count_as_closed(monkeypatch):
    unknown = [{"location_id": 1, "date": "2026-10-12", "status": "unknown",
                "windows": []}]  # fmt: skip
    assert not answered(monkeypatch, snapshot([menu(1, [item(1)])], unknown), ANYONE)
    assert not answered(monkeypatch, snapshot([menu(1, [item(1)])], []), ANYONE)


def test_outside_opening_hours_does_not_count(monkeypatch):
    morning = [{"location_id": 1, "date": "2026-10-12", "status": "open",
                "windows": [[420, 660]]}]  # 7-11am  # fmt: skip
    assert not answered(monkeypatch, snapshot([menu(1, [item(1)])], morning), ANYONE)


def test_only_this_meal_and_all_day_menus_count(monkeypatch):
    assert not answered(monkeypatch, snapshot([menu(1, [item(1)], "Dinner")]), ANYONE)
    assert answered(monkeypatch, snapshot([menu(1, [item(1)], "Daily")]), ANYONE)


def test_everyone_must_fit_at_the_same_location(monkeypatch):
    nutty = item(1, icons=["Contains Nuts"], allergens=["nuts"])
    milky = item(2, icons=["Contains Dairy"], allergens=["dairy"])
    split = snapshot([menu(1, [nutty]), menu(2, [milky])])
    # Location 1 only suits the dairy-free person, location 2 only the nut-free one.
    assert not answered(monkeypatch, split, NO_NUTS, NO_DAIRY)
    both = snapshot([menu(1, [nutty, milky])])
    assert answered(monkeypatch, both, NO_NUTS, NO_DAIRY)


def test_unknown_trait_answers_the_baseline_but_not_packplate(monkeypatch):
    snap = snapshot([menu(1, [item(1, icons=["Unknown"], unknown=["Unknown"])])])
    assert answered(monkeypatch, snap, NO_NUTS, which="baseline")
    assert not answered(monkeypatch, snap, NO_NUTS, which="packplate")


def test_answer_rate_with_restrictions_only_counts_restricted_groups(monkeypatch):
    gs = [Group(NOON, "Lunch", (ANYONE, ANYONE)), Group(NOON, "Lunch", (NO_NUTS,))]
    monkeypatch.setattr(m0, "groups", lambda config: gs)
    nutty = item(1, icons=["Contains Nuts"], allergens=["nuts"])
    u = m0.useful(snapshot([menu(1, [nutty])]), CONFIG)
    assert u["groups_with_restrictions"] == 1
    assert u["packplate"]["answer_rate"] == 0.5
    assert u["packplate"]["answer_rate_with_restrictions"] == 0.0


def sheet_row(row, kind, decision, under="baseline+packplate", appearances=1):
    return {"row": str(row), "kind": kind, "profile": "avoid_nuts", "item": "x",
            "location": "y", "fits_under": under, "appearances": str(appearances),
            "matched": "nut" if kind == "flagged" else "", "decision": decision,
            "note": "", "label_key": f"k{row}", "ingredients": "x"}  # fmt: skip


def test_safe_counts_confirmed_flags_per_filter():
    rows = [
        sheet_row(1, "flagged", "confirm", appearances=3),
        sheet_row(2, "flagged", "confirm", under="baseline"),
        sheet_row(3, "flagged", "reject"),
        sheet_row(4, "sample", "missed"),
        sheet_row(5, "sample", "ok"),
    ]
    pairs = [{"fits_under": "baseline+packplate", "ingredients": "x"},
             {"fits_under": "baseline", "ingredients": ""}]  # fmt: skip
    s = m0.safe(rows, pairs)
    assert s["packplate"]["confirmed_false_fits"] == 1
    assert s["packplate"]["menu_items_affected"] == 3
    assert s["baseline"]["confirmed_false_fits"] == 2
    assert s["baseline"]["fits_answers_without_ingredients"] == 1
    assert s["scan"] == {"flags": 3, "flags_confirmed": 2,
                         "random_unflagged_checked": 2, "random_unflagged_missed": 1}  # fmt: skip


def write_sheet(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_read_sheet_ignores_case_and_spaces(tmp_path):
    write_sheet(tmp_path / "s.csv", [sheet_row(1, "flagged", " Confirm ")])
    assert m0.read_sheet(tmp_path / "s.csv")[0]["decision"] == "confirm"


@pytest.mark.parametrize("kind,decision", [("flagged", ""), ("flagged", "ok"),
                                           ("sample", "confirm"), ("sample", "yes")])  # fmt: skip
def test_read_sheet_rejects_missing_or_wrong_decisions(tmp_path, kind, decision):
    write_sheet(tmp_path / "s.csv", [sheet_row(1, kind, decision)])
    with pytest.raises(m0.StaleSheet):
        m0.read_sheet(tmp_path / "s.csv")


def test_stale_sheet_is_refused():
    filled = [sheet_row(1, "flagged", "confirm")]
    m0.check_sheet(filled, [dict(filled[0], row=1)])  # same rows: fine
    with pytest.raises(m0.StaleSheet):
        m0.check_sheet(filled, [dict(filled[0], matched="peanut")])
    with pytest.raises(m0.StaleSheet):
        m0.check_sheet(filled, [])


RESULT = {"x": 1}


def test_check_mode_passes_only_when_results_match(tmp_path, monkeypatch):
    monkeypatch.setattr(m0, "evaluate", lambda: RESULT)
    monkeypatch.setattr(m0, "render", lambda r: "")
    monkeypatch.setattr(m0, "RESULTS", tmp_path / "results.json")
    assert m0.main(["--check"]) == 1  # no results file yet
    assert m0.main([]) == 0  # writes it
    assert m0.main(["--check"]) == 0
    (tmp_path / "results.json").write_text('{"x": 2}\n', encoding="utf-8")
    assert m0.main(["--check"]) == 1


def test_stale_sheet_exits_with_an_error(monkeypatch, capsys):
    def stale():
        raise m0.StaleSheet("drifted")

    monkeypatch.setattr(m0, "evaluate", stale)
    assert m0.main([]) == 1
    assert "drifted" in capsys.readouterr().err
