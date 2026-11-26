"""Loop 2's runner on tiny hand-made data: each rule checked on its own."""

import ast
import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from app.services.filter_engine import Profile
from app.services.hours import CAMPUS_TZ
from eval_loop2 import m0
from eval_loop2.simulate import Group

NOON = datetime(2026, 10, 21, 12, 30, tzinfo=CAMPUS_TZ)
NO_DAIRY = Profile(avoid=frozenset({"dairy"}))
NO_NUTS = Profile(avoid=frozenset({"nuts"}))
ANYONE = Profile()
CONFIG = {"all_day_menus": ["Daily"]}


def label(ingredients="Rice, Salt", flags=None):
    return {"calories": 1.0, "protein_g": 1.0, "sodium_mg": 1.0, "contains": [],
            "ingredients": ingredients, "ingredient_flags": flags or {},
            "missing_fields": [], "serving_size": "1 cup"}  # fmt: skip


def item(id, label_key="k", allergens=()):
    return {"id": id, "name": f"dish {id}", "course": "x", "icons": [],
            "allergens": list(allergens), "diets": [], "unrecognized_traits": [],
            "label": label_key}  # fmt: skip


def snapshot(menus, labels, hours=None):
    return {
        "locations": [{"id": 1, "name": "Fountain"}, {"id": 2, "name": "Clark"}],
        "menus": menus,
        "labels": labels,
        "reviews": [],
        "hours": hours if hours is not None else [
            {"location_id": loc, "date": "2026-10-21", "status": "open",
             "windows": [[420, 1260]]} for loc in (1, 2)],
    }  # fmt: skip


def menu(loc, items, meal="Lunch"):
    return {"id": loc, "location_id": loc, "date": "2026-10-21", "meal": meal,
            "items": items}  # fmt: skip


def answered(monkeypatch, snap, *people):
    monkeypatch.setattr(m0, "groups", lambda config: [Group(NOON, "Lunch", people)])
    return m0.useful(snap, CONFIG)["answered"] == 1


def test_thresholds_are_the_pre_registered_ones():
    assert m0.SAFE_MAX_MISSES == 0
    assert m0.USEFUL_MIN_ANSWER_RATE == 0.80


def test_open_location_with_something_for_everyone(monkeypatch):
    snap = snapshot([menu(1, [item(1)])], {"k": label()})
    assert answered(monkeypatch, snap, ANYONE, NO_DAIRY)


def test_ingredient_flags_count_in_usefulness(monkeypatch):
    whey = {"k": label("Rice, Whey", {"dairy": ["whey"]})}
    assert not answered(monkeypatch, snapshot([menu(1, [item(1)])], whey), NO_DAIRY)


def test_closed_or_unknown_hours_do_not_count(monkeypatch):
    for status in ("closed", "unknown"):
        hours = [{"location_id": 1, "date": "2026-10-21", "status": status,
                  "windows": []}]  # fmt: skip
        snap = snapshot([menu(1, [item(1)])], {"k": label()}, hours)
        assert not answered(monkeypatch, snap, ANYONE)


def test_only_this_meal_and_all_day_menus_count(monkeypatch):
    labels = {"k": label()}
    assert not answered(monkeypatch, snapshot([menu(1, [item(1)], "Dinner")], labels),
                        ANYONE)  # fmt: skip
    assert answered(
        monkeypatch, snapshot([menu(1, [item(1)], "Daily")], labels), ANYONE
    )


def test_everyone_must_fit_at_the_same_location(monkeypatch):
    labels = {"k": label()}
    nutty = item(1, allergens=["nuts"])
    milky = item(2, allergens=["dairy"])
    split = snapshot([menu(1, [nutty]), menu(2, [milky])], labels)
    assert not answered(monkeypatch, split, NO_NUTS, NO_DAIRY)
    together = snapshot([menu(1, [nutty, milky])], labels)
    assert answered(monkeypatch, together, NO_NUTS, NO_DAIRY)


