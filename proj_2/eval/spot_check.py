"""Build the hand spot-check sheet: every scan flag, plus 30 random unflagged items.

Run once, from proj_2/:

    python -m eval.spot_check

It writes eval/data/spot_check.csv for a person to fill in, and refuses to
overwrite a sheet that already exists, so filled-in decisions can't be lost.

One row per recipe (nutrition label) per test profile: the same dish on many
menus is read once. Only items that come out `fits` under PackPlate or the
icon-only baseline are scanned, since only those can be false fits.

The `decision` column:
- flagged rows: "confirm" (a real false fit) or "reject" (the word misfired)
- sample rows: "ok" (nothing avoided in the ingredients) or "missed" (the scan
  missed something)
"""

import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

from app.services.filter_engine import FITS
from eval.profiles import TEST_PROFILES
from eval.scan import scan, term_pattern
from eval.snapshot import load, verdicts

SHEET = Path(__file__).parent / "data" / "spot_check.csv"
SAMPLE_SIZE = 30
SEED = 510
COLUMNS = [
    "row",
    "kind",
    "profile",
    "item",
    "location",
    "fits_under",
    "appearances",
    "matched",
    "context",
    "warnings_only",
    "ingredients",
    "decision",
    "note",
    "label_key",
]


def context(ingredients: str, terms: list[str], width: int = 40) -> str:
    """The text around every place each matched word appears, to read at a glance.

    Shows every occurrence, including ones an exception removed before matching
    ("cocoa butter"), so the reviewer sees all of them and judges the real one.
    """
    snippets = []
    for term in terms:
        for m in term_pattern(term).finditer(ingredients):
            start, end = max(0, m.start() - width), m.end() + width
            snippets.append(f"...{ingredients[start:end]}...")
    return " | ".join(snippets)


def candidates(snapshot: dict) -> list[dict]:
    """Every (recipe, profile) that fits under either filter, with its scan hits."""
    labels = snapshot["labels"]
    names = {loc["id"]: loc["name"] for loc in snapshot["locations"]}
    found = defaultdict(lambda: {"under": set(), "appearances": 0})
    for menu in snapshot["menus"]:
        for item in menu["items"]:
            if not item["label"]:
                continue  # nothing to scan; the eval counts these separately
            for key, profile in TEST_PROFILES.items():
                ours, base = verdicts(item, labels, profile)
                under = {n for n, v in (("packplate", ours), ("baseline", base))
                         if v == FITS}  # fmt: skip
                if not under:
                    continue
                entry = found[(item["label"], key)]
                entry["under"] |= under
                entry["appearances"] += 1
                entry["item"] = item["name"]
                entry["location"] = names[menu["location_id"]]
    rows = []
    for (label_key, key), entry in sorted(found.items()):
        ingredients = labels[label_key]["ingredients"]
        hits = scan(ingredients, key)
        rows.append(
            {
                "label_key": label_key,
                "profile": key,
                "item": entry["item"],
                "location": entry["location"],
                "fits_under": "+".join(sorted(entry["under"])),
                "appearances": entry["appearances"],
                "matched": "; ".join(hits.terms),
                "context": context(ingredients or "", hits.terms),
                "warnings_only": "; ".join(hits.advisory),
                "ingredients": ingredients or "",
            }
        )
    return rows


def sheet(rows: list[dict], sample_size: int = SAMPLE_SIZE, seed: int = SEED):
    """Flagged rows first, then a fixed random sample of scannable unflagged rows.

    Flagged rows are sorted by matched word and context, so identical cases
    (one shared sauce in many recipes) sit next to each other.
    """
    flagged = sorted(
        (r for r in rows if r["matched"]),
        key=lambda r: (r["matched"], r["context"], r["profile"], r["label_key"]),
    )
    clean = [r for r in rows if not r["matched"] and r["ingredients"]]
    sample = random.Random(seed).sample(clean, min(sample_size, len(clean)))
    sample.sort(key=lambda r: (r["label_key"], r["profile"]))
    out = []
    for kind, group in (("flagged", flagged), ("sample", sample)):
        for r in group:
            out.append({**r, "row": len(out) + 1, "kind": kind,
                        "decision": "", "note": ""})  # fmt: skip
    return out


def main():
    """Write eval/data/spot_check.csv, unless a sheet already exists."""
    if SHEET.exists():
        sys.exit(f"{SHEET} already exists; delete it first to rebuild it.")
    rows = candidates(load())
    out = sheet(rows)
    # utf-8-sig so Excel shows characters like "–" correctly.
    with SHEET.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(out)
    flagged = sum(1 for r in out if r["kind"] == "flagged")
    print(f"recipe/profile pairs that fit under either filter: {len(rows)}")
    print(f"flagged by the scan: {flagged}")
    print(f"random unflagged sample: {len(out) - flagged}")
    print(f"wrote {SHEET}")


if __name__ == "__main__":
    main()
