"""Building the spot-check sheet from a tiny hand-made snapshot."""

from eval.profiles import TEST_PROFILES
from eval.snapshot import packplate_item, verdicts
from eval.spot_check import candidates, context, sheet


def snapshot(*items, labels=None):
    return {
        "locations": [{"id": 1, "name": "Fountain"}],
        "menus": [{"id": 1, "location_id": 1, "items": list(items)}],
        "labels": labels or {},
    }


def item(id, label, icons=(), allergens=(), diets=(), unknown=()):
    return {
        "id": id,
        "name": f"dish {id}",
        "label": label,
        "icons": list(icons),
        "allergens": list(allergens),
        "diets": list(diets),
        "unrecognized_traits": list(unknown),
    }


def label(ingredients):
    return {
        "calories": 1.0,
        "protein_g": 1.0,
        "sodium_mg": 1.0,
        "contains": [],
        "ingredients": ingredients,
    }


def rows_for(snap, profile):
    return [r for r in candidates(snap) if r["profile"] == profile]


def test_packplate_item_has_what_the_engine_reads():
    it = packplate_item(item(1, "k", allergens=["soy"]), {"k": label("x")})
    assert it.allergens == ["soy"] and it.nutrition.protein_g == 1.0
    assert packplate_item(item(2, None), {}).nutrition is None


def test_both_filters_run():
    labels = {"k": label("Rice")}
    assert verdicts(item(1, "k"), labels, TEST_PROFILES["avoid_nuts"]) == (
        "fits",
        "fits",
    )
    # An "Unknown" trait: PackPlate holds back, the baseline doesn't.
    unk = item(2, "k", icons=["Unknown"], unknown=["Unknown"])
    assert verdicts(unk, labels, TEST_PROFILES["avoid_nuts"]) == (
        "incomplete",
        "fits",
    )


def test_a_fits_item_with_an_avoided_word_is_flagged():
    snap = snapshot(item(1, "k"), labels={"k": label("Pasta, Pine Nuts")})
    [row] = rows_for(snap, "avoid_nuts")
    assert row["matched"] == "nut; pine nut"
    assert row["fits_under"] == "baseline+packplate"


def test_items_that_dont_fit_are_not_scanned():
    snap = snapshot(
        item(1, "k", icons=["Contains Nuts"], allergens=["nuts"]),
        labels={"k": label("Pine Nuts")},
    )
    assert rows_for(snap, "avoid_nuts") == []


def test_baseline_only_fits_are_included_and_marked():
    snap = snapshot(
        item(1, "k", icons=["Unknown"], unknown=["Unknown"]),
        labels={"k": label("Peanuts")},
    )
    [row] = rows_for(snap, "avoid_nuts")
    assert row["fits_under"] == "baseline"


def test_same_recipe_on_many_menus_is_one_row():
    snap = snapshot(item(1, "k"), item(2, "k"), labels={"k": label("Milk")})
    [row] = rows_for(snap, "avoid_dairy")
    assert row["appearances"] == 2


def test_items_without_a_label_are_skipped():
    assert candidates(snapshot(item(1, None))) == []


def test_sheet_puts_flags_first_then_a_fixed_sample():
    rows = [
        {"label_key": f"{i}", "profile": "avoid_dairy", "matched": "milk" if i < 3
         else "", "context": "", "ingredients": "x"}
        for i in range(50)
    ]  # fmt: skip
    a = sheet(rows, sample_size=5)
    assert [r["kind"] for r in a] == ["flagged"] * 3 + ["sample"] * 5
    assert [r["row"] for r in a] == list(range(1, 9))
    assert all(r["decision"] == "" for r in a)
    assert a == sheet(rows, sample_size=5)  # same seed, same sample


def test_sample_skips_rows_without_ingredient_text():
    rows = [{"label_key": "a", "profile": "p", "matched": "", "ingredients": ""}]
    assert sheet(rows) == []


def test_flagged_rows_with_the_same_text_sit_together():
    def row(key, matched, ctx):
        return {"label_key": key, "profile": "avoid_soy", "matched": matched,
                "context": ctx, "ingredients": "x"}  # fmt: skip

    rows = [row("a", "soy", "...A..."), row("b", "flour", "...F..."),
            row("c", "soy", "...B..."), row("d", "soy", "...A...")]  # fmt: skip
    flagged = [r for r in sheet(rows) if r["kind"] == "flagged"]
    assert [r["label_key"] for r in flagged] == ["b", "a", "d", "c"]


def test_context_shows_every_occurrence_with_surrounding_text():
    text = "Cocoa Butter, Sugar, Butter (Cream, Salt)"
    assert context(text, ["butter"], width=6) == (
        "...Cocoa Butter, Suga... | ...ugar, Butter (Crea..."
    )
    assert context(text, []) == ""


def test_flagged_row_carries_its_context():
    snap = snapshot(item(1, "k"), labels={"k": label("Pasta, Pine Nuts, Oil")})
    [row] = rows_for(snap, "avoid_nuts")
    assert "Pine Nuts" in row["context"]
