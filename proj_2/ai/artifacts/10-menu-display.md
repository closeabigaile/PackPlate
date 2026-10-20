# 10 — Menu display and nutrition info unavailable

| | |
|---|---|
| **Author** | Morgan Simon |
| **Date** | 2026-10-20 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

Polish the menu navigation in the UI, show the new ingredient warnings, list
only locations that have menus, and show "nutrition info unavailable" when NC
State's nutrition label is incomplete (PRs #22, #23, #25).

## 2. AI proposal

Group NC State's stations into sections, add meal tabs, show one listing per dish
with a size picker, name what is uncertain on each badge, and hide labels
whose numbers look wrong, starting with labels that read all zeros.

## 3. Human review

- **Badges.** I replaced the vague "Can't confirm" with specific labels such
  as "Not labeled Halal", "May contain Dairy", and "Unknown allergen".
- **Ingredient warnings.** These say "Check label", never "contains", since a
  word in the ingredients is only a possibility.
- **Sizes.** I set how the size picker works with a profile: open on the
  best-fitting size and note any size that fits worse.
- **Sections.** I kept toppings and sauces visible and in the same style, and
  asked for stations to be grouped into subsections (Flashpoint → Entrées).
- **Locations.** Locations with no menu data are hidden in the app but still
  scraped and stored.
- **Zero-calorie foods.** I rejected the all-zeros rule because it hid real
  zero-calorie foods such as lettuce. The final rule only covers prepared
  foods listed per 1 gram, dishes of the day with no recipe ("Soup Du Jour"),
  and calories NC State itself flags as incomplete.

## 4. Final version

On `feature/menu-display`, `feature/menu-warnings` and `feature/menu-polish`:
meal tabs, a size picker, specific badges sorted by fit, station subsections,
"Check label" warnings, only locations with menus, and "Nutrition info
unavailable for this item." in place of the numbers for incomplete labels. The
API returns a new `nutrition_unavailable` field on each menu item.

## 5. Verification

- `pytest`: 270 passed on `feature/menu-polish`, including new tests for the
  location filter and nutrition info unavailable. The M0 eval still matches
  its results.
- Checked on real data: the bagel, quesadilla, and soups of the day show
  nutrition info unavailable; lettuce, cucumbers, and bananas keep their
  labels. None of the 54 labels that mention Worcestershire sauce list
  anchovies, so it was not added to the seafood words.

Human checks (tick what was actually done):

- [x] Previewed the menu pages locally
- [ ] Read the diffs on the three branches
