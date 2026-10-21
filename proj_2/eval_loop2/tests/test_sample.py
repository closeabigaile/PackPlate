"""Loop 2's sample sheet, on a tiny hand-made snapshot."""

from app.services.label_reviews import dish_name, ingredients_hash
from eval_loop2 import sample
from eval_loop2.profiles import TEST_PROFILES
from eval_loop2.sample import COLUMNS, draw, fits_answers
from eval_loop2.snapshot import approved_reviews, verdict

PASTA = "Pasta (Durum Wheat Semolina), Olive Oil, Salt"


def label(ingredients=PASTA, flags=None):
    return {"calories": 200.0, "protein_g": 7.0, "sodium_mg": 10.0, "contains": [],
            "ingredients": ingredients, "ingredient_flags": flags or {},
            "missing_fields": [], "serving_size": "1 cup"}  # fmt: skip


def item(id, label_key="k", name="Pasta", diets=(), allergens=()):
    return {"id": id, "name": name, "course": "Pasta", "icons": [],
            "allergens": list(allergens), "diets": list(diets),
            "unrecognized_traits": [], "label": label_key}  # fmt: skip


def snapshot(items, labels, reviews=()):
    return {"locations": [{"id": 1, "name": "Fountain"}],
            "menus": [{"id": 1, "location_id": 1, "date": "2026-10-20",
                       "meal": "Lunch", "items": list(items)}],
            "labels": labels, "reviews": list(reviews)}  # fmt: skip


def answers(snap):
    return fits_answers(snap)[0]


def keys(snap):
    return {(a["label_key"], a["profile_key"]) for a in answers(snap)}


def test_profiles_match_loop_1():
    assert len(TEST_PROFILES) == 11
    assert set(sample.PROFILE_WORDS) == set(TEST_PROFILES)


def test_only_fits_answers_can_be_drawn():
    snap = snapshot([item(1, allergens=["gluten"])], {"k": label()})
    assert ("k", "avoid_gluten") not in keys(snap)  # conflicts
    assert ("k", "avoid_dairy") in keys(snap)


def test_ingredient_flags_are_used_like_the_api():
    snap = snapshot([item(1)], {"k": label(PASTA + ", Whey", {"dairy": ["whey"]})})
    assert ("k", "avoid_dairy") not in keys(snap)  # flagged: incomplete, not fits


def test_approved_reviews_are_applied_like_the_api():
    review = {"location_id": 1, "dish": dish_name("Pasta"),
              "ingredients_hash": ingredients_hash(PASTA), "tags": ["vegan"],
              "reason": "test"}  # fmt: skip
    plain = snapshot([item(1, diets=["vegan"])], {"k": label()})
    reviewed = snapshot([item(1, diets=["vegan"])], {"k": label()}, [review])
    assert ("k", "diet_vegan") in keys(plain)
    assert ("k", "diet_vegan") not in keys(reviewed)
    approved = approved_reviews(reviewed)
    profile = TEST_PROFILES["diet_vegan"]
    assert verdict(item(1, diets=["vegan"]), 1, reviewed, approved, profile) != "fits"


def test_one_answer_per_recipe_and_profile():
    snap = snapshot([item(1), item(2)], {"k": label()})
    pairs = [(a["label_key"], a["profile_key"]) for a in answers(snap)]
    assert len(pairs) == len(set(pairs))


def test_dishes_without_ingredients_are_left_out_and_counted():
    snap = snapshot([item(1, "a"), item(2, "b")], {"a": label(), "b": label("  ")})
    found, unscannable = fits_answers(snap)
    assert {a["label_key"] for a in found} == {"a"}
    assert unscannable > 0


def test_draw_is_fixed_by_the_seed_and_sized_50():
    pool = [{"label_key": f"k{i}", "profile_key": "avoid_dairy", "item": f"d{i}"}
            for i in range(200)]  # fmt: skip
    a, b = draw(pool), draw(pool)
    assert a == b and len(a) == 50
    assert [r["row"] for r in a] == list(range(1, 51))
    assert draw(pool, seed=2027) != a


def test_draw_takes_everything_if_there_are_fewer_than_50():
    pool = [{"label_key": "k", "profile_key": "avoid_dairy", "item": "d"}]
    assert len(draw(pool)) == 1


def test_sheet_hides_packplates_flags_and_reasons():
    assert "verdict" not in COLUMNS and "reasons" not in COLUMNS
    assert not any("flag" in c or "icon" in c or "allergen" in c for c in COLUMNS)


def test_sheet_is_not_overwritten(tmp_path, monkeypatch, capsys):
    filled = tmp_path / "sample.csv"
    filled.write_text("row,decision\n1,ok\n", encoding="utf-8")
    monkeypatch.setattr(sample, "SHEET", filled)
    assert sample.main() == 1
    assert filled.read_text(encoding="utf-8") == "row,decision\n1,ok\n"


def test_seed_and_size_are_the_pre_registered_ones():
    assert sample.SEED == 2026  # fixed in #26
    assert sample.SAMPLE_SIZE == 50
