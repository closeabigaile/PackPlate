# 11 — M0 loop 2: re-testing after the fixes

| | |
|---|---|
| **Author** | Ethan Goodman |
| **Date** | 2026-10-20 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

M0 loop 1 (artifact 06) missed Safe. Since then the team added ingredient
flags (#17, fixed in #20), label reviews (#19), and menu warnings (#23). I
asked whether loop 1 was still valid, and then for a second eval that tests
today's PackPlate on new days.

The working rules were the same as in artifacts 05 and 06:

- one step at a time, reported in a table, and committed by me before the next
  step started;
- no guessing;
- the AI never commits or pushes.

I added one more rule: loop 1 and loop 2 must be completely independent, with
separate code, commands, results, CI jobs, and badges, so either can be
removed without breaking the other.

## 2. AI proposal

The AI checked loop 1 against today's code and found:

- **Loop 1 still reproduces,** but it measures the filter as it was before
  #17: it builds items without the new ingredient flags.
- **Re-running loop 1's scan wouldn't be independent.** The new scanner copies
  about 99% of loop 1's word list and was tuned on loop 1's misfires, so
  scanning again would check the scanner against itself.

It offered to re-run loop 1 or build a new loop. For the new loop, it proposed
that a person read the ingredients of a random sample of `fits` answers, with
no word list. Its plan, in order:

1. Pre-register the targets, days, sample size, and seed (issue #26).
2. Export a frozen snapshot of the new days, including ingredient flags and
   approved reviews.
3. Draw 50 random `fits` answers into a sheet that hides PackPlate's flags
   and reasons.
4. Hand check, done by me.
5. Runner: `python -m eval_loop2.m0` and `--check`.
6. CI: its own tests step, workflow, and badge.
7. Docs.
8. Post the results on #26.
9. This artifact.

Problems it found along the way:

- **The scanner may have seen these days.** The #20 tuning happened while Oct
  20–22 were already in the database. This is disclosed in #26: the
  independence comes from the hand check, not from the days.
- **Some answers can't be checked.** 294 `fits` answers have no ingredient
  text, so they're left out of the draw and counted.
- **The bound is over 45, not 50.** Unclear answers count neither way, so 0
  in 45 gives a 6.4% upper bound instead of the "about 6%" in the plan.

Mistakes the AI made:

- It first added loop 2 to loop 1's snapshot exporter, before I had asked for
  separation. It reverted the change (loop 1 still matched its results) and
  rebuilt everything in `eval_loop2/`.
- It started implementing right after showing the task list, instead of
  waiting for my go.
- It credited the ingredient flags to #19; they are #17, and #19 is label
  reviews.
- In the step 5 report it said the lower Useful number was expected because
  of the new flags. It corrected this in the docs: the days changed too, so
  the eval can't tell which one caused the drop.
- Its first tests missed two bugs it planted on purpose: a sample drawn with a
  seed other than the one in #26 (step 3), and a group counted again for every
  location that fits (step 5). It added a test for each.

## 3. Human review

- I chose a new loop over re-running loop 1, and required the two to be fully
  independent. I accepted duplicate code as the price: loop 2 has its own
  copies of the profiles, the simulator, and its settings.
- I chose the days (Oct 20–22). I questioned whether the database had data
  for them, and pasted the coverage output before the snapshot was exported.
- I set the sample size (50), the seed (2026), and the thresholds (0 missed;
  80% answered), and posted them in #26 before the snapshot existed.
- I judged all 50 rows myself, 25 at a time. The AI suggested a decision for
  each row; I decided.
- I set the natural-flavors rule before judging any row: `unclear` for pork,
  halal, vegan, and vegetarian, `ok` for the allergens US law requires labels
  to name. I posted it in #26.
- I kept loop 1's CI workflow unchanged and only renamed its README badge to
  "M0 loop 1".
- The team made the review decision and recorded it in #26.

## 4. Final version

On branch `m0/re-measure`, all under `proj_2/eval_loop2/`, one commit per step:

- **`export_snapshot.py`**: exports `data/snapshot.json`. The data covers
  Oct 20–22, with menus at 12 locations and 2,826 items in all, with 690 labels carrying
  ingredient flags and 0 approved reviews.
- **`snapshot.py`**: runs today's filter on the snapshot the way the API does,
  with approved reviews applied by the backend's own `reviewed()`.
- **`sample.py`**: writes `data/sample.csv`, 50 answers drawn from 7,774 with
  seed 2026, holding my decisions.
- **`simulate.py`** and **`simulation.json`**: copies of loop 1's, with only
  the days changed.
- **`m0.py`**: `python -m eval_loop2.m0` writes `results.json`, and `--check`
  compares against it. It refuses to run if the sheet no longer matches the
  draw.
- **CI**: an "M0 loop 2 tests" step in the Tests workflow (38 tests) and a
  separate `m0_loop2.yml` workflow with its own badge.
- **Docs**: a loop 2 part in the README and in `m0-eval.md`, `why.md`, and
  `how.md`. The docs generator skips a loop whose folder is missing.

**Result:**

- **Safe: met.** 0 missed in 50 (45 ok, 5 unclear). That puts the miss rate at
  6.4% or lower, with 95% confidence. All 5 unclear answers are natural
  flavors for a pork, halal, vegan, or vegetarian profile.
- **Useful: met.** 90.2% of 1,000 groups were answered, down from loop 1's
  100%.

## 5. Verification

- [x] Ran it manually: I ran the database coverage check and the snapshot
  export against the shared database, and pasted their output.
- [x] I filled in and saved all 50 hand-check rows.
- [x] I posted the pre-registration, the natural-flavors rule, and the results
  and decision in issue #26.
- [x] I reviewed each step's report, then committed and pushed it myself.
- [ ] Tests pass on GitHub: the Tests and M0 loop 2 workflows ran green.

The AI ran these checks; no person did:

- `pytest eval eval_loop2`: 148 passed. Both `python -m eval.m0 --check` and
  `python -m eval_loop2.m0 --check` matched, after every step.
- Deliberate bugs in the runner, one at a time: unknown hours counted as open,
  the meal filter dropped, a group counted twice, unclear answers counted in
  the bound, a changed threshold, and decisions not lowercased. Each was
  caught after the fixes above.
- A changed sheet, tried on a copy, was refused.
- A test that loop 2 never imports loop 1, plus searches in both directions.
- The docs generator, run with each loop's folder deleted in a copy.
- Every PR number in the docs, checked against the merge commits.
