"""M0 risk-killer eval: is PackPlate safe, and is it useful? One command, from proj_2/:

    python -m eval.m0            # compute, print, and write eval/results.json
    python -m eval.m0 --check    # recompute and fail if it differs from results.json

Inputs, all committed: the frozen snapshot, the hand spot-check sheet, and the
simulation settings. Thresholds were posted in the pre-registration issue
before the first run. A missed threshold is reported, not an error: only a
crash, a stale spot-check sheet, or (with --check) a changed result fails.

Safe: every `fits` answer was scanned against its ingredient list; a person
read every flag (and 30 random unflagged answers). Confirmed flags are false
fits, counted separately for PackPlate and the icon-only baseline.

Useful: a simulated group is answered if some location is open at the group's
time and every person has at least one `fits` item on that meal's menu (or an
all-day menu). Unknown hours count as closed: we can't promise it's open.
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from app.services import filter_engine
from app.services.filter_engine import FITS, INCOMPLETE
from app.services.hours import open_state
from eval import baseline
from eval.profiles import TEST_PROFILES
from eval.simulate import groups, load_config
from eval.snapshot import load, packplate_item
from eval.spot_check import SHEET, candidates, sheet

RESULTS = Path(__file__).parent / "results.json"
SAFE_MAX_FALSE_FITS = 0
USEFUL_MIN_ANSWER_RATE = 0.80
FILTERS = ("packplate", "baseline")
DECISIONS = {"flagged": {"confirm", "reject"}, "sample": {"ok", "missed"}}


class StaleSheet(Exception):
    """The spot-check sheet no longer matches what the snapshot and scan produce."""


def read_sheet(path: Path = SHEET) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["decision"] = r["decision"].strip().lower()
        if r["decision"] not in DECISIONS[r["kind"]]:
            raise StaleSheet(
                f"row {r['row']}: decision {r['decision']!r} must be one of "
                f"{sorted(DECISIONS[r['kind']])}"
            )
    return rows


def check_sheet(filled: list[dict], expected: list[dict]):
    """The filled sheet must cover exactly the rows the scan produces today."""

    def key(r):
        return (str(r["row"]), r["kind"], r["profile"], r["label_key"], r["matched"])

    if [key(r) for r in filled] != [key(r) for r in expected]:
        raise StaleSheet(
            "the spot-check sheet doesn't match the snapshot and word list any more; "
            "the decisions in it may belong to different items"
        )


def safe(rows: list[dict], pairs: list[dict]) -> dict:
    flagged = [r for r in rows if r["kind"] == "flagged"]
    sample = [r for r in rows if r["kind"] == "sample"]
    confirmed = [r for r in flagged if r["decision"] == "confirm"]
    out = {}
    for f in FILTERS:
        mine = [p for p in pairs if f in p["fits_under"].split("+")]
        hits = [r for r in confirmed if f in r["fits_under"].split("+")]
        out[f] = {
            "fits_answers_checked": sum(1 for p in mine if p["ingredients"]),
            "fits_answers_without_ingredients": sum(
                1 for p in mine if not p["ingredients"]
            ),
            "confirmed_false_fits": len(hits),
            "menu_items_affected": sum(int(r["appearances"]) for r in hits),
        }
    out["scan"] = {
        "flags": len(flagged),
        "flags_confirmed": len(confirmed),
        "random_unflagged_checked": len(sample),
        "random_unflagged_missed": sum(1 for r in sample if r["decision"] == "missed"),
    }
    out["confirmed"] = [
        {"profile": r["profile"], "item": r["item"], "location": r["location"],
         "note": r["note"]}  # fmt: skip
        for r in confirmed
    ]
    return out


class Verdicts:
    """Both filters' verdicts, cached: profiles repeat a lot across people."""

    def __init__(self, labels: dict):
        self.labels = labels
        self.cache = {}

    def fits(self, item: dict, profile, which: str) -> bool:
        key = (item["id"], profile, which)
        if key not in self.cache:
            if which == "packplate":
                obj = packplate_item(item, self.labels)
                verdict = filter_engine.check(obj, profile).verdict
            else:
                verdict = baseline.check(item["icons"], profile)
            self.cache[key] = verdict == FITS
        return self.cache[key]


class _Hours:
    """A snapshot hours row in the shape services.hours expects."""

    def __init__(self, row: dict):
        self.date = date.fromisoformat(row["date"])
        self.status, self.windows = row["status"], row["windows"]


