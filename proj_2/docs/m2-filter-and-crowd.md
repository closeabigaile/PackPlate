# M2 — Dietary filter, group finder, and crowd reports

**Status (2026-10-12):** backend built on `feature/filters-crowd`, not yet
merged. The filter rules need team review. No frontend yet (see M4).

## Goal

Let one student, or a group with different diets, see what they can eat and
where everyone can eat together: allergies, vegetarian, halal, and goals like
a protein target (the 1b mission). Then let them see how busy each place is
before walking over.

The worst thing PackPlate can do is call a dish safe when it isn't. So every
gap in the data makes a result `incomplete`, never `fits`.

## Dietary filter and group finder

### What exists

- `POST /filters/locations/{id}/menus?date=`: that location's menus for the
  day, with a verdict per person on every item (`fits`, `conflicts`, or
  `incomplete`) and the reasons.
- `POST /filters/group?at=`: every location, with how many items fit each
  person and whether everyone has something. Ranked: everyone fits first, then
  open at `at`, then by name.
- **Profiles** (1–10 per request): `avoid` (dairy, egg, gluten, nuts, pork,
  seafood, sesame, soy), `diets` (halal, vegan, vegetarian), `min_protein_g`,
  `max_calories`, `max_sodium_mg`, and an optional `name`.
- **Privacy:** profiles are sent with each request and never stored.
- **Strict input:** an unknown allergen, diet, or field name is rejected (422),
  never ignored. Ignoring `"peanuts"` would make every item "fit".

### The rules

Written out at the top of `backend/app/services/filter_engine.py`.

| Profile asks for | Item | Verdict |
|---|---|---|
| Avoid an allergen | lists it (icon or label) | conflicts |
| | has a trait we don't recognize | incomplete |
| | has no nutrition label | incomplete |
| A diet | tagged with it (vegan also counts as vegetarian) | fits |
| | lists an allergen that rules it out (pork → halal, vegetarian, vegan; seafood → vegetarian, vegan; dairy, egg → vegan) | conflicts |
| | otherwise | incomplete |
| A nutrition goal | no label, or the nutrient isn't printed | incomplete |
| | outside the limit | conflicts |

Any conflict makes the item `conflicts`; otherwise any gap makes it
`incomplete`; otherwise it `fits`.

## Crowd reports

### What exists

- `POST /crowd/{id}` with `{"level": "not_busy" | "moderate" | "crowded"}`
  stores a report and returns the location's new crowd level.
- `GET /locations` and `GET /locations/{id}` include each location's `crowd`:
  level, number of recent reports, and the time of the latest one.
- **Level:** worked out from reports in the last 30 minutes
  (`CROWD_WINDOW_MINUTES`), with newer reports counting more. With no recent
  reports the level is `null` (unknown), not "not busy".
- **No race conditions:** reports are only ever added, never edited, and the
  level is calculated when read. The architecture critique predicted crowd
  counts going wrong under concurrent writes; this design avoids it.
- **Privacy:** nothing about the reporter is stored.
- **Spam limit:** one report per client address per location per minute
  (429 with `Retry-After` otherwise). Kept in memory only.

## For the team to decide

The filter rules decide what a student with an allergy is told, and
AI_USAGE.md says people should own them.

- Should an untagged item be `incomplete` for a diet (current), or `conflicts`?
- Vegan counts as vegetarian but not as halal. Agreed?
- Students on the same campus Wi-Fi may share one address, and so share the
  once-a-minute crowd-report limit. Is that acceptable?
- Should crowd reports be refused while a location is closed?

## Evidence

- 69 backend tests pass, including unit tests for every filter rule and for
  the crowd weighting, window, and throttle, plus API tests for single-person
  and group filtering, crowd reports, and rejected input.
- Nine deliberate bugs in the safety rules and crowd logic were each caught by
  the tests.
- On real 2026-10-07 data, the 29 items that "fit" a nut- and dairy-free
  profile were checked against their ingredient text. None contained dairy or
  nuts.
- Crowd reports checked end to end against the dev database (see AI artifact
  04): report accepted, repeat refused with 429, level shown in `/locations`.

## Done when

- [ ] The team has reviewed and signed off on the filter rules
- [ ] Merged into `dev`
- [ ] M0's safety and usefulness thresholds are met (or the review decision is
  recorded)
- [ ] The group and menu pages in M4 show verdicts and reasons
- [ ] The "How Busy Is It?" page lets a student report in one tap and shows
  each location's level

## Leads into Project 3

The 1b report lists predicting busy periods from accumulated crowd reports.
The reports are kept for that, with no reporter data attached.