def test_a_group_counts_once_even_if_many_locations_fit(monkeypatch):
    snap = snapshot([menu(1, [item(1)]), menu(2, [item(2)])], {"k": label()})
    assert answered(monkeypatch, snap, ANYONE)  # exactly 1 answered, not 2


def row(n, decision, note=""):
    return {"row": str(n), "profile": "avoids dairy", "item": f"d{n}",
            "location": "Fountain", "decision": decision, "note": note,
            "label_key": f"k{n}", "profile_key": "avoid_dairy"}  # fmt: skip


def test_safe_counts_decisions_and_lists_misses():
    rows = [row(1, "ok"), row(2, "missed", "whey in sauce"), row(3, "unclear", "nf")]
    s = m0.safe(rows, pool_size=100, left_out=7)
    assert (s["ok"], s["missed"], s["unclear"]) == (1, 1, 1)
    assert s["missed_answers"][0]["note"] == "whey in sauce"
    assert (
        s["fits_answers_in_pool"] == 100
        and s["fits_answers_left_out_no_ingredients"] == 7
    )


def test_upper_bound_matches_the_rule_of_three():
    assert m0.upper_bound(0, 50) == pytest.approx(0.058, abs=0.002)  # about 3/50
    assert m0.upper_bound(0, 45) == pytest.approx(0.064, abs=0.002)
    assert m0.upper_bound(1, 45) > m0.upper_bound(0, 45)


def test_unclear_answers_are_left_out_of_the_bound():
    rows = [row(i, "ok") for i in range(1, 46)] + [
        row(i, "unclear") for i in range(46, 51)
    ]
    assert m0.safe(rows, 100, 0)["miss_rate_upper_bound_95"] == m0.upper_bound(0, 45)


def write_sheet(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_read_sheet_ignores_case_and_spaces(tmp_path):
    write_sheet(tmp_path / "s.csv", [row(1, " Missed ")])
    assert m0.read_sheet(tmp_path / "s.csv")[0]["decision"] == "missed"


@pytest.mark.parametrize("decision", ["", "unclar", "confirm", "reject"])
def test_read_sheet_rejects_missing_or_wrong_decisions(tmp_path, decision):
    write_sheet(tmp_path / "s.csv", [row(1, decision)])
    with pytest.raises(m0.StaleSheet):
        m0.read_sheet(tmp_path / "s.csv")


def test_stale_sheet_is_refused():
    filled = [row(1, "ok")]
    m0.check_sheet(
        filled, [{"row": 1, "label_key": "k1", "profile_key": "avoid_dairy"}]
    )
    with pytest.raises(m0.StaleSheet):
        m0.check_sheet(
            filled, [{"row": 1, "label_key": "k9", "profile_key": "avoid_dairy"}]
        )
    with pytest.raises(m0.StaleSheet):
        m0.check_sheet(filled, [])


def test_check_mode_passes_only_when_results_match(tmp_path, monkeypatch):
    monkeypatch.setattr(m0, "evaluate", lambda: {"x": 1})
    monkeypatch.setattr(m0, "render", lambda r: "")
    monkeypatch.setattr(m0, "RESULTS", tmp_path / "results.json")
    assert m0.main(["--check"]) == 1
    assert m0.main([]) == 0
    assert m0.main(["--check"]) == 0
    (tmp_path / "results.json").write_text('{"x": 2}\n', encoding="utf-8")
    assert m0.main(["--check"]) == 1


def test_simulation_is_loop_1s_with_only_the_days_changed():
    here = Path(m0.__file__).parent
    mine = json.loads((here / "simulation.json").read_text(encoding="utf-8"))
    assert mine["days"] == ["2026-10-20", "2026-10-21", "2026-10-22"]
    assert mine["seed"] == 510 and mine["groups"] == 1000
    assert mine["group_size"] == [2, 5]


def test_loop_2_never_imports_loop_1():
    here = Path(m0.__file__).parent
    for f in here.rglob("*.py"):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(n == "eval" or n.startswith("eval.") for n in names), f
