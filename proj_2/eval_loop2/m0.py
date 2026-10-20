"""M0 loop 2 (#26): is today's PackPlate safe and useful? One command, from proj_2/:

    python -m eval_loop2.m0            # compute, print, and write eval_loop2/results.json
    python -m eval_loop2.m0 --check    # recompute and fail if it differs from results.json

Inputs, all committed in eval_loop2/: the frozen Oct 20-22 snapshot, the hand
check of 50 random `fits` answers, and the simulation settings. Thresholds were
posted in #26 before the snapshot was exported. A missed threshold is reported,
not an error: only a crash, a stale or invalid sheet, or (with --check) a
changed result fails.

Safe: a person read the ingredients of 50 random `fits` answers (without seeing
PackPlate's flags or reasons) and marked each ok, missed, or unclear. Target:
0 missed. Unclear answers count neither way.

Useful: a simulated group is answered if some location is open at the group's
time and every person has at least one `fits` item on that meal's menu (or an
all-day menu), using today's PackPlate. Unknown hours count as closed.
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from math import comb
from pathlib import Path

from app.services.filter_engine import FITS, INCOMPLETE
from app.services.hours import open_state
from eval_loop2.profiles import TEST_PROFILES
from eval_loop2.sample import SHEET, draw, fits_answers
from eval_loop2.simulate import groups, load_config
from eval_loop2.snapshot import approved_reviews, load, verdict

RESULTS = Path(__file__).parent / "results.json"
SAFE_MAX_MISSES = 0
USEFUL_MIN_ANSWER_RATE = 0.80
DECISIONS = {"ok", "missed", "unclear"}


class StaleSheet(Exception):
    """The hand-check sheet doesn't match what the snapshot and draw produce."""


def read_sheet(path: Path = SHEET) -> list[dict]:
    """The filled-in sheet, with decisions lowercased and checked.

    Raises StaleSheet if a decision is missing or isn't ok, missed, or unclear.
    """
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["decision"] = r["decision"].strip().lower()
        if r["decision"] not in DECISIONS:
            raise StaleSheet(
                f"row {r['row']}: decision {r['decision']!r} must be one of "
                f"{sorted(DECISIONS)}"
            )
    return rows


def check_sheet(filled: list[dict], expected: list[dict]):
    """The sheet must hold exactly the 50 answers the pre-registered draw gives."""

    def key(r):
        return (str(r["row"]), r["label_key"], r["profile_key"])

    if [key(r) for r in filled] != [key(r) for r in expected]:
        raise StaleSheet(
            "the hand-check sheet doesn't match the snapshot and the draw any more; "
            "the decisions in it may belong to different answers"
        )


def upper_bound(misses: int, checked: int, confidence: float = 0.95) -> float:
    """One-sided upper confidence bound on the miss rate (exact binomial)."""
    if checked == 0:
        return 1.0

    def cdf(p):
        return sum(
            comb(checked, i) * p**i * (1 - p) ** (checked - i)
            for i in range(misses + 1)
        )

    low, high = 0.0, 1.0
    for _ in range(60):
        mid = (low + high) / 2
        low, high = (mid, high) if cdf(mid) > 1 - confidence else (low, mid)
    return round(high, 4)


def safe(rows: list[dict], pool_size: int, left_out: int) -> dict:
    """The Safe numbers from the hand check."""
    counts = Counter(r["decision"] for r in rows)
    checked = counts["ok"] + counts["missed"]
    return {
        "fits_answers_in_pool": pool_size,
        "fits_answers_left_out_no_ingredients": left_out,
        "sampled": len(rows),
        "ok": counts["ok"],
        "missed": counts["missed"],
        "unclear": counts["unclear"],
        "miss_rate_upper_bound_95": upper_bound(counts["missed"], checked),
        "missed_answers": [
            {"profile": r["profile"], "item": r["item"], "location": r["location"],
             "note": r["note"]}
            for r in rows if r["decision"] == "missed"
        ],  # fmt: skip
        "unclear_answers": [
            {"profile": r["profile"], "item": r["item"], "note": r["note"]}
            for r in rows if r["decision"] == "unclear"
        ],  # fmt: skip
    }


class _Hours:
    """A snapshot hours row in the shape services.hours expects."""

    def __init__(self, row: dict):
        self.date = date.fromisoformat(row["date"])
        self.status, self.windows = row["status"], row["windows"]


