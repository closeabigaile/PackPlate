# Contributing to PackPlate

How to set up, test, and check your changes before opening a pull request.
All the code lives in `proj_2/`; `proj_1b/` is finished coursework and is not
linted, formatted, or tested.

## One-time setup

You need **Python 3.12**, **Node 22**, and **Docker** (for Postgres).
On Windows, keep the clone at a short path (like `C:\Users\you\PackPlate`):
`pip install` fails with "No such file or directory" when paths pass 260
characters.

From the repo root:

```bash
python -m venv proj_2/.venv
# Activate it:
#   PowerShell:  proj_2\.venv\Scripts\Activate.ps1
#   Git Bash:    source proj_2/.venv/Scripts/activate
#   macOS/Linux: source proj_2/.venv/bin/activate
pip install -r proj_2/requirements-dev.txt
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

**Clones made before 2026-10-18 only:** line endings are now LF on every OS
(`proj_2/.gitattributes`). With a clean working tree (`git status` shows
nothing), refresh your files once:

```bash
git rm -q --cached -r proj_2
git reset -q --hard
```

This rewrites `proj_2/` from your last commit and **discards uncommitted
changes**, so commit or stash first.

## What happens when you commit

The hooks run on the files you're committing:

| Hook | Does |
|---|---|
| Ruff | Lints Python and fixes what it safely can (imports, old syntax) |
| Black | Formats Python |
| Prettier | Formats the frontend |

If a hook changes a file, **the commit stops**. Look at the changes, `git add`
them, and commit again. If Ruff reports something it can't fix, fix it by hand.
Settings are in `proj_2/pyproject.toml` and `proj_2/frontend/.prettierrc`.

## Running the tests

About a third of the tests need Postgres. Without it they're **skipped**
locally; in CI a skipped database test **fails the build**.

Start the database (from `proj_2/`):

```bash
docker compose up db
```

Then, in another terminal with the venv active, point the tests at it. The
tests create the `packplate_test` database themselves. They don't read `.env`,
so set the variable in your shell:

```bash
# Git Bash / macOS / Linux
export TEST_DATABASE_URL=postgresql://packplate:packplate@localhost:5432/packplate_test
# PowerShell
$env:TEST_DATABASE_URL = "postgresql://packplate:packplate@localhost:5432/packplate_test"
```

(If 5432 is taken by a local Postgres, set `POSTGRES_PORT` in `proj_2/.env`
and use that port here.)

| Suite | Run from | Command |
|---|---|---|
| Backend | `proj_2/backend` | `pytest` |
| Ingestion | `proj_2` | `pytest ingestion` |
| Backend with coverage | `proj_2/backend` | `pytest --cov=app --cov-config=../pyproject.toml` |
| Ingestion with coverage | `proj_2` | `pytest ingestion --cov=ingestion --cov=db --cov-config=pyproject.toml` |

With the database up, nothing should say `skipped`.

## Running the checkers

CI runs each of these, and each has a badge in the README.

| Checker | Check (what CI runs) | Fix |
|---|---|---|
| Ruff (Python lint) | `ruff check .` in `proj_2` | `ruff check --fix .` |
| Black (Python format) | `black --check .` in `proj_2` | `black .` |
| Prettier (frontend format) | `npm run format:check` in `proj_2/frontend` | `npm run format` |
| ESLint (frontend lint) | `npm run lint` in `proj_2/frontend` | by hand |
| Typecheck (frontend) | `npm run typecheck` in `proj_2/frontend` | by hand |

`pre-commit run --all-files` (from the repo root) runs Ruff, Black, and
Prettier on everything at once.

## Adding tests

Put a test next to the code it covers, in a file named `test_*.py`:

- **Backend** (`proj_2/backend/tests/`)
  - Logic with no database (rules in `app/services/`): call the function
    directly. See `test_filter_engine.py`.
  - API endpoints: use the `client` fixture (the API on the test database) and
    `seed` (inserts rows the way ingestion would). See `test_meta_api.py`.
- **Ingestion** (`proj_2/ingestion/tests/`)
  - Parsing: use `fixture_html("name.html")` with captured pages in
    `tests/fixtures/`, so tests run offline. See `test_parse.py`. Trim new
    captures to the HTML the parser reads.
  - Writing to the database: use the `db` fixture. See `test_write.py`.

Any test that uses `db`, `client`, or `seed` needs Postgres. The database is
rebuilt from the Alembic migrations once per run and emptied before each test,
so tests don't depend on each other.

Test the failure cases, not just the happy path: missing data, bad input
(422), unknown IDs (404), and anything that should come out `incomplete`
rather than `fits`.

## When a test fails

1. Open a GitHub issue: what failed, the error, and how to reproduce it.
2. Fix it on a branch and reference the issue in the PR description
   (`Fixes #12`), so the issue links to its fix.
3. Once the PR is merged into `dev`, close the issue by hand. GitHub only
   closes issues automatically on merges into the default branch (`main`).

## Branches and pull requests

- Work on a feature branch and open a pull request into `dev`. `main` gets
  `dev` once it's stable.
- CI must be green before merging. The README badges show `dev`.
- Merge with a **merge commit**, not squash or rebase. Squashing changes commit
  hashes, which breaks `.git-blame-ignore-revs`.
