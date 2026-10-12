# M4 — "Where can we eat right now?" web app

**Status (2026-10-12):** wireframes done on `feature/frontend` (Savanah). The
Next.js pages (`/`, `/locations`, `/group`) are still stubs.

## Goal

One responsive site, for computer and phone, that answers "where can we eat
right now?" in one view instead of about 20 navigations across two sites.
This is what the demo and both videos show.

## Pages (from the wireframes)

| Page | Shows | Backed by |
|---|---|---|
| Home | The five features below | — |
| What's Open Now | Open locations and their hours; closed ones below, with a dropdown for future menus | `GET /locations` |
| Menus & Nutrition | A location's menus for a day, with allergens, diets, and nutrition | `GET /locations/{id}/menus` |
| My Dietary Profile | Allergies and dietary preferences | Used by the two filter endpoints |
| Eat as a Group | Several profiles; locations where everyone can eat | `POST /filters/group` |
| How Busy Is It? | Each location's crowd level, and a way to report | `POST /crowd/{id}`, `crowd` in `GET /locations` |
| Login / Signup | — | No backend yet |

## Must get right

- **Show `incomplete` honestly.** An incomplete item is never shown as safe, and
  its reasons are visible ("no nutrition label: allergens come from icons
  only").
- **Show data freshness** from `GET /freshness`, and warn when data is stale.
- **Typed API contract.** Generate TypeScript types from the API's OpenAPI
  spec, so a field renamed on one side breaks the build instead of the demo.
  The architecture critique named frontend/backend field mismatches as a
  likely week-3 failure.
- **NC State theme**, as the wireframes note.

## For the team to decide

The wireframes include Login/Signup and a saved "My Dietary Profile". The
backend currently never stores dietary information, following the 1b
report's privacy stakeholders. Options:

1. No accounts: keep the profile in the browser (local storage) only.
2. Accounts that store profiles, which needs auth, a new table, and a
   privacy note about storing health-related data.

Option 1 delivers the same experience with far less risk and work.

## Done when

- [ ] Every page above works on a phone and a computer, against the real API
- [ ] A group can go from opening the site to choosing a location in under
  two minutes (measured in M0's bonus study)
- [ ] TypeScript types are generated from the API, not hand-written
- [ ] Teaser (12–30 s) and walk-through (2–5 min) videos recorded from it
