# AI Usage — Project 3

AI-assisted work recorded by PackPlate's Project 3 team: **Abigail, Aditya,
Satwi, and Supreme**. This file contains our team's notes and supporting
artifacts.

The original team's record is preserved in
[Project 2 ai/AI_USAGE.md](Project%202%20ai/AI_USAGE.md), using the version
inherited at commit `c152606`. Their artifacts 01–12 remain with that record
in [Project 2 ai/artifacts/](Project%202%20ai/artifacts/).

## Tools recorded by our team

| Team member | Tool | Model / version | Recorded use |
|---|---|---|---|
| Abigail Close | OpenAI Codex | GPT-6.1 Sol| M4 review, M0 verification, documentation, and CI |
| Aditya | Claude Code (terminal / CLI) | Claude Opus 5.5 | Accounts, chat integration, saved diets, UI refresh, and demo videos |
| Satwi | TODO | TODO | Add the AI-use notes for crowd forecasting |
| Supreme Constantine | ChatGPT (browser) | GPT-6 series | Meal recommendations, integration, testing, and documentation |

## Abigail — M4, M0, documentation, and CI

**Period:** November 2026. **Human reviewer recorded in the notes:** Abigail
Close.

- **Task:** Review and document group chat and account-access rules, verify
  Project 3 M0, and complete installation, contribution, and CI documentation.
- **AI assistance:** Reviewing edge cases and test coverage, drafting
  documentation, regenerating API/reference files, inspecting hosted CI
  results, correcting workflow configuration, and running local checks.
- **Files and outputs:** M4 chat documentation and tests; the Project 3 M0
  evaluator, scenarios, and results; installation/contribution guides; the
  documentation generator/reference; CI workflows and evidence reports.
- **Conclusion and corrections:** Added the missing Project 3 evaluator to
  the reference generator. Identified missing badge-publishing credentials
  as the cause of the hosted Tests failure. Updated the workflow to check
  configuration before that optional step and retain test/coverage reports.
  Routine M0 checks use Project 3, while inherited evaluations remain
  available manually.
- **Recorded verification:** The November 24 notes report 474/474 application
  tests passing and Project 3 M0's 6/6 authorized journeys, with zero
  unauthorized accesses in 21 attempts and the faulty controls detected.
  Hosted verification of those workflow edits was still pending when that
  note was written. These are dated session results, not a new test run for
  this document reorganization.

### Reports and supporting outputs

| Date | Report / conclusion | Supporting output |
|---|---|---|
| November 19–21, 2026 | [Project 3 M0 evaluation and findings](../docs/m0-eval-project3.md) | [Recorded M0 outcomes](../eval_project3/results.json) and [fixed scenarios](../eval_project3/scenarios.json) |
| November 24, 2026 | [M4 completed work](../docs/m4-chat-room.md) and [CI evidence](../docs/ci-evidence.md) | [Local verification summary](../docs/ci-evidence/local-validation.json), [backend tests](../docs/ci-evidence/local/backend.xml), and [ingestion tests](../docs/ci-evidence/local/ingestion.xml) |

## Aditya — accounts, integration, UI, and videos

**Tool:** Claude Code, Claude Opus 5.5, used through the terminal / CLI.

- **Accounts and integration, November 9–16, 2026:** AI assistance with user
  accounts, connecting chat to authenticated users, and saving dietary
  profiles to accounts. The artifact records coordination with Abigail and
  Supreme, preserving teammate authorship, reviewing integration failures,
  privacy decisions, and the checks actually run, including initially
  unavailable database tests and their later recheck.
- **UI and videos, November 25, 2026:** AI assistance with a UI audit,
  redesign, comparison against the previous interface, scripted walkthrough
  and teaser recordings, and verification. The artifact records Aditya's
  design decisions and corrections, checks of the dietary safety wording,
  and the need to disclose the demo clock and sample data.

See [14 — User accounts, chat integration, and saved diets](artifacts/14-accounts.md)
and [15 — UI refresh and demo videos](artifacts/15-ui-refresh.md) for the
requests, proposals, human review, final changes, and verification.

## Satwi — crowd forecasting

**TODO:** Satwi has not added her AI-use notes yet. Add the tool and model,
session dates, requests, AI proposals, human review and corrections, and
verification for the crowd-forecasting work. No AI-use details are assumed
until she supplies them.

## Supreme — M5 meal comparison and integration

**Tool:** ChatGPT, GPT-6 series, used in the browser. **Recorded date:**
November 24, 2026.

- **AI assistance:** Planning and implementing meal recommendations,
  understanding the inherited codebase, writing tests, debugging,
  integrating the feature with the other Project 3 work, and drafting
  documentation.
- **Human review:** Reviewing the existing repository, keeping the feature
  within the application, checking the intended workflow, working through
  integration issues, and reviewing changes through Git.
- **Final work:** A rule-based recommendation service, API, and meal
  comparison interface integrated with account-based dietary profiles.
- **Recorded verification:** The artifact identifies implementation commit
  `51a695f`, integration PR #10, the related test files, and the session's
  reported checks, including tests skipped because the database was not
  configured.

See [13 — M5 meal comparison and integration](artifacts/13-m5-meal-comparison.md)
for the full session record.

## Project 3 artifact index

| # | Artifact | Author | Recorded date |
|---|---|---|---|
| 13 | [M5 meal comparison and integration](artifacts/13-m5-meal-comparison.md) | Supreme Constantine | 2026-11-24 |
| 14 | [User accounts, chat integration, and saved diets](artifacts/14-accounts.md) | Aditya | 2026-11-09 to 2026-11-16 |
| 15 | [UI refresh and demo videos](artifacts/15-ui-refresh.md) | Aditya | 2026-11-25 |

Abigail's notes and supporting reports are recorded above. Satwi's entry
remains TODO. Keep the original artifact numbers so existing references
remain identifiable.

## Recording future sessions

Use [artifacts/TEMPLATE.md](artifacts/TEMPLATE.md) to record the request, AI
proposal, human review, final version, and verification. Identify who reviewed
the output and report failed or skipped checks alongside successful ones.
Only record tools, decisions, and results supported by the session.
