# M3 — Testing and quality pipeline

**Status (2026-10-18):** CI runs the backend and ingestion tests against
Postgres, plus Ruff, Black, Prettier, ESLint, and a type check, each with a
README badge. Pre-commit hooks format code on commit, and CONTRIBUTING.md
explains the setup. Still open: a coverage badge, the M0 eval in CI, frontend
and end-to-end tests, and reaching 150 tests.

## Goal

Every change is tested automatically, and anyone (a teammate, the tutor, or
the Project 3 team) can see that the system works without taking our word for
it. This is a systems milestone: users never see it, but it is what makes
M0's numbers reproducible and the repo safe to inherit.

The Project 2 rubric marks tests, CI, coverage, and style tools directly, and
"a badge that does not work when clicked" loses marks.

## Where we are

| Area | Tests | Runs in CI |
|---|---|---|
| Backend (`backend/tests`) | 69 | Yes, against Postgres 16 |
| Ingestion (`ingestion/tests`) | 43, including offline parsing of captured pages | Yes, against Postgres 16 |
| Frontend | None yet | Build, ESLint, Prettier, and type check only |

Strengths to keep:

- Tests cover failure cases, not just the happy path: unknown hours, missing
  labels, bad input (422), unknown locations (404), throttling (429).
- Database tests run against real Postgres, rebuilt from the Alembic
  migrations, and a test fails if the models and migrations drift apart.
- Mutation checks: deliberate bugs in the safety rules were each caught.

## Work

1. **CI (GitHub Actions).** On every push and pull request:
   - start a Postgres 16 service and run the backend and ingestion tests
     against it;
   - run the M0 eval and fail the build if a threshold is missed;
   - run the frontend lint, type check, tests, and build.

   This needs the team to reverse the earlier "no GitHub Actions yet"
   decision.
2. **Coverage.** `pytest-cov` for Python and the frontend test runner's
   coverage, reported to a coverage service so the badge shows a real number.
3. **Style, format, and syntax checkers.** One each, with config files in the
   repo, run in CI. Suggested: Ruff for Python style and syntax, Ruff format or
   Black for formatting, ESLint and Prettier for the frontend.
4. **Frontend tests.** Component tests for the pages in M4, especially that an
   `incomplete` item is never shown as safe and that its reasons are visible.
5. **End-to-end tests.** A browser test of the main flow against a seeded
   database: open the site, enter a group, pick a location.
6. **Failing test → issue → fix.** When a test fails, open an issue, link the
   fixing commit, and close it. The rubric looks for this.
7. **Badges.** Build, tests passing, coverage, and one for each checker, at
   the top of the README. Every badge must link to its proof.

## Checklist

- [x] CI runs the backend and ingestion tests against Postgres 16 on every push
  and pull request; a skipped database test fails the build
- [x] CI runs the frontend build
- [x] Style, format, and syntax checkers configured in the repo and enforced
  in CI: Ruff, Black, Prettier, ESLint, Typecheck
- [x] Pre-commit hooks run Ruff, Black, and Prettier on every commit
- [x] Badges for the build, the test count, and each checker, each linking to
  its runs
- [x] Coverage measured with `pytest-cov` and printed in CI
- [ ] Coverage shown in a live badge (Codecov; needs the repo owner)
- [ ] CI runs the M0 eval and fails if a threshold is missed (needs M0)
- [ ] Frontend tests, with coverage, run in CI (needs M4 pages)
- [ ] At least one end-to-end test of the group flow
- [ ] At least 150 tests across backend, ingestion, and frontend, covering
  expected and failure cases (112 now)
- [ ] Failing tests tracked as issues and closed by fixes
- [x] CONTRIBUTING.md explains how to run the tests and add new ones
- [ ] DOI badge from Zenodo (needs the repo owner and a GitHub release)