def useful(snapshot: dict, config: dict) -> dict:
    """The Useful numbers: how many simulated groups today's PackPlate answers."""
    hours = {
        (h["location_id"], date.fromisoformat(h["date"])): _Hours(h)
        for h in snapshot["hours"]
    }
    menus = defaultdict(list)
    for m in snapshot["menus"]:
        menus[(m["location_id"], date.fromisoformat(m["date"]))].append(m)
    all_day = set(config["all_day_menus"])
    approved = approved_reviews(snapshot)
    cache = {}

    def fits(item, location_id, profile):
        key = (item["id"], profile)
        if key not in cache:
            cache[key] = verdict(item, location_id, snapshot, approved, profile) == FITS
        return cache[key]

    answered = answered_restricted = restricted_groups = 0
    gs = groups(config)
    for g in gs:
        day = g.at.date()
        restricted = any(p.avoid or p.diets for p in g.people)
        restricted_groups += restricted
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
            if items and all(any(fits(i, loc, p) for i in items) for p in g.people):
                answered += 1
                answered_restricted += restricted
                break
    return {
        "groups": len(gs),
        "groups_with_restrictions": restricted_groups,
        "answered": answered,
        "answer_rate": round(answered / len(gs), 4),
        "answer_rate_with_restrictions": round(
            answered_restricted / max(restricted_groups, 1), 4
        ),
    }


def incomplete_share(snapshot: dict) -> dict:
    """Of every item x test profile, how today's PackPlate answers."""
    approved = approved_reviews(snapshot)
    counts = Counter(
        verdict(i, m["location_id"], snapshot, approved, p)
        for m in snapshot["menus"]
        for i in m["items"]
        for p in TEST_PROFILES.values()
    )
    total = sum(counts.values())
    return {
        "answers": total,
        "fits": round(counts[FITS] / total, 4),
        "incomplete": round(counts[INCOMPLETE] / total, 4),
    }


def evaluate() -> dict:
    """Run the whole loop 2 eval on the committed inputs and return the result."""
    snapshot = load()
    pool, left_out = fits_answers(snapshot)
    filled = read_sheet()
    check_sheet(filled, draw(pool))
    s = safe(filled, len(pool), left_out)
    u = useful(snapshot, load_config())
    return {
        "loop": 2,
        "days": snapshot["days"],
        "thresholds": {
            "safe_max_missed": SAFE_MAX_MISSES,
            "useful_min_answer_rate": USEFUL_MIN_ANSWER_RATE,
        },
        "safe": s,
        "useful": u,
        "answers": incomplete_share(snapshot),
        "verdict": {
            "safe_met": s["missed"] <= SAFE_MAX_MISSES,
            "useful_met": u["answer_rate"] >= USEFUL_MIN_ANSWER_RATE,
        },
    }


def render(r: dict) -> str:
    """The result as a short summary for the terminal."""
    s, u, v = r["safe"], r["useful"], r["verdict"]
    return "\n".join([
        f"M0 loop 2 (#26): today's PackPlate, snapshot {r['days'][0]}..{r['days'][-1]}",
        "",
        f"Hand check of {s['sampled']} random fits answers (of {s['fits_answers_in_pool']}):"
        f" {s['ok']} ok, {s['missed']} missed, {s['unclear']} unclear",
        f"  miss rate, 95% upper bound: {s['miss_rate_upper_bound_95']:.1%}"
        f" (over the {s['ok'] + s['missed']} decided answers)",
        f"Simulated groups answered: {u['answered']} of {u['groups']}"
        f" ({u['answer_rate']:.1%}; groups with restrictions"
        f" {u['answer_rate_with_restrictions']:.1%})",
        f"PackPlate answers incomplete: {r['answers']['incomplete']:.1%}"
        f", fits: {r['answers']['fits']:.1%}",
        "",
        f"Safe   (0 missed in the hand check): {'MET' if v['safe_met'] else 'MISSED'}",
        f"Useful (answer rate >= 80%):         {'MET' if v['useful_met'] else 'MISSED'}",
    ])  # fmt: skip


def to_json(r: dict) -> str:
    """The result as the exact text written to eval_loop2/results.json."""
    return json.dumps(r, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    """Command-line entry point. Returns the process exit code (0 or 1)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="fail if the result differs from eval_loop2/results.json")  # fmt: skip
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
            print("\nerror: the result differs from eval_loop2/results.json",
                  file=sys.stderr)  # fmt: skip
            return 1
        print("\nmatches eval_loop2/results.json")
        return 0
    RESULTS.write_text(to_json(result), encoding="utf-8", newline="\n")
    print(f"\nwrote {RESULTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
