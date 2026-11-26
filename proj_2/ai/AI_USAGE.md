# AI Usage

How the PackPlate team uses AI tools in Projects 2 and 3, and where to find the
evidence. Every significant AI-assisted change has an artifact file in
[`artifacts/`](artifacts/) recording what the AI proposed, what a human
changed, and how the result was checked.

## Tools

| Tool | Model / version | Used by | Where it runs |
|---|---|---|---|
| Claude Code | Claude Opus 5.5 | Ethan, Moe, Morgan | VS Code extension |
| Claude | Sonnet 5.5 | Savanah | Browser |
| Claude Code | Claude Opus 5.5 | Aditya (Project 3) | Terminal (CLI) |
| ChatGPT | GPT-6 series | Supreme Constantine | Browser |
| _TODO_ | | | |

## What we use AI for

- Generating project scaffolding and boilerplate (see
  [01-scaffolding](artifacts/01-scaffolding.md))
- Explaining course requirements and tooling options
- Porting a prototype into production code, finding its bugs, and writing
  tests (see [02-ingestion](artifacts/02-ingestion.md))
- Project 3: building user accounts, wiring a teammate's chat code to them,
  and saving diets to accounts (see [14-accounts](artifacts/14-accounts.md))
- Project 3: auditing and redesigning the UI, and recording the demo videos
  (see [15-ui-refresh](artifacts/15-ui-refresh.md))
- _TODO: add as the project goes (e.g. first drafts of tests, PR review)_
- Planning and implementing Project 3 meal recommendations, integration,
  debugging, and testing (see [13-m5-meal-comparison](artifacts/13-m5-meal-comparison.md))
- _TODO: add remaining Project 3 team contributions_

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
| 14 | [User accounts, chat integration, and saved diets](artifacts/14-accounts.md) | Aditya | 2026-11-16 |
| 15 | [UI refresh and demo videos](artifacts/15-ui-refresh.md) | Aditya | 2026-11-25 |
| 13 | [M5 meal comparison and integration](artifacts/13-m5-meal-comparison.md) | Supreme Constantine | 2026-11-24 |
AI-assisted work for PackPlate's Project 3 team.

## Project 3 M4 review, M0 verification, and documentation - November 2026

- **AI tool:** OpenAI Codex.
- **Files:** M4 chat documentation and tests reviewed; Project 3 M0 evaluator,
  scenarios, and results checked; installation/contribution guides,
  documentation generator/reference, CI workflows, and evidence reports updated.
- **Task:** Review and document group chat and account-access rules, verify
  Project 3 M0, and complete setup, contribution, and CI documentation.
- **AI assistance:** Assisted with reviewing edge cases and test coverage,
  drafting documentation, regenerating API/reference files, inspecting hosted
  CI results, correcting workflow configuration, and running local checks.
- **Conclusion and corrections:** Added the missing Project 3 evaluator to the
  reference generator. The hosted Tests failure came from missing badge
  publishing credentials; the workflow now checks configuration before that
  optional step and retains test/coverage reports. Routine M0 checks now use
  Project 3, with inherited evaluations kept manual. Local verification passed
  474/474 application tests and Project 3 M0's 6/6 authorized journeys, with
  zero unauthorized accesses in 21 attempts and both faulty controls detected.
  Hosted verification of the updated workflows remains pending.
- **Human reviewer:** Abigail Close.

### Project 3 reports and supporting outputs

| Date                 | Report / conclusion                                                                    | Supporting output                                                                                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| November 19–21, 2026 | [Project 3 M0 evaluation and findings](../docs/m0-eval-project3.md)                    | [Recorded M0 outcomes](../eval_project3/results.json) and [fixed scenarios](../eval_project3/scenarios.json)                                                                                    |
| November 24, 2026    | [M4 completed work](../docs/m4-chat-room.md) and [CI evidence](../docs/ci-evidence.md) | [Local verification summary](../docs/ci-evidence/local-validation.json), [backend tests](../docs/ci-evidence/local/backend.xml), and [ingestion tests](../docs/ci-evidence/local/ingestion.xml) |
