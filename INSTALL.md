# Installing PackPlate

How to get PackPlate running on your machine: the database, the API, and the
website. All the code is in `proj_2/`. To also run the tests and the commit
hooks, follow [CONTRIBUTING.md](CONTRIBUTING.md) after this.

## 1. What you need

| Tool | Version | Used for |
|---|---|---|
| [Git](https://git-scm.com/) | any recent | getting the code |
| [Python](https://www.python.org/downloads/) | **3.12** | the API, the scraper, the tests |
| [Node.js](https://nodejs.org/) | **22** | the website |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | any recent | a local Postgres database (not needed if you use the team's shared database) |

On Windows, clone to a short path (like `C:\Users\you\PackPlate`):
`pip install` fails with "No such file or directory" when paths pass 260
characters.

## 2. Get the code

```bash
git clone https://github.com/morgansimon425/PackPlate.git
cd PackPlate
```

## 3. Install the Python packages

From the repo root:

```bash
python -m venv proj_2/.venv
```

Activate it (do this in every new terminal):

```bash
# PowerShell
proj_2\.venv\Scripts\Activate.ps1
# Git Bash
source proj_2/.venv/Scripts/activate
# macOS / Linux
source proj_2/.venv/bin/activate
```

Then install everything (the API, the scraper, and the test and check tools):

```bash
pip install -r proj_2/requirements-dev.txt
```

## 4. Install the website's packages

```bash
cd proj_2/frontend
npm ci
cd ../..
```

`npm ci` installs exactly the versions in `package-lock.json`.

## 5. Set up a database

Pick one.

### Option A: the team's shared database (has real data)

The scraped menus already live in the team's shared Supabase Postgres
database. Ask a teammate for the connection string (it contains a password, so
it's never in the repo), and set it in the terminal you'll run the API from:

```bash
# PowerShell
$env:DATABASE_URL = "<connection string>"
# Git Bash / macOS / Linux
export DATABASE_URL="<connection string>"
```

Nothing else to do: the shared database is already migrated and filled.

### Option B: a local database (starts empty)

Start Postgres in Docker, from `proj_2/`:

```bash
cd proj_2
cp .env.example .env
docker compose up -d db
```

If port 5432 is already in use (for example by a Postgres you installed
yourself), set `POSTGRES_PORT=5433` in `proj_2/.env` and use 5433 in the URLs
below.

Point the API at it, create the tables, and load some data. Run these from
`proj_2/`, with the virtual environment active:

```bash
# PowerShell
$env:DATABASE_URL = "postgresql://packplate:packplate@localhost:5432/packplate"
# Git Bash / macOS / Linux
export DATABASE_URL=postgresql://packplate:packplate@localhost:5432/packplate

alembic -c db/alembic.ini upgrade head
python -m ingestion.run --units 1 --days 1 --no-nutrition
```

- `alembic ... upgrade head` creates the tables. The API doesn't create them
  itself.
- The `ingestion.run` line is a quick scrape: one dining hall (Fountain),
  today, without nutrition labels. Without labels, allergy filters answer
  `incomplete`. `python -m ingestion.run` with no options scrapes everything:
  24 locations, 7 days, with labels. NC State Dining allows scraping at most
  once or twice a day, so don't run it more often than that.

## 6. Run it

You need two terminals.

**Terminal 1: the API.** From `proj_2/`, with the virtual environment active
and `DATABASE_URL` set as in step 5:

```bash
python -m uvicorn app.main:app --app-dir backend --reload
```

**Terminal 2: the website.** From `proj_2/frontend/`:

```bash
npm run dev
```

## 7. Check it works

| Open | You should see |
|---|---|
| http://localhost:8000/health | `"db": "ok"` and `"schema": "current"` |
| http://localhost:8000/docs | the API's interactive documentation |
| http://localhost:3000 | the PackPlate website |

## Troubleshooting

| Problem | Fix |
|---|---|
| `/health` says `"db": "unreachable"` | `DATABASE_URL` isn't set in that terminal, or the database isn't running (`docker compose up -d db` in `proj_2/`) |
| `/health` says `"schema": "outdated"` | Run `alembic -c db/alembic.ini upgrade head` from `proj_2/` |
| The website loads but shows no data | The API isn't running, or (Option B) nothing has been scraped yet |
| A CORS error in the browser console | The website isn't on port 3000 (Next.js uses 3001 if 3000 is taken). Free port 3000, or set `FRONTEND_ORIGIN` to the website's address before starting the API. |
| PowerShell won't run `Activate.ps1` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or skip activating and call `proj_2\.venv\Scripts\python` directly |
| `ModuleNotFoundError: No module named 'app'` or `'db'` | Run the API from `proj_2/`, with `--app-dir backend` as shown |
