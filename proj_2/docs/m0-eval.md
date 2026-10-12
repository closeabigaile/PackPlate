# M0 — Risk-killer eval

**Status (2026-10-12):** not started. Thresholds below are proposed; the team
must agree and pre-register them before the first run.

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
| Safe | False-fit rate: items PackPlate calls `fits` that the hand labels say conflict | 0 of ≥ 300 labeled items (95% upper bound ≈ 1%, "rule of three") | Icon-only filter, which treats a missing icon as safe (how NetNutrition's own trait filter behaves) |
| Useful | Answer rate: simulated group scenarios with ≥ 1 location open at that time where everyone has a `fits` item | ≥ 80% | The same scenarios with the icon-only filter |

The baseline is expected to look more useful and be less safe. The gap
between the two is what honesty about missing data costs, and the eval
reports it.

## The instrument

1. **Frozen snapshot.** Run a full scrape (all units, labels on), export the
   tables to a JSON fixture, and commit it. CI and the tutor run on the same
   data, so the number is reproducible.
2. **Hand-labeled ground truth.** At least 300 items, sampled across
   locations and meals. Two teammates label each one independently from its
   ingredient text: which of the eight allergens it contains, and whether it
   is vegan, vegetarian, or halal. Record their agreement rate and settle
   disagreements together.
3. **Simulated users.** Groups of 2–5 people at breakfast, lunch, and dinner
   times across the snapshot's days, with a fixed random seed. How often each
   restriction appears comes from a cited source and lives in a config file.
   The README says these are simulated users.
4. **Eval script.** `eval/m0.py` loads the snapshot and labels, runs PackPlate's
   filter and the icon-only baseline, and prints false-fit rate, answer rate,
   and the share of `incomplete` results. It writes the results to JSON and
   exits non-zero if a threshold is missed.
5. **CI.** A GitHub Actions job runs the eval on every push, as part of the
   pipeline in M3.

## Limits to state in the results

- The ground truth checks our engine against NC State's own ingredient text.
  It does not check what the kitchen actually serves.
- "Contains Nuts" covers peanuts and tree nuts, and "Contains Seafood" covers
  fish and shellfish. The eval can't be more precise than the source.
- Simulated users are not real users.

## If it fails

A failed eval is a spiral review, not a failed milestone. Report the number,
hold the review in the pre-registration issue, and record the decision.
Likely options:

- Fetch every nutrition label on every scrape, so fewer items lack one.
- Show "likely fits (icons only)" as a separate, clearly marked tier.
- Narrow the scope to the five dining halls.

## Bonus: real evidence

The 1b report promised to test whether a group can choose a location in
under two minutes. Time 6–10 real student groups doing the same task twice:
once with dining.ncsu.edu and NetNutrition, once with PackPlate. Record each
person's restrictions, the time taken, and whether the chosen location
actually worked for everyone.

## Done when

- [ ] Thresholds agreed and posted in a GitHub issue before the first run
- [ ] Snapshot and hand labels committed, with the labelers' agreement rate
- [ ] `eval/m0.py` runs from a clean checkout with one command
- [ ] The eval runs in CI
- [ ] Results and the review decision recorded in the issue
