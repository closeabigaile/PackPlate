# AI Usage

How the PackPlate team uses AI tools in Project 2, and where to find the
evidence. Every significant AI-assisted change has an artifact file in
[`artifacts/`](artifacts/) recording what the AI proposed, what a human
changed, and how the result was checked.

## Tools

| Tool | Model / version | Used by | Where it runs |
|---|---|---|---|
| Claude Code | Claude Opus 5.5 | Ethan, Moe, Morgan | VS Code extension |
| Claude | Sonnet 5.5 | Savanah | Browser |
| _TODO_ | | | |

## What we use AI for

- Generating project scaffolding and boilerplate (see
  [01-scaffolding](artifacts/01-scaffolding.md))
- Explaining course requirements and tooling options
- Porting a prototype into production code, finding its bugs, and writing
  tests (see [02-ingestion](artifacts/02-ingestion.md))
- _TODO: add as the project goes (e.g. first drafts of tests, PR review)_

## What we do not use AI for

- _TODO: team to decide. Suggestions:_
  - _Deciding allergen and dietary labelling rules. A wrong "fits" can
    hurt someone, so these are written and reviewed by people._
  - _Merging code no human has read._
  - _Writing M0 eval results or self-assessed rubric scores._

## How AI output is checked

1. Whoever uses AI output reviews it by hand and tests it before
   committing.
2. A different teammate reviews the pull request before it is merged.
3. The person who ran the session writes an artifact file from
   [`TEMPLATE.md`](artifacts/TEMPLATE.md).
4. CI runs the test suite on every push, so a regression blocks the
   merge.

## Artifact index

| # | Artifact | Author | Date |
|---|---|---|---|
| 01 | [Project 2 scaffolding](artifacts/01-scaffolding.md) | Whole team | 2026-10-05 |
| 02 | [Ingestion pipeline](artifacts/02-ingestion.md) | Ethan Goodman | 2026-10-06 |
| 03 | [Backend database connection and read API](artifacts/03-backend-read-api.md) | Moe Ko | 2026-10-07 |
| 04 | [Filter engine and crowd reports](artifacts/04-filters-crowd.md) | Moe Ko | 2026-10-12 |
| 05 | [CI, code quality tools, and badges](artifacts/05-ci-quality.md) | Ethan Goodman | 2026-10-18 |
| 06 | [M0 risk-killer eval](artifacts/06-m0-eval.md) | Ethan Goodman | 2026-10-18 |
| 07 | [Ingredient-based allergen flags](artifacts/07-allergen-flags.md) | Morgan Simon | 2026-10-19 |
| 08 | [Review queue for contradicted diet tags](artifacts/08-label-reviews.md) | Morgan Simon | 2026-10-19 |
| 09 | [Shared database and daily scrape](artifacts/09-shared-db-schedule.md) | Morgan Simon | 2026-10-19 |
| 10 | [Menu display and nutrition info unavailable](artifacts/10-menu-display.md) | Morgan Simon | 2026-10-20 |
| 11 | [M0 loop 2: re-testing after the fixes](artifacts/11-m0-loop-2.md) | Ethan Goodman | 2026-10-20 |
| 12 | [Frontend development from wireframes](artifacts/12-frontend.md) | Savanah Hendzel | 2026-10-18 |
 
M2 predicted crowd levels - November 12-25, 2026

AI tool: Claude (Sonnet 5.5), used in the browser chat.

Files: `crowd_forecast.py`, `app/api/locations.py`, `app/schemas/crowd.py`, `app/schemas/locations.py`, `test_crowd_forecast.py`, `test_crowd_forecast_api.py`, `types.ts`, `Badges.tsx`, `busy/page.tsx`, and the M2 milestone description in docs.

Task: Improve the busyness estimates without asking students to report crowd levels, while keeping the existing crowd reports working.

AI assistance: Assisted with comparing options, writing the crowd forecast service, adding the forecast field to the locations API, adding a predicted badge to the How Busy page, writing tests, and drafting the milestone description. The first suggestion assumed a different tech stack (Flask and SQLite) and was corrected after Claude read the repository's FastAPI and Postgres code. The meal-rush times and cut-offs are hand-tuned guesses, and the campus calendar list is left empty because AI should not invent campus dates.

Conclusion and verification: The existing crowd field was left unchanged so other features are not affected. The 13 forecast unit tests passed on my machine, and black, ruff and the docs generator ran clean. Claude also ran the backend tests in its own environment before handoff (100 passed). The 3 database API tests and the frontend checks are run by CI, and the predictions have not yet been compared with real crowds at a dining hall.

Human reviewer: Satwi.

M2 conclusion reports and saved outputs

| Date | Report / conclusion | Supporting output |
|---|---|---|
| November 12-25, 2026 | Crowd forecast built and tested | `crowd_forecast.py`, 13 unit tests, 3 API tests |
| November 27, 2026 | M2 milestone description added | Milestone description in docs |
