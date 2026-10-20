"""Build loop 2's hand-check sheet: 50 random `fits` answers from today's PackPlate.

As pre-registered in #26: every dish x test profile on the loop 2 days is run
through today's filter; each `fits` answer (one per recipe per profile) can be
drawn; 50 are drawn with seed 2026. Dishes with no ingredient text can't be
checked, so they're left out of the draw and counted.

The sheet shows only what a person needs to judge the answer (the profile, the
dish, and its full ingredient list), not PackPlate's flags, icons, or reasons,
so the check isn't biased by them. Run once, from proj_2/:

    python -m eval_loop2.sample

It writes eval_loop2/data/sample.csv and refuses to overwrite it once it exists.
The `decision` column takes "ok", "missed" (the ingredients name something the
profile avoids), or "unclear" (the label can't tell).
"""

import csv
import random
import sys
from pathlib import Path

from app.services.filter_engine import FITS
from eval_loop2.profiles import TEST_PROFILES
from eval_loop2.snapshot import approved_reviews, load, verdict

SHEET = Path(__file__).parent / "data" / "sample.csv"
SAMPLE_SIZE = 50
SEED = 2026  # fixed in #26
COLUMNS = ["row", "profile", "item", "location", "ingredients", "decision", "note",
           "label_key", "profile_key"]  # fmt: skip

PROFILE_WORDS = {
    **{f"avoid_{a}": f"avoids {a}" for a in
       ("dairy", "egg", "gluten", "nuts", "pork", "seafood", "sesame", "soy")},
    "diet_halal": "eats halal",
    "diet_vegan": "is vegan",
    "diet_vegetarian": "is vegetarian",
}  # fmt: skip


def fits_answers(snapshot: dict) -> tuple[list[dict], int]:
    """Every `fits` answer that can be checked, one per recipe per profile.

    Returns the answers, sorted, and how many `fits` answers had no ingredient
    text (left out, since nobody can check them).
    """
    approved = approved_reviews(snapshot)
    names = {loc["id"]: loc["name"] for loc in snapshot["locations"]}
    found, unscannable = {}, set()
    for menu in snapshot["menus"]:
        for item in menu["items"]:
            for key, profile in TEST_PROFILES.items():
                if (
                    verdict(item, menu["location_id"], snapshot, approved, profile)
                    != FITS
                ):
                    continue
                label = snapshot["labels"][item["label"]] if item["label"] else None
                pair = (item["label"], key)
                if not label or not (label["ingredients"] or "").strip():
                    unscannable.add(pair)
                    continue
                found.setdefault(pair, {
                    "label_key": item["label"],
                    "profile_key": key,
                    "profile": PROFILE_WORDS[key],
                    "item": item["name"],
                    "location": names[menu["location_id"]],
                    "ingredients": label["ingredients"],
                })  # fmt: skip
    return [found[k] for k in sorted(found)], len(unscannable)


def draw(answers: list[dict], size: int = SAMPLE_SIZE, seed: int = SEED) -> list[dict]:
    """A fixed random sample, ordered by profile then dish for easier reading."""
    picked = random.Random(seed).sample(answers, min(size, len(answers)))
    order = list(TEST_PROFILES)
    picked.sort(
        key=lambda a: (order.index(a["profile_key"]), a["item"], a["label_key"])
    )
    return [{**a, "row": i, "decision": "", "note": ""}
            for i, a in enumerate(picked, 1)]  # fmt: skip


def main() -> int:
    """Write eval_loop2/data/sample.csv, unless a sheet already exists."""
    if SHEET.exists():
        print(
            f"{SHEET} already exists; delete it first to rebuild it.", file=sys.stderr
        )
        return 1
    answers, unscannable = fits_answers(load())
    rows = draw(answers)
    # utf-8-sig so Excel shows characters like "–" correctly.
    with SHEET.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"fits answers that can be checked: {len(answers)}")
    print(f"fits answers left out (no ingredient text): {unscannable}")
    print(f"drawn: {len(rows)} (seed {SEED})")
    print(f"wrote {SHEET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
