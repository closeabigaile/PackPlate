# 07 — Ingredient-based allergen flags

| | |
|---|---|
| **Author** | Morgan Simon |
| **Date** | 2026-10-19 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

Fix the 6 false fits found by the M0 eval (#11): items whose ingredients
contain an allergen that NC State's labels leave out (issue #15). PackPlate
must never claim an item contains an allergen or is safe, and the rules must
be deterministic and based on US standards.

## 2. AI proposal

An ingredient scanner in ingestion, starting from the M0 word list (kept as a
separate copy so the eval stays independent), with cross-contact warnings
ignored. Its results are stored apart from NC State's allergens and make an
item `incomplete` rather than `fits`.

## 3. Human review

- **Alternatives to a hardcoded list.** I asked what official apps use and
  had the AI evaluate Open Food Facts on our 1,329 ingredient lists. It added
  few real words and conflicts with the US soybean oil exemption, so it was
  not adopted.
- **Sourced rules.** I required every category to cite a standard: FDA major
  allergens and its 2025 guidance (e.g. the 12 tree nuts), the FDA gluten and
  flour rules, and the Vegetarian and Vegan Societies. Halal is not scanned
  beyond pork, since no single standard exists.
- **Judging by ingredients, not names.** I proposed it; tested on a week of
  real data, it dropped real flags (e.g. bacon lost its pork flag), so names
  still count and only verified look-alikes are skipped.
- **Checking flags by hand.** I questioned the dairy flag on NC State's Vegan
  Cheese Pizza; its ingredients contain no milk, so that exact phrase became
  an exception.

## 4. Final version

On `feature/allergen-flags`:

- `ingestion/ingredients.py`: sourced word lists, a plant-based imitation rule,
  and verified look-alikes; reports the matched words (`{"dairy": ["whey"]}`).
- Migration `0003` adds `nutrition.ingredient_flags`, filled by the scraper and
  returned by the menu API.
- The filter marks an item `incomplete` ("ingredients mention whey: may
  contain dairy"; "tagged vegetarian, but ingredients mention chicken"),
  never `conflicts`.
- `ingestion.backfill_flags` fills flags for stored labels (preview by
  default), and `ingestion.discrepancy_report` lists possible label gaps as a
  CSV for NC State Dining. Its first run found an item NC State tags Vegan
  whose ingredients start with tempura chicken.

## 5. Verification

- `pytest ingestion backend eval`: 252 passed against Postgres 16, including
  17 scanner tests covering the 6 M0 cases and the FDA 2025 tree nut list;
  `python -m eval.m0 --check` still reproduces `results.json`.
- On one week of real data, the plant-based rule changed only the two
  plant-based meat imitations.

Human checks (tick what was actually done):

- [ ] Read the diff on `feature/allergen-flags`
- [ ] Ran `pytest ingestion` locally
- [ ] Spot-checked flagged items against NetNutrition
