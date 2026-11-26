# Contributing to PackPlate

## 1. Overview

PackPlate helps NC State students choose where to eat on campus. CSC 510
Project 3 extends the inherited application with accounts, crowd forecasts,
a dining assistant, group chat, saved dietary profiles, and recommendations.
The application is in `proj_2/`; `proj_1b/` is inherited coursework and is not
linted, formatted, or tested.

Contributions from team members, future maintainers, and outside contributors
are welcome. The project repository is
[closeabigaile/PackPlate](https://github.com/closeabigaile/PackPlate), and pull
requests target `dev`.

Use [GitHub Issues](https://github.com/closeabigaile/PackPlate/issues) for bugs
and proposed changes. Include steps to reproduce, expected and actual behavior,
and relevant Python, Node, operating system, or browser details. Discuss larger
changes in an issue and coordinate work on shared modules or migrations.

## 2. Code of Conduct

Follow the [Code of Conduct](CODE-OF-CONDUCT.md) in issues, pull requests, and
reviews. Use its reporting process for personal conduct concerns and keep
those reports out of public bug reports.

## 3. Project Setup

Use **Git**, **Python 3.12**, **Node.js 22**, and **Postgres 16**. Docker with
Compose provides the local database. See [INSTALL.md](INSTALL.md) for tool
links, application startup, environment settings, and sample dining data.
On Windows, keep the clone at a short path (such as `C:\Users\you\PackPlate`)
to avoid long-path installation errors.

### Contributors with repository write access

Clone the integrated `dev` branch:

```bash
git clone --branch dev https://github.com/closeabigaile/PackPlate.git
cd PackPlate
```

### Contributors using a fork

Fork the repository into your GitHub account and clone your fork. Replace
`YOUR-USERNAME` with your account name and `your-branch-name` with a descriptive
branch name. Run these commands for a new clone:

```bash
git clone https://github.com/YOUR-USERNAME/PackPlate.git
cd PackPlate
git remote add upstream https://github.com/closeabigaile/PackPlate.git
git fetch upstream
git switch -c your-branch-name upstream/dev
```

`origin` points to your fork; `upstream` points to the project repository.
Fetching `upstream/dev` lets you start from the integrated application even
when your fork initially contains only `main`. Push your contribution to your
fork and open a PR into the project's `dev` branch. Repository write access
is needed to push directly to the project; a fork gives you a place to publish
your own branch for review.

### Dependencies and local data

Both contribution paths use the same setup. From the repository root, with
Python 3.12 selected:

```bash
python -m venv proj_2/.venv
```

Activate it from the repository root in each new Python terminal:

| Shell         | Command                                |
| ------------- | -------------------------------------- |
| PowerShell    | `proj_2\.venv\Scripts\Activate.ps1`    |
| Git Bash      | `source proj_2/.venv/Scripts/activate` |
| macOS / Linux | `source proj_2/.venv/bin/activate`     |

Then install the dependencies and enable the commit hooks:

```bash
python -m pip install -r proj_2/requirements-dev.txt
cd proj_2/frontend
npm ci
cd ../..

pre-commit install
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

- `pre-commit install` turns on the commit hooks for **this clone**. Hooks
  aren't copied by `git clone`, so everyone runs it once.
- The `blame` line makes `git blame` skip the one big formatting commit, so it
  shows who really wrote each line. GitHub already does this.

[`proj_2/.gitattributes`](proj_2/.gitattributes) keeps text files on LF line
endings across platforms. Keep this setting when adding new files.

For normal development, use the local database and ingestion steps in
[INSTALL.md](INSTALL.md#5-set-up-a-database). Access to the team's shared
Supabase database is optional. Tests and M0 use the disposable local databases
described in section 8. Keep credentials, administrative keys, and session
tokens out of commits, issues, and AI records.

## 4. Branching and Workflow

Use a descriptive branch name, such as `docs/update-install` or
`fix/chat-invitations`. Existing team branch names are also supported. Replace
`your-branch-name` in the examples with the name you choose.

Before switching branches, commit or safely preserve existing changes.
For a new contribution with repository write access, run from the repository
root:

```bash
git switch dev
git pull --ff-only origin dev
git switch -c your-branch-name
```

For a new contribution from an existing fork clone, fetch the project and
create your branch from its current `dev`:

```bash
git fetch upstream
git switch -c your-branch-name upstream/dev
```

If you already created your contribution branch during setup, continue on
that branch. Make focused changes, run the relevant checks in section 8,
and review the changes before committing:

```bash
git status
git diff
git add path/to/changed-file
git diff --cached
git commit -m "Describe the change"
git push -u origin your-branch-name
```

Replace `path/to/changed-file` with each file you intend to include. For a
fork, the push goes to your own repository. Open the PR with base repository
`closeabigaile/PackPlate` and base branch `dev`.

## 5. Commit Messages

Use short, descriptive messages. Prefixes such as `feat`, `fix`, `docs`,
`refactor`, `test`, and `chore` can help explain the type of change:

```text
feat(chat): add invitation status labels
fix(profile): clear browser data after logout
docs(contributing): explain the fork workflow
```

### Commit hooks

The hooks run on the files you're committing:

| Hook     | Does                                                            |
| -------- | --------------------------------------------------------------- |
| Ruff     | Lints Python and fixes what it safely can (imports, old syntax) |
| Black    | Formats Python                                                  |
| Prettier | Formats the frontend                                            |

If a hook changes a file, **the commit stops**. Look at the changes, `git add`
them, and commit again. If Ruff reports something it can't fix, fix it by hand.
Settings are in `proj_2/pyproject.toml` and `proj_2/frontend/.prettierrc`.

## 6. Pull Request Process

1. Explain the problem, the resulting behavior, and any related issue or
   milestone. For a bug fix, include reproduction steps.
2. List the checks you ran and their results, including failures, skipped
   tests, and checks not run. Add screenshots or recordings for interface
   changes and name the browsers or layouts you checked.
3. Update affected documentation. For M0 changes, explain changed outcomes
   and link the evidence and review decision.
4. Disclose AI assistance and human review as described in section 10.
5. Request review from a maintainer or another contributor, and address the
   feedback. Maintainers merge after review approval and passing applicable
   CI checks. Investigate failures instead of removing checks to get a pass.

These are contribution expectations; they do not describe configured branch
protection. Check the PR's runs for the commit being reviewed. README badges
report a branch rather than your individual PR. Maintainers handle repository
secrets, shared-database updates, and merges; outside contributors can develop
and test with local resources.

Maintainers use merge commits when integrating PRs, following the repository's
existing workflow. `dev` is integrated into `main` once stable. Preserve the
history referenced by `.git-blame-ignore-revs`.

When a test exposes a bug, open an issue with the failure, error, and steps to
reproduce. Reference it in the fixing PR, for example `Fixes #12`, and confirm
it is closed after the merge; close it manually if needed. For an M0 finding,
include failed scenario IDs or changed metrics and the team's review decision.

## 7. Coding Standards and Extending the Application

Follow the surrounding code and the settings in
[`proj_2/pyproject.toml`](proj_2/pyproject.toml),
[`proj_2/frontend/eslint.config.mjs`](proj_2/frontend/eslint.config.mjs), and
[`proj_2/frontend/.prettierrc`](proj_2/frontend/.prettierrc).

- Within `proj_2/backend/app/`, keep HTTP routes in `api/`, business rules
  in `services/`, database queries in `repositories/`, and request/response
  models in `schemas/`.
- Within `proj_2/frontend/src/`, keep pages in `app/`, shared components
  in `components/`, and API and profile helpers in `lib/`.
- Treat missing hours, ingredients, allergens, or nutrition as unknown.
  Preserve `fits`, `conflicts`, and `incomplete` behavior and its reasons.
- Use the authenticated account for private data access. Check membership
  and invitation ownership, and preserve account-deletion cleanup rules.
- Keep changes focused, explain non-obvious decisions, and preserve existing
  attribution and license notices. Add or update meaningful tests for changed
  behavior, including failure and missing-data cases.

### Adding tests

Put Python tests in the relevant test directory, in a file named `test_*.py`:

- **Backend** (`proj_2/backend/tests/`)
  - Logic with no database (rules in `app/services/`): call the function
    directly. See `test_filter_engine.py`.
  - API endpoints: use the `client` fixture (the API on the test database) and
    `seed` (inserts rows the way ingestion would). See `test_meta_api.py`.
  - Project 3: see `test_crowd_forecast.py`, `test_assistant_api.py`,
    `test_chat_room_api.py`, `test_chat_accounts.py`, `test_profile_api.py`,
    and `test_recommendations_api.py`. Use separate session cookies when
    testing multiple accounts and include attempts to access another user's
    rooms, messages, or saved profile.
- **Ingestion** (`proj_2/ingestion/tests/`)
  - Parsing: use `fixture_html("name.html")` with captured pages in
    `tests/fixtures/`, so tests run offline. See `test_parse.py`. Trim new
    captures to the HTML the parser reads.
  - Writing to the database: use the `db` fixture. See `test_write.py`.
- **Inherited evaluations** (`proj_2/eval/tests/` and
  `proj_2/eval_loop2/tests/`): use small, fixed inputs to test the instrument;
  run the reproduction commands in section 8 to check the committed evidence.

Any test that uses `db`, `client`, or `seed` needs Postgres. The database is
rebuilt from the Alembic migrations once per run and emptied before each test,
so tests don't depend on each other.

Test the failure cases, not just the happy path: missing data, bad input
(422), missing sessions (401), forbidden access (403), unknown IDs (404),
invalid room states (409), rate limits (429), and anything that should come
out `incomplete` rather than `fits`.

### Database migrations

Edit the appropriate models in `proj_2/db/`, then create and review an
Alembic migration from `proj_2/`:

```bash
python -m alembic -c db/alembic.ini revision --autogenerate -m "describe the change"
```

Set `DATABASE_URL` to a local development database whose schema matches the
current migrations before generating the new revision. Commit the model and
migration together. Coordinate migration numbers with other contributors and keep one
Alembic head; check with `python -m alembic -c db/alembic.ini heads`.

The API applies migrations automatically only to local databases on startup.
Shared-database migrations are applied by the team's maintainer. Database
tests rebuild from migrations, so they check the schema a new installation
actually receives.

## 8. Testing and Checks

For documentation-only changes, verify links, command examples, and Markdown
formatting. For code changes, run the relevant suites and checkers below.
Keep automated tests on local fixtures and disposable databases.

### Local test database and suites

Backend and ingestion tests that use database fixtures need Postgres.
Without `TEST_DATABASE_URL`, or if the database is unreachable, those tests
skip locally. CI sets `REQUIRE_TEST_DB=1` so either condition fails instead;
use the same setting locally when checking a change before a PR.

Start the database (from `proj_2/`):

```bash
docker compose up -d db
```

Then, in another terminal with the venv active, point the tests at it. The
tests create the `packplate_test` database themselves. They don't read `.env`,
so set the variables in your shell:

```bash
# Git Bash / macOS / Linux
export TEST_DATABASE_URL=postgresql://packplate:packplate@localhost:5432/packplate_test
export REQUIRE_TEST_DB=1
```

```powershell
$env:TEST_DATABASE_URL = "postgresql://packplate:packplate@localhost:5432/packplate_test"
$env:REQUIRE_TEST_DB = "1"
```

(If 5432 is taken by a local Postgres, set `POSTGRES_PORT` in `proj_2/.env`
and use that port here.)

Use a **disposable local database** for `TEST_DATABASE_URL`. The fixtures
rebuild its schema and empty its tables; keep this URL separate from the
application's shared Supabase `DATABASE_URL`. Run the backend and ingestion
database suites sequentially when they use the same test database.

| Suite                   | Run from         | Command                                                                 |
| ----------------------- | ---------------- | ----------------------------------------------------------------------- |
| Backend                 | `proj_2/backend` | `pytest`                                                                |
| Ingestion               | `proj_2`         | `pytest ingestion`                                                      |
| Backend with coverage   | `proj_2/backend` | `pytest --cov=app --cov-config=../pyproject.toml`                       |
| Ingestion with coverage | `proj_2`         | `pytest ingestion --cov=ingestion --cov=db --cov-config=pyproject.toml` |

The backend suite includes Project 3's account, forecast, assistant, chat,
saved-profile, recommendation, and startup-migration tests. Review the test
summary to confirm the intended database cases ran.

Backend fixtures turn off automatic startup migrations and the assistant's
Ollama, geocoding, and routing requests. Test these integrations with mocks;
keep ordinary tests independent of live services and the shared database.

### Reproducing M0

Project 3's account and private-chat evaluation is the M0 check required by
current CI. Run it from `proj_2/` with the Python environment active:

| Evaluation                          | Command                              | Database                                         |
| ----------------------------------- | ------------------------------------ | ------------------------------------------------ |
| Project 3 accounts and private chat | `python eval_project3/m0.py --check` | Dedicated local `packplate_m0_project3` database |

For Project 3, follow the disposable database setup in
[m0-eval-project3.md](proj_2/docs/m0-eval-project3.md#reproduce). Set
`M0_DATABASE_URL` in the evaluator's terminal; this is separate from both
`DATABASE_URL` and `TEST_DATABASE_URL`. The evaluator accepts only a local
Postgres database named `packplate_m0_project3`, applies migrations in a
temporary schema, and removes that schema afterward. An API server does not
need to be running.

The [Project 3 workflow](.github/workflows/m0_project3.yml) runs this check on
pushes and pull requests. The inherited Project 2 evaluators and their
results remain as historical evidence; their workflows are manual-only, and
their instrument tests are outside the routine application test workflow.
Use `python -m eval.m0 --check`, `python -m eval_loop2.m0 --check`,
`pytest eval`, or `pytest eval_loop2` only when working on those historical
evaluators.
A passing reproduction check means the committed evidence matches the run;
read the recorded verdict separately to see whether a target was met.

**If your change moves the M0 numbers**, review the finding before replacing
the matching `results.json`. Running a command above without `--check`
writes that evaluator's result file. Keep the original evidence in Git,
explain the changed outcomes in the PR, and record the review with maintainers. Changes
to dietary checks can affect inherited loops; changes to accounts or chat can
affect Project 3's scenarios and controls.

Keep snapshots, scenario definitions, thresholds, and manual review sheets
consistent with the evaluation plan. Changed snapshot or sampling inputs can
require a new manual review; preserve the earlier loop's evidence. See the
[inherited plan](proj_2/docs/m0-eval.md) and
[Project 3 plan](proj_2/docs/m0-eval-project3.md).

### Format, lint, type, and build checks

CI runs these checks for relevant changes. Use this repository's PR checks
and [Actions runs](https://github.com/closeabigaile/PackPlate/actions) to
confirm the result for your branch.

| Checker                    | Check (what CI runs)                        | Fix                  |
| -------------------------- | ------------------------------------------- | -------------------- |
| Ruff (Python lint)         | `ruff check .` in `proj_2`                  | `ruff check --fix .` |
| Black (Python format)      | `black --check .` in `proj_2`               | `black .`            |
| Prettier (frontend format) | `npm run format:check` in `proj_2/frontend` | `npm run format`     |
| ESLint (frontend lint)     | `npm run lint` in `proj_2/frontend`         | by hand              |
| Typecheck (frontend)       | `npm run typecheck` in `proj_2/frontend`    | by hand              |
| Frontend production build  | `npm run build` in `proj_2/frontend`        | resolve build errors |

`pre-commit run --all-files` (from the repo root) runs Ruff, Black, and
Prettier on everything at once.

The hooks cover Python and frontend formatting; they do not run the test
suites, generated-doc checks, M0 evaluators, ESLint, Typecheck, or the build.
The [Tests workflow](.github/workflows/tests.yml) runs the backend and
ingestion suites, coverage, the generated-doc check, and the frontend build.
It saves the JUnit and coverage XML reports as an Actions artifact for 30
days. External gist badge publishing runs only when `GIST_SECRET` and
`TEST_BADGE_GIST_ID` are configured; missing settings are noted in the run
summary. An unconfigured badge publisher is separate from test success.
The checkers and Project 3 M0 have separate workflows.

The frontend currently has no automated component or browser test script.
For a UI change, run its checkers and build, then record the relevant browser
checks in the PR, including phone and desktop layouts when affected. Use the
feature walkthrough in [INSTALL.md](INSTALL.md#7-check-it-works) as a starting
point.

## 9. Documentation

[`proj_2/docs/reference.md`](proj_2/docs/reference.md) and
[`proj_2/docs/api.md`](proj_2/docs/api.md) are generated from the code: every
public module, class, and function needs a docstring, and the API's routes
describe themselves. After changing a docstring, a function signature, or an
API route, run this from `proj_2/` and commit the result:

```bash
python docs/generate.py
python docs/generate.py --check
```

CI fails if the generated files are out of date. Write new docstrings the
same way as the existing ones: one sentence saying what it does or returns,
plus anything a caller must know (what `None` means, what it raises).

Keep hand-written instructions in [INSTALL.md](INSTALL.md), this guide,
[why.md](proj_2/docs/why.md), [how.md](proj_2/docs/how.md), and the relevant
milestone pages in sync with the behavior. Project 3's
[account notes](proj_2/docs/m1-accounts.md),
[chat milestone](proj_2/docs/m4-chat-room.md), and
[M0 evidence](proj_2/docs/m0-eval-project3.md) describe the new collaboration
features. If you change something a worked example in `how.md` shows, rerun
the example and update it. Preserve the inherited M0 results alongside the
new Project 3 results, and link README claims to their result files and
workflow runs in this team's repository.

## 10. AI Assistance and Human Review

When AI tools assist with a contribution, record the tool, what it helped
with, and a concise prompt or plan summary in the PR or a linked repository
document. For significant assistance, use the existing
[AI usage recordkeeping](proj_2/ai/AI_USAGE.md) and
[artifact template](proj_2/ai/artifacts/TEMPLATE.md).

Record who reviewed the output, which code or claims they checked, the
commands and results used for verification, and any corrections or remaining
limitations. Keep credentials and private conversations out of these records.
AI-generated tests and passing CI alone do not establish human review.
Contributors remain responsible for the changes they submit.
