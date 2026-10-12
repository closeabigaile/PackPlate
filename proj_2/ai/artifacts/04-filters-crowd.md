# 04 — Filter engine and crowd reports

| | |
|---|---|
| **Author** | Moe Ko |
| **Date** | 2026-10-12 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

The AI was asked to finish the backend, with an emphasis on correctness. No
constraints were given; the AI was asked to set its own and record them.

Before writing code, the AI reviewed the repository and the Project 1b report.
The read API from artifact 03 was complete. Steps 3 (filter engine) and 4
(crowd reports) of the plan in artifact 03 were still empty stubs, so the work
covered those two steps.

## 2. AI proposal

These are the constraints the AI set itself, and where each came from:

- **Filtering is stateless and on the server.** Profiles come in a POST body
  and are never stored. This follows the report's privacy stakeholders
  ("avoid unnecessary storage of dietary information"). The 1b audit's defect
  was an allergen check not enforced on the server, which is why the check
  runs there.
- **Unknown is never safe.**
  - An item without a nutrition label is `incomplete` for allergy checks.
    The README already said this about `--no-nutrition`.
  - An unrecognized trait is `incomplete`.
  - An unknown allergen or diet key, or a misnamed field, gets a 422. It is
    never ignored, because ignoring it would make everything "fit".
- **Crowd reports are append-only and aggregated on read.** This answers the
  architecture critique's prediction of a read-modify-write race in crowd
  counts. Nothing about the reporter is stored. Spam is limited by an
  in-memory throttle: one report per client address per location per minute.
- **Keep the layering and single-writer rules.** The API writes only
  `crowd_reports`, which is added in a new Alembic migration (0002).

Filter rules it proposed (now at the top of
`backend/app/services/filter_engine.py`):

- **Avoided allergen.**
  - Listed on the item → `conflicts`.
  - Otherwise, if the item has an unrecognized trait or no label →
    `incomplete`.
- **Required diet.**
  - Tagged with that diet → fits. Vegan also counts as vegetarian.
  - Lists an allergen that rules the diet out → `conflicts`. Pork rules out
    halal, vegetarian and vegan. Seafood rules out vegetarian and vegan.
    Dairy and egg rule out vegan.
  - Otherwise → `incomplete`, because being untagged doesn't prove anything.
- **Goals** (min protein, max calories, max sodium).
  - No label, or the nutrient isn't printed on it → `incomplete`.
  - Outside the limit → `conflicts`.

Crowd level: reports from the last 30 minutes, weighted so newer ones count
more (linear decay), averaged and rounded to a level. If there are no
reports, the level is `null` (unknown), not "not busy".

## 3. Human review

- _TODO (team): the filter rules above decide what a student with an allergy
  is told. AI_USAGE.md suggests these rules be written and reviewed by people.
  Review them before merging, especially:_
  - _untagged items are `incomplete` for diets, not `conflicts`;_
  - _vegan counts as vegetarian, but not as halal._
- _TODO (team): is one report per client per location per minute right? On
  shared campus Wi-Fi, students behind one address share the limit._
- _TODO (reviewer): record changes requested in PR review._

## 4. Final version

On branch `feature/filters-crowd`, from `dev`.

- **Schema.** `CrowdReport` is in `db/models.py`. Migration
  `0002_crowd_reports` adds a check constraint on `level` and an index on
  (location, time).
- **Filters.**
  - `POST /filters/locations/{id}/menus?date=` returns that location's menus
    with one result per profile on every item.
  - `POST /filters/group?at=` returns, for each location and each profile,
    how many items fit, conflict, or are incomplete, plus `everyone_fits`.
    Locations are ranked everyone-fits first, then open, then by name.
- **Crowd.**
  - `POST /crowd/{id}` stores a report and returns the new level. It returns
    429 with `Retry-After` when throttled.
  - `/locations` and `/locations/{id}` now include `crowd`.
- **Contract.** The allergen and diet keys are written out in the backend,
  because the Docker image doesn't include `ingestion/`. A test checks that
  they match `ingestion/normalize.py`.

## 5. Verification

Checks the AI ran and reported:

- **Tests.**
  - `pytest` in `backend/`: **69 passed** against Postgres 16 in Docker
    (22 before).
  - `pytest ingestion`: **43 passed**, including the check that the models
    match the migrations.
- **Mutation checks.** The AI broke nine rules on purpose, one at a time.
  The tests caught every one:
  - treat a missing label as safe;
  - ignore unrecognized traits;
  - accept a misnamed profile field;
  - stop counting vegan as vegetarian;
  - allow pork for halal;
  - treat a missing nutrient as fine;
  - bypass the throttle;
  - ignore the crowd window;
  - use "anyone fits" instead of "everyone fits".
- **Migration.** Ran 0002 up, down, and up again on the dev database.
- **End to end.** This used the 2026-10-07 data already in the dev database
  (Fountain and Case, 331 items).
  - Profiles: Sam avoids nuts and dairy. Ana is vegan and wants at least 10 g
    of protein.
  - `/filters/group` at noon ranked Fountain first (`everyone_fits`). Ana's
    one fit there is a plant-based sausage patty with 12 g of protein.
  - Case had no fits for either profile.
  - The 29 distinct items that "fit" Sam were checked by keyword against
    their ingredient text. The one hit was "Butter Flavor (Sunflower Oil,
    …)", which isn't dairy.
  - The crowd report, the 429 and `/docs` all worked. The test report was
    then deleted from the dev database.
- `docker compose build backend` succeeded, and the image imports the app.

Human checks (tick what was actually done):

- [ ] Reviewed the filter rules in `services/filter_engine.py`
- [ ] Ran the API locally and opened `/docs`
- [ ] Reviewed the code in a PR
