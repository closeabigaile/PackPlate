# M0 — Risk-killer eval

**Status (2026-10-18):** built and run (see Result). Safe missed, Useful met.
The review decision is recorded in the pre-registration issue (#11). The full
scrape it needs now exists in the shared database (2026-10-11, issue #3):
every item has a nutrition label, but 2,418 of 6,239 items list no allergen info, which is the
usefulness risk this eval measures.

**Loop 2 (2026-10-20):** after the fixes loop 1 led to, a second, separate
eval re-tested today's PackPlate on new days. Safe met, Useful met. See
[Loop 2](#loop-2-after-the-fixes).

## The risk

PackPlate's promise is that a group with different diets can find somewhere
on campus where everyone can eat, in one view. That depends on NC State's
published data being complete enough to answer the question.

The filter engine (M2) never calls an item "fits" when data is missing, so it
can't be made dangerous. It can be made useless. Early sign, from the
2026-10-07 data in the dev database:

- For a profile avoiding nuts and dairy, 143 of Fountain's 258 items were
  `incomplete`.
- Case had no fitting items for either test profile.

Part of this is the 40-label cap on that test scrape. Nobody knows how much.
If most items stay `incomplete` after a full scrape, the product can't deliver
its main promise, and we need to know that now.

## Hypothesis

Two claims; both must hold.

| Claim | Metric | Threshold | Baseline |
|---|---|---|---|
| Safe | False fits: items PackPlate calls `fits` for a test profile whose ingredient list contains something that profile avoids (flagged by an ingredient scan, confirmed by hand) | 0 confirmed false fits across every `fits` item in the snapshot | Icon-only filter, which treats a missing icon as safe (how NetNutrition's own trait filter behaves) |
| Useful | Answer rate: simulated group scenarios with ≥ 1 location open at that time where everyone has a `fits` item | ≥ 80% | The same scenarios with the icon-only filter |

**Test profiles:** one per allergen PackPlate knows (avoid dairy, egg, gluten,
nuts, pork, seafood, sesame, soy) and one per diet (halal, vegan, vegetarian),
eleven in all.

The baseline is expected to look more useful and be less safe. The gap
between the two is what honesty about missing data costs, and the eval
reports it.

## The instrument

1. **Frozen snapshot.** A trimmed copy of one full scrape: menus and hours
   for Mon–Wed, 2026-10-12 to 10-14 (the first three weekdays of the latest
   full scrape, fixed in the pre-registration issue), with only the fields
   the filter needs (allergens, diets,
   whether there's a nutrition label, protein, calories, sodium), plus the
   ingredient text of items the scan checks. Committed, so CI and the tutor
   run on the same data and the number is reproducible.
2. **Ingredient scan.** A script checks every item that comes out `fits` for
   a test profile, under PackPlate or the icon-only filter, against a word
   list per allergen and diet ("milk", "whey", "wheat", "almond", "gelatin",
   ...). The filter engine never reads ingredient text, so this is an
   independent check. The word list is committed.
3. **Hand spot-check.** One person reads every flagged item and confirms or
   rejects it (word lists misfire: "coconut milk", "dairy-free"), and reads
   30 random unflagged `fits` items to see whether the scan misses things.
   The decisions are committed as a CSV, so the result is reproducible.
4. **Simulated users.** Groups of 2–5 people at breakfast, lunch, and dinner
   times across the snapshot's days, with a fixed random seed. How often each
   restriction appears comes from a cited source and lives in a config file.
   The README says these are simulated users.
5. **Eval script.** `eval/m0.py` loads the snapshot, word list, and
   spot-check CSV, runs PackPlate's filter and the icon-only baseline, and
   prints confirmed false fits, answer rate, and the share of `incomplete`
   results for both. It writes the results to JSON.
6. **CI.** A GitHub Actions job runs the eval on every push. It fails if the
   eval crashes or its numbers differ from the committed results, not if a
   threshold is missed: a missed threshold is a finding to report, not a
   broken build.

## Limits to state in the results

- The ground truth checks our engine against NC State's own ingredient text.
  It does not check what the kitchen actually serves.
- "Contains Nuts" covers peanuts and tree nuts, and "Contains Seafood" covers
  fish and shellfish. The eval can't be more precise than the source.
- Simulated users are not real users.
- The scan only finds allergens its word list names. Vague ingredients
  ("natural flavors", "seasoning") can hide one; the 30-item spot-check
  estimates how often.
- One person did the spot-check; it isn't double-checked.
- Ingredient text can't prove an item is halal, so the scan can only flag
  items that clearly aren't (pork, alcohol).
- Items with no ingredient text can't be scanned; the eval reports how many.

## If it fails

A failed eval is a spiral review, not a failed milestone. Report the number,
hold the review in the pre-registration issue, and record the decision:
persevere, re-plan, or descope. Likely options:

- Fetch every nutrition label on every scrape, so fewer items lack one.
- Show "likely fits (icons only)" as a separate, clearly marked tier.
- Narrow the scope to the five dining halls.

## Bonus: real evidence

The 1b report promised to test whether a group can choose a location in
under two minutes. Time 6–10 real student groups doing the same task twice:
once with dining.ncsu.edu and NetNutrition, once with PackPlate. Record each
person's restrictions, the time taken, and whether the chosen location
actually worked for everyone.

## Result

`python -m eval.m0` from `proj_2/` (full numbers in `eval/results.json`):

| | PackPlate | Icon-only baseline |
|---|---|---|
| "Fits" answers checked against ingredients | 7,926 | 7,932 |
| Confirmed false fits (target: 0) | **6** | 6 |
| Simulated groups answered (target: 80%) | **100%** | 100% |

- **Safe: missed.** The scan raised 172 flags; a person confirmed 6 and found
  0 misses in 30 random unflagged answers. All 6 are allergens or animal
  products NC State's icons leave out, so the baseline makes the same 6.
- **Useful: met.** Every simulated group had an open location with something
  for everyone. "Something" can be one side dish, which makes this metric
  generous.
- PackPlate held back 9.3% of answers as `incomplete`, but on these days that
  cost no answered groups and prevented no false fits: icons and labels never
  disagreed.

## Checklist

- [x] Thresholds and snapshot days posted in a GitHub issue before the first
  run
- [x] Full scrape run, all units with labels on (2026-10-11, ingest run #2 in
  the shared database)
- [x] Trimmed snapshot (2026-10-12 to 10-14) exported and committed
- [x] Ingredient scan and its word list committed
- [x] Every flagged item reviewed by hand, plus 30 random unflagged items;
  decisions committed as a CSV
- [x] Simulated group scenarios with a fixed seed, and restriction frequencies
  from a cited source in a config file
- [x] `eval/m0.py` runs from a clean checkout with one command
- [x] The eval runs in CI and fails only on a crash or a changed result
- [x] Results and the review decision recorded in the issue

## Loop 2: after the fixes

Loop 1 missed Safe: all 6 false fits were allergens or animal products NC
State's icons leave out. In response, PackPlate now reads each dish's
ingredient list and flags what the icons miss (#17, false alarms fixed in #20),
the team can correct a dish's tags by hand (#19), and the menu warns that
labels can be wrong (#23). Loop 2 checks whether today's PackPlate is safe and
useful, on days loop 1 never saw. It was pre-registered in #26 and lives in
`eval_loop2/`, which shares no code with loop 1's `eval/`, so either loop can
be removed without breaking the other.

### Why a hand check, not a word list

The new ingredient scanner (#17) was built from loop 1's word list and tuned on
loop 1's misfires, so scanning with that list again would check the scanner
against itself. Instead, a person reads the ingredients.

| Claim | Metric | Threshold |
|---|---|---|
| Safe | Of 50 random `fits` answers, how many name something the profile avoids, by a person reading the full ingredient list | 0 missed |
| Useful | Answer rate of simulated groups, same rules and settings as loop 1 | ≥ 80% |

### The instrument

1. **Frozen snapshot** of Tue–Thu, 2026-10-20 to 10-22, exported from the
   shared database after #17 merged, with the stored ingredient flags and
   approved label reviews (there were none). `eval_loop2/data/snapshot.json`.
2. **Sample.** Every dish × test profile is run through today's filter, as the
   API runs it. Each `fits` answer with ingredient text, one per recipe and
   profile, can be drawn: 7,774 in all. 50 were drawn with seed 2026.
   `eval_loop2/sample.py` writes `eval_loop2/data/sample.csv`.
3. **Hand check.** The sheet shows the profile, the dish, and its ingredients,
   not PackPlate's flags or reasons. Each row is marked `ok`, `missed`, or
   `unclear` (the label can't tell).
4. **Simulated groups.** A copy of loop 1's simulator and settings (seed 510,
   1,000 groups of 2–5), with only the days changed.
5. **Eval script.** `python -m eval_loop2.m0` writes
   `eval_loop2/results.json`. Its own CI job (`m0_loop2.yml`) fails only on a
   crash, a sheet that no longer matches the draw, or a changed result.

**Natural flavors.** Agreed before any row was judged, and posted in #26: a
"natural flavors" ingredient is `unclear` for pork, halal, vegan, and
vegetarian profiles, since the label doesn't say where it comes from. For
dairy, egg, gluten, nuts, seafood, sesame, and soy it's `ok`: US law requires
those allergens to be named even inside flavorings (FALCPA, and the FASTER Act
for sesame). For gluten that law covers wheat but not barley or rye, a gap
this check accepts.

### Result

| | Loop 2 |
|---|---|
| `fits` answers that could be drawn | 7,774 (294 more had no ingredient text) |
| Hand check of 50 | 45 ok, **0 missed**, 5 unclear |
| Miss rate, 95% upper bound | 6.4% (over the 45 decided answers) |
| Simulated groups answered (target: 80%) | **90.2%** (88.8% of groups with a restriction) |
| Answers held back as `incomplete` | 9.6% |

- **Safe: met.** No sampled answer named something the profile avoids. All 5
  unclear answers were "natural flavors" for a pork, halal, vegan, or
  vegetarian profile.
- **Useful: met,** but lower than loop 1's 100%. The days and the filter both
  changed between loops, so this can't say how much of the drop the new flags
  caused.

### Limits

- 0 in 50 doesn't mean 0: the miss rate is at most 6.4% at 95% confidence.
  Loop 1 scanned every `fits` answer; loop 2 samples 50, so the two Safe
  numbers measure different things.
- If all 5 unclear answers were really misses, Safe would be missed. Their
  labels can't settle it.
- The 294 `fits` answers with no ingredient text can't be checked by anyone.
- One person did the hand check; it isn't double-checked.
- The snapshot days were already in the database while #20 tuned the scanner,
  so the scanner may have been tuned on some of these dishes. The hand check
  doesn't depend on the scanner, so it still checks the result.
- The natural-flavors rule was agreed before any row was judged but posted in
  #26 at 2:34 pm, one minute after the sheet was first saved (2:33 pm).
- The same limits as loop 1 apply: NC State's text, not the kitchen; "nuts"
  and "seafood" are as broad as the source; simulated users aren't real.

### Checklist

- [x] Thresholds, days, sample size, and seed posted in #26 before the run
- [x] Snapshot exported and committed
- [x] Sample drawn with the posted seed and committed
- [x] All 50 rows judged by hand; decisions committed in the sheet
- [x] `eval_loop2/m0.py` runs from a clean checkout with one command
- [x] Its own CI job and badge, separate from loop 1
- [ ] Results recorded in #26
