# 05 — CI, code quality tools, and badges

| | |
|---|---|
| **Author** | Ethan Goodman |
| **Date** | 2026-10-18 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

First, the AI reviewed the M0–M4 milestone docs against the code and reported
what was done and what was left. Then it was asked to set up the M3 quality
pipeline:

- Python coverage, Ruff and Black for Python, Prettier for the frontend
- pre-commit hooks, so formatting happens before code is pushed
- the README badges the rubric requires

Constraints from the start:

- Plan first, then do **one step at a time**. After each step the AI reports
  in a table (task | status | issues) and stops. I review and commit before
  saying "resume".
- Never guess. Leaving something undone is better than doing it by guessing.
- `proj_2/` only; leave `proj_1b/` alone.
- The AI never pushes. I push and test CI myself.

Finally, the AI rechecked the milestones and added checklists to the
milestone docs.

## 2. AI proposal

The AI said where my outline was wrong or incomplete:

- `pytest-cov` only covers Python. The frontend needs its own test runner
  (Vitest) and has no tests yet.
- Ruff and Black overlap. Use Ruff for linting and Black for formatting.
- Hooks can't install themselves when someone clones the repo, so CI still
  has to check everything.
- GitHub gives one badge per workflow file, so each checker needs its own
  workflow to get its own badge.
- Things only the repo owner can do (Morgan): Codecov and Zenodo.

Its plan, in order:

1. Tool config (`pyproject.toml`, `requirements-dev.txt`)
2. Frontend config (Prettier, eslint-config-prettier, a typecheck script)
3. Pre-commit hooks
4. One-time format commit, plus `.git-blame-ignore-revs`
5. CI test workflow against Postgres
6. One workflow per checker
7. Test-count badge
8. Codecov
9. README badges
10. CONTRIBUTING.md
11. Zenodo DOI
12. Frontend tests (deferred)

Each step also had a verification plan.

Issues the AI found while doing the work:

- **Database tests skip silently.** Both conftests skip database tests when
  Postgres is unreachable. A misconfigured CI database would skip 39 of 112
  tests and still show green.
- **Typecheck fails on a fresh checkout.** `tsc` failed on a type that Next.js
  generates into `.next/`. Fixed by running `next typegen` first.
- **Line endings on Windows.** Git converts files to CRLF on checkout, which
  breaks Prettier on Windows while CI on Linux passes.
- **FastAPI false positives.** Ruff's B008 rule flags FastAPI's `Depends()`
  and `Query()`.
- **Issue closing.** `Fixes #N` only auto-closes an issue on a merge into the
  default branch (`main`), and PRs here go into `dev`.

## 3. Human review

- I required each step to be committed on its own, so a later step couldn't
  quietly break an earlier one.
- For line endings I chose the AI's recommended `.gitattributes` fix (LF
  everywhere) over `endOfLine: auto`. I ran the one-time refresh myself.
- I rejected the "auto-install hooks" options (an npm `prepare` script, a git
  template directory, pre-commit.ci). Instead, each person runs
  `pre-commit install` once, with CI as the backstop.
- I asked why `.git-blame-ignore-revs` was needed. I kept it because it keeps
  teammates credited as the authors of the lines the format commit touched.
- I chose `dev` as the branch the badges track.
- I created the gist on my account, plus a token with only the `gist` scope,
  stored as a repo secret.
- I moved the badges ahead of Codecov, so they didn't wait on Morgan.
- I decided milestone items should be checked once they're pushed to a
  branch, because the checked docs reach `dev` along with the work.

## 4. Final version

On branch `feature/ingestion-testing-and-ci`, one commit per step.

- **Config**
  - `proj_2/pyproject.toml`: Ruff, Black, and coverage settings.
  - `proj_2/requirements-dev.txt`: pinned tool versions.
  - Frontend: Prettier, eslint-config-prettier, and `format`,
    `format:check`, and `typecheck` scripts.
  - `proj_2/.gitattributes`: LF line endings.
- **Hooks.** `.pre-commit-config.yaml` runs Ruff (with `--fix`), Black, and
  Prettier on `proj_2/`.
- **Format commit.** 42 files reformatted, listed in
  `.git-blame-ignore-revs`. Ruff also made a few fixes:
  - `timezone.utc` → `UTC`
  - two unused imports removed
  - `zip(..., strict=True)` in `filters.py`, checked by hand: the two lists
    are always the same length
- **CI.**
  - `tests.yml` runs the backend and ingestion tests against Postgres 16
    (set `REQUIRE_TEST_DB=1` to make missing-database skips fail), and
    builds the frontend.
  - One workflow each for Ruff, Black, Prettier, ESLint, and Typecheck.
- **Test-count badge.** `.github/scripts/test_badge.py` counts the JUnit
  results. On pushes to `dev`, the count is written to a gist that shields.io
  reads.
- **Docs**
  - 7 badges in the root README.
  - `CONTRIBUTING.md`.
  - Milestone docs: refreshed status lines and checklists.

## 5. Verification

- [x] Tests pass: I pushed, and all six workflows ran green on GitHub
  (commits `a986b6a` and `3e2ca76`). Because a skipped database test fails
  CI, this also shows all 112 tests ran against Postgres.
- [x] Ran it manually: I reviewed and committed each step, and set up the
  gist, token secret, and repo variable.
- [ ] Badges live on `dev` and the gist shows "112 passed": waiting on the
  merge into `dev`.

The AI ran these checks; no person did:

- Each workflow's command run locally, and each one failing on deliberately
  bad files.
- A bad commit blocked by the hooks, in a throwaway clone.
- Black changed layout only, not code, in 32 of the 41 Python files. The
  other 9 were checked by hand.
- `actionlint` on all workflows.
- A fresh clone set up by following only CONTRIBUTING.md.
- Every badge image and link returning HTTP 200.
