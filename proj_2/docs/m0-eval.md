# M0 — Risk-killer eval

**Status (2026-10-18):** thresholds and snapshot days pre-registered in a
GitHub issue; eval not built yet. The full scrape it
needs now exists in the shared database (2026-10-11, issue #3): every item has
a nutrition label, but 2,418 of 6,239 items list no allergen info, which is the
usefulness risk this eval measures.

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

## Checklist

- [x] Thresholds and snapshot days posted in a GitHub issue before the first
  run
- [x] Full scrape run, all units with labels on (2026-10-11, ingest run #2 in
  the shared database)
- [ ] Trimmed snapshot (2026-10-12 to 10-14) exported and committed
- [ ] Ingredient scan and its word list committed
- [ ] Every flagged item reviewed by hand, plus 30 random unflagged items;
  decisions committed as a CSV
- [ ] Simulated group scenarios with a fixed seed, and restriction frequencies
  from a cited source in a config file
- [ ] `eval/m0.py` runs from a clean checkout with one command
- [ ] The eval runs in CI and fails only on a crash or a changed result
- [ ] Results and the review decision recorded in the issue
