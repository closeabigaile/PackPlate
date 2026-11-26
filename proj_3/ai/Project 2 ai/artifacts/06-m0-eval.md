# 06 — M0 risk-killer eval

| | |
|---|---|
| **Author** | Ethan Goodman |
| **Date** | 2026-10-18 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

Build M0, the eval the Project 2 writeup requires: a measurable claim with a
metric, a threshold, and a baseline; a runnable script wired to CI; a number
the tutor can reproduce. The deadline was two days away.

The working rules were the same as in artifact 05:

- one step at a time, reported in a table, and committed by me before the next
  step started;
- no guessing;
- the AI never commits or pushes.

## 2. AI proposal

The AI checked the M0 plan in `docs/m0-eval.md` against the writeup and
flagged the following:

- "Fail CI if a threshold is missed" would leave the build badge red after an
  honest miss, even though a miss still earns full marks. Instead, CI should
  fail only if the eval crashes or its numbers stop reproducing.
- The thresholds have to be posted before the first run, or the eval looks
  fitted to its own result.
- Committing a full scrape would put NC State's whole data set in a public
  repo.

Its plan, in order:

0. Pre-register the claim and thresholds in an issue.
1. Snapshot: 3 days, trimmed to the fields the eval needs.
2. Icon-only baseline filter.
3. Ingredient-text scan with a word list.
4. Hand spot-check sheet.
5. Simulated groups, with restriction rates from cited sources.
6. `eval/m0.py`.
7. CI.
8. Docs.
9. Results and the review decision.
10. This artifact.

Problems it found along the way:

- **Icons and labels never disagree.** In this data the label's "Contains:"
  line never lists an allergen the icons miss. PackPlate's extra caution
  therefore barely changes anything, which leaves the ingredient scan as the
  real safety test.
- **The word list.** Several terms misfire: soybean oil, vegan chorizo, and
  "Butter Flavor" made from sunflower oil.
- **`config.json` was ignored.** The root `.gitignore` ignores every file named
  `config.json`, so the eval's settings would never have been committed. The
  file was renamed to `simulation.json`.

## 3. Human review

- I cut hand-labeling to a scan plus a spot-check, done by me alone, with no
  re-label.
- I chose a trimmed snapshot over the full data, and gave it fixed days chosen
  by a rule (the first three weekdays of the latest full scrape), posted in
  issue #11 before any eval code existed.
- I approved the word list before seeing any flags, and kept it unchanged
  afterwards, misfires included.
- I made all 202 spot-check decisions myself. The AI proposed each one and
  showed the text; I decided.
  - I kept the peanut-oil items as confirmed, even though the word list
    exempted soybean oil.
  - I confirmed the garlic bread whose label lists sesame seeds "if present".
  - Where my sheet and the AI's recommendations disagreed (rows 72/75, and row
    82 after an input glitch), I checked and corrected them.
- I decided that unknown hours count as closed, that vegan counts as
  vegetarian in the baseline too, and that M0 gets its own CI badge.
- I chose to show the actual numbers, including the miss, in the README.

## 4. Final version

On branch `m0/eval`, all under `proj_2/eval/`, one commit per step:

- **`export_snapshot.py`**: exports `data/snapshot.json`. The data covers
  Oct 12–14 at 12 locations, 3,191 items in all.
- **`baseline.py`**: works the way NetNutrition's own filter does ("Do not
  show items with…"). The AI confirmed this against the live site.
- **`scan.py` and `wordlist.py`**, plus **`spot_check.py`**, which writes
  `data/spot_check.csv`: 172 flags and 30 random unflagged items, with my
  decisions.
- **`simulate.py`** and **`simulation.json`**: 1,000 groups with seed 510.
  The rates come from Gupta et al. 2019 (JAMA Netw Open), Gallup 2023, and
  Pew.
- **`m0.py`**: `python -m eval.m0` writes `results.json`, and
  `python -m eval.m0 --check` compares against it. It refuses to run if the
  spot-check sheet no longer matches the scan.
- **CI**: `pytest eval` runs in the Tests workflow, which brings the test-count
  badge to 222. A new M0 eval workflow has its own badge.
- **Docs**: a README section with the results, and updates to the M0 and M3
  docs and CONTRIBUTING.

**Result:**

- **Safe: missed.** There were 6 confirmed false fits: chicken fat in a soup
  tagged Vegetarian, whey in a pancake with no dairy icon, sesame in garlic
  bread, and possible peanut oil in sunflower seeds (×3).
- **Useful: met.** 100% of groups were answered.
- **Baseline:** the icon-only baseline scored the same on both.

## 5. Verification

- [x] Tests pass: I pushed every step, and the Tests and M0 eval workflows ran
  green on GitHub.
- [x] Ran it manually: I ran the snapshot export against the shared database
  and pasted its summary, then filled in all 202 spot-check rows and saved
  them.
- [x] I posted the pre-registration (issue #11).
- [ ] Results and the review decision posted in issue #11. This is waiting on
  a team decision: persevere, re-plan, or descope.

The AI ran these checks; no person did:

- Deliberate bugs in each module. Each one was caught by a test after fixes;
  four were missed at first and new tests were added for them.
- The eval run twice, with `--check` matching.
- Every ingredient cell in the sheet compared with the snapshot after each save.
- Every number in the README and the docs compared with `results.json`.
- A check that the 100% answer rate wasn't a bug: open locations per time slot,
  and hard profiles such as all 8 allergens.
