# PackPlate CI evidence

Branch: `Abigail/documentation` (local worktree)\
Base commit: `02a64d5e853ce8bd2924261b82c8e77a3f721459` (not pushed)\
Generated: 2026-11-24T21:16:01Z\
Current result: **all local validation checks passed**\
Hosted result for the updated workflows: **pending**

This report verifies the current local application and workflow edits. Only
**Project 3 M0** is part of routine CI. The inherited M0 workflows are
manual-only, and their 148 instrument tests are outside the current
application test workflow. They were not run in this local verification.

The input files are identified by the source fingerprint in
[local-validation.json](ci-evidence/local-validation.json):
`5c15c87f005260fd0f0faf4a3da03892fc8769822a3088b779040e605f4bd461`. The checks used Python 3.12.10, Node 22.23.5, and Postgres
16.15 in an isolated Docker container, on macOS arm64. Hosted CI runs on
Ubuntu; these local results do not certify a future GitHub-hosted run.

| Check                                              | Local result                                                                                              |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Backend tests                                      | **389/389 passing**                                                                                       |
| Ingestion tests                                    | **85/85 passing**                                                                                         |
| Combined application tests                         | **474/474 passing; 0 skipped, failures, or errors**                                                       |
| Project 3 M0                                       | **6/6 authorized journeys; 0 unauthorized accesses in 21 denied attempts; both faulty controls detected** |
| Project 3 M0 recorded outcomes                     | reproduced; reliability and privacy targets met                                                           |
| Generated API/reference documentation              | success                                                                                                   |
| Python lint and syntax checks (Ruff)               | success                                                                                                   |
| Python format (Black)                              | success; 165 files checked                                                                                |
| Frontend format (Prettier)                         | success                                                                                                   |
| Frontend lint (ESLint)                             | success                                                                                                   |
| TypeScript type checking                           | success                                                                                                   |
| Frontend production build                          | success under Node 22                                                                                     |
| GitHub Actions workflow syntax (actionlint 1.7.12) | success                                                                                                   |
| Test-count output                                  | `message=474 passed`, `color=brightgreen`                                                                 |
| Optional badge configuration handling              | success for complete settings, missing token, missing gist ID, and both missing                           |

The production build initially could not download its configured Google
Fonts inside the restricted sandbox. It succeeded when that network access
was permitted. All results in the table are the final completed checks.

## Test-count scope

The current **474** count is the backend and ingestion pytest total. Both
suites ran against a dedicated local Postgres database with
`REQUIRE_TEST_DB=1`; the JUnit reports record no skipped tests, failures, or
errors. The Project 3 evaluator's six journeys and 21 denied attempts are
reported separately and are not added to the pytest count. A frontend build
is not a frontend test suite; automated browser coverage is not claimed.

The earlier hosted **622** count included **148 inherited M0 instrument
tests**. The decrease to 474 reflects the requested CI scope change, rather
than a changed count of application tests. The original hosted count remains
recorded in [summary.json](ci-evidence/summary.json).

## Verified local Python coverage

| Measured scope                    | Line coverage | Covered / executable lines | Branch coverage      |
| --------------------------------- | ------------- | -------------------------- | -------------------- |
| Backend `app`                     | **96.94%**    | **2314/2387**              | **563/616 (91.40%)** |
| Ingestion and shared `db` modules | **82.40%**    | **1058/1284**              | **179/240 (74.58%)** |

These values come from the local `pytest-cov` XML reports. Line percentages
use covered executable lines divided by measured executable lines; branch
percentages use covered branches divided by measured branches. The
configuration enables branch coverage and excludes `*/tests/*`.

These are separate Python measurement scopes. They do not measure frontend
code, every repository line, or coverage of the Project 3 evaluator itself.
They are **local measurements**, not a claim about Codecov's hosted report.
The portable XML copies below retain the original counts and coverage hits;
machine hostnames are omitted and source roots are made repository-relative.

## CI changes ready for the next hosted run

- Project 3 M0 runs on pushes and pull requests. Both inherited M0 workflows
  run only when manually dispatched. Their source and historical results
  remain available.
- The Tests workflow runs the backend and ingestion suites, the generated-doc
  check, and the frontend build. The count and external coverage inputs use
  the two active Python suites.
- Test and coverage XML reports are configured as a GitHub Actions artifact
  with 30-day retention. This provides source measurements independently of
  an external coverage service.
- The gist badge publisher checks for both `GIST_SECRET` and
  `TEST_BADGE_GIST_ID` before attempting publication. Missing configuration is
  recorded in the run summary and the optional publishing step is skipped.
  It is not reported as a successful publication. Configured publication
  failures and application test failures still fail the workflow.

Workflow syntax and the configuration branches were checked locally. The
artifact upload and any configured gist publication still require an actual
hosted run to verify their remote results.

## Last hosted snapshot

Branch: `dev`\
Commit: [`eeefa498df914ebec1c1ceb65f22b12304f129c7`](https://github.com/closeabigaile/PackPlate/commit/eeefa498df914ebec1c1ceb65f22b12304f129c7)\
Run date: November 22, 2026 (UTC), attempt 1\
[GitHub Actions Tests run #22](https://github.com/closeabigaile/PackPlate/actions/runs/45071945540)

That earlier run reported **622 passed**, but the overall Tests workflow
failed at **Update test badge**, with **“Missing auth secret.”** The source
annotation and step statuses are preserved in
[steps.json](ci-evidence/steps.json). The current workflow edits address the
missing-configuration path; the earlier hosted result remains a failure.

The older snapshot's workflow list includes the inherited M0 runs that were
active at that time. It is retained as historical evidence and does not
represent the current required M0 scope. Its numeric hosted coverage was not
verified: the run retained no Actions artifacts, and the Codecov commit
lookup returned 404. The local coverage above is a separate measurement.

## Supporting reports

- [local-validation.json](ci-evidence/local-validation.json): current local
  check results, tool versions, M0 outcomes, coverage, and source hashes.
- [Backend JUnit report](ci-evidence/local/backend.xml).
- [Ingestion JUnit report](ci-evidence/local/ingestion.xml).
- [Backend coverage XML](ci-evidence/local/coverage-backend.xml).
- [Ingestion/database coverage XML](ci-evidence/local/coverage-ingestion.xml).
- [summary.json](ci-evidence/summary.json): the earlier hosted run snapshot,
  including its exact commit, attempts, and publication failure.
- [steps.json](ci-evidence/steps.json): earlier hosted Tests and Project 3 M0
  job/step metadata and failure annotation.

No new hosted run was triggered for these edits. Nothing was committed or
pushed, and the README has not been changed. Refresh the hosted evidence
once a completed run exists for the updated revision; check its source
commit and attempt before citing a passing CI result.