def useful(snapshot: dict, config: dict) -> dict:
    hours = {
        (h["location_id"], date.fromisoformat(h["date"])): _Hours(h)
        for h in snapshot["hours"]
    }
    menus = defaultdict(list)
    for m in snapshot["menus"]:
        menus[(m["location_id"], date.fromisoformat(m["date"]))].append(m)
    all_day = set(config["all_day_menus"])
    verdicts = Verdicts(snapshot["labels"])

    answered = {f: 0 for f in FILTERS}
    answered_restricted = {f: 0 for f in FILTERS}
    restricted_groups = 0
    gs = groups(config)
    for g in gs:
        day = g.at.date()
        restricted = any(p.avoid or p.diets for p in g.people)
        restricted_groups += restricted
        open_items = []
        for (loc, d), ms in menus.items():
            if d != day:
                continue
            state = open_state(
                g.at, hours.get((loc, day)), hours.get((loc, day - timedelta(days=1)))
            )
            if state.is_open is not True:  # closed, or hours unknown
                continue
            items = [i for m in ms if m["meal"] == g.meal or m["meal"] in all_day
                     for i in m["items"]]  # fmt: skip
            if items:
                open_items.append(items)
        for f in FILTERS:
            if any(
                all(any(verdicts.fits(i, p, f) for i in items) for p in g.people)
                for items in open_items
            ):
                answered[f] += 1
                answered_restricted[f] += restricted
    return {
        "groups": len(gs),
        "groups_with_restrictions": restricted_groups,
        **{
            f: {
                "answered": answered[f],
                "answer_rate": round(answered[f] / len(gs), 4),
                "answer_rate_with_restrictions": round(
                    answered_restricted[f] / max(restricted_groups, 1), 4
                ),
            }
            for f in FILTERS
        },
    }


def incomplete_share(snapshot: dict) -> dict:
    """Of every item x test profile, the share PackPlate holds back as incomplete."""
    items = [i for m in snapshot["menus"] for i in m["items"]]
    counts = Counter(
        filter_engine.check(packplate_item(i, snapshot["labels"]), p).verdict
        for i in items
        for p in TEST_PROFILES.values()
    )
    total = sum(counts.values())
    return {
        "answers": total,
        "packplate_fits": round(counts[FITS] / total, 4),
        "packplate_incomplete": round(counts[INCOMPLETE] / total, 4),
    }


def evaluate() -> dict:
    snapshot = load()
    pairs = candidates(snapshot)
    filled = read_sheet()
    check_sheet(filled, sheet(pairs))
    s = safe(filled, pairs)
    u = useful(snapshot, load_config())
    return {
        "thresholds": {
            "safe_max_confirmed_false_fits": SAFE_MAX_FALSE_FITS,
            "useful_min_answer_rate": USEFUL_MIN_ANSWER_RATE,
        },
        "safe": s,
        "useful": u,
        "incomplete": incomplete_share(snapshot),
        "verdict": {
            "safe_met": s["packplate"]["confirmed_false_fits"] <= SAFE_MAX_FALSE_FITS,
            "useful_met": u["packplate"]["answer_rate"] >= USEFUL_MIN_ANSWER_RATE,
        },
    }


def render(r: dict) -> str:
    s, u, v = r["safe"], r["useful"], r["verdict"]
    lines = [
        "M0 risk-killer eval (snapshot 2026-10-12..14, simulated users)",
        "",
        f"{'':38}{'PackPlate':>11}{'Icon-only':>11}",
        f"{'Fits answers checked':38}{s['packplate']['fits_answers_checked']:>11}"
        f"{s['baseline']['fits_answers_checked']:>11}",
        f"{'Confirmed false fits':38}{s['packplate']['confirmed_false_fits']:>11}"
        f"{s['baseline']['confirmed_false_fits']:>11}",
        f"{'Groups answered (of ' + str(u['groups']) + ')':38}"
        f"{u['packplate']['answered']:>11}{u['baseline']['answered']:>11}",
        f"{'Answer rate':38}{u['packplate']['answer_rate']:>11.1%}"
        f"{u['baseline']['answer_rate']:>11.1%}",
        f"{'Answer rate, groups with restrictions':38}"
        f"{u['packplate']['answer_rate_with_restrictions']:>11.1%}"
        f"{u['baseline']['answer_rate_with_restrictions']:>11.1%}",
        "",
        f"Scan: {s['scan']['flags']} flags, {s['scan']['flags_confirmed']} confirmed; "
        f"{s['scan']['random_unflagged_missed']} missed in "
        f"{s['scan']['random_unflagged_checked']} random unflagged answers",
        f"PackPlate holds back {r['incomplete']['packplate_incomplete']:.1%} of answers "
        "as incomplete",
        "",
        f"Safe   (0 confirmed false fits): {'MET' if v['safe_met'] else 'MISSED'}",
        f"Useful (answer rate >= 80%):     {'MET' if v['useful_met'] else 'MISSED'}",
    ]
    return "\n".join(lines)


def to_json(r: dict) -> str:
    return json.dumps(r, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="fail if the result differs from eval/results.json")  # fmt: skip
    args = parser.parse_args(argv)
    try:
        result = evaluate()
    except StaleSheet as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(render(result))
    if args.check:
        if not RESULTS.exists() or RESULTS.read_text(encoding="utf-8") != to_json(
            result
        ):
            print("\nerror: the result differs from eval/results.json", file=sys.stderr)
            return 1
        print("\nmatches eval/results.json")
        return 0
    RESULTS.write_text(to_json(result), encoding="utf-8")
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
