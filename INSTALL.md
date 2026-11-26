# Installing PackPlate

How to get PackPlate running on your machine: the database, the API, and the
website, including Project 3's accounts, crowd forecasts, dining assistant,
group chat, saved dietary profiles, and meal recommendations. Project 3
extends the application in `proj_3/`. Each step names its working directory.
To also run the tests and the commit hooks, follow
[CONTRIBUTING.md](CONTRIBUTING.md) after this.

## 1. What you need

| Tool                                                              | Version                  | Used for                                                  |
| ----------------------------------------------------------------- | ------------------------ | --------------------------------------------------------- |
| [Git](https://git-scm.com/)                                       | any recent               | getting the code                                          |
| [Python](https://www.python.org/downloads/)                       | **3.12**                 | the API, the scraper, the tests                           |
| [Node.js](https://nodejs.org/)                                    | **22**                   | the website                                               |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | any recent, with Compose | local **Postgres 16** (or use the team's shared database) |

The assistant works with its built-in rules using these dependencies. Ollama
is an optional addition, described in step 8.

On Windows, clone to a short path (like `C:\Users\you\PackPlate`):
`pip install` fails with "No such file or directory" when paths pass 260
characters.

## 2. Get the code

```bash
git clone --branch dev https://github.com/closeabigaile/PackPlate.git
cd PackPlate
```

`dev` contains the integrated Project 3 application. If you already have a
clone on your working branch, continue there.

The application directory is now `proj_3/` (previously `proj_2/`). After
pulling this rename, recreate any existing Python virtual environment under
`proj_3/` using step 3: activation scripts and installed command shortcuts
contain the environment's original absolute path. Then reinstall the Python
dependencies. Docker Compose keeps the project name `proj_2` so the existing
database volume continues to be used.

## 3. Install the Python packages

Make sure `python --version` reports Python 3.12 before creating the virtual
environment. If needed, use `python3.12` on macOS/Linux or `py -3.12` on
Windows in place of `python` in the command below. From the repo root:

```bash
python -m venv proj_3/.venv
```

Activate it from the repo root in each new Python terminal:

| Shell         | Command                                |
| ------------- | -------------------------------------- |
| PowerShell    | `proj_3\.venv\Scripts\Activate.ps1`    |
| Git Bash      | `source proj_3/.venv/Scripts/activate` |
| macOS / Linux | `source proj_3/.venv/bin/activate`     |

Then install everything (the API, the scraper, and the test and check tools):

```bash
python -m pip install -r proj_3/requirements-dev.txt
```

## 4. Install the website's packages

```bash
cd proj_3/frontend
npm ci
cd ../..
```

`npm ci` installs exactly the versions in `package-lock.json`.

## 5. Set up a database

Pick one. The API and ingestion read their settings from the terminal's
environment. They do **not** automatically load `proj_3/.env` when run with
the commands below. Docker Compose uses that file for its database settings;
export `DATABASE_URL` separately in each terminal that needs it.

### Option A: the team's shared database (has real data)

The scraped menus already live in the team's shared Supabase Postgres
database. Ask a teammate for the connection string (it contains a password, so
it's never in the repo), and set it in the terminal you'll run the API from:

```powershell
$env:DATABASE_URL = "<connection string>"
```

```bash
# Git Bash / macOS / Linux
export DATABASE_URL="<connection string>"
```

The shared database has scraped data. Its maintainer must apply the current
migrations before you use Project 3. The API automatically migrates local
databases only, so starting it will leave a hosted Supabase database as-is.
Check `/health` in step 7 to confirm its schema is current. If it is outdated,
ask the maintainer to run `alembic -c db/alembic.ini upgrade head` from
`proj_3/` against the shared database.

Use the existing shared menus rather than running ingestion against this
database. Keep `TEST_DATABASE_URL` pointed at a disposable local database:
tests rebuild and empty it.

### Option B: a local database (starts empty)

Start Postgres in Docker, from `proj_3/`:

```bash
cd proj_3
cp .env.example .env
docker compose up -d db
```

If port 5432 is already in use (for example by a Postgres you installed
yourself), set `POSTGRES_PORT=5433` in `proj_3/.env` and use 5433 in the URLs
below.

Point the API at it, create the tables, and load some data. Run these from
`proj_3/`, with the virtual environment active:

```powershell
$env:DATABASE_URL = "postgresql://packplate:packplate@localhost:5432/packplate"
```

```bash
# Git Bash / macOS / Linux
export DATABASE_URL=postgresql://packplate:packplate@localhost:5432/packplate
```

Then migrate and load menus:

```bash
python -m alembic -c db/alembic.ini upgrade head
python -m ingestion.run --units 1 --days 1
```

- `alembic ... upgrade head` applies all migrations, including accounts, chat,
  assistant history, dining coordinates, and saved dietary profiles. Run it
  before ingestion, which requires a current schema.
- The API also upgrades local databases on startup by default, so later
  migrations are applied when you restart it after pulling changes. Set
  `MIGRATE_ON_START=false` in the API terminal to manage migrations manually.
  A failed startup migration is logged; use `/health` to check the result.
- The `ingestion.run` line loads one dining hall (Fountain) for today,
  including nutrition labels needed by dietary checks and recommendations.
  For a faster menus-and-hours check, add `--no-nutrition`. Without labels,
  allergy filters answer `incomplete` and nutrition-based recommendations can
  be empty.
  `python -m ingestion.run` with no options scrapes all locations for seven
  days with labels. NC State Dining allows scraping at most once or twice a
  day, so coordinate runs with the team and keep `SCRAPE_DELAY` at least 1.0.

For distance questions, the assistant fills in missing coordinates for known
dining locations when needed. To update coordinates after editing their
definitions, run `python -m db.seed_location_points` from `proj_3/` with
`DATABASE_URL` set and locations already loaded.

## 6. Run it

You need two terminals.

**Terminal 1: the API.** From `proj_3/`, with the virtual environment active
and `DATABASE_URL` set as in step 5:

```bash
python -m uvicorn app.main:app --app-dir backend --reload
```

**Terminal 2: the website.** From `proj_3/frontend/`:

```bash
npm run dev
```

Use `localhost` for both the website and API (ports 3000 and 8000). Account
sessions use cookies, so mixing `localhost` with `127.0.0.1` can prevent login
from persisting. For local HTTP, leave `COOKIE_SECURE` unset; use
`COOKIE_SECURE=1` when serving over HTTPS.

If your addresses differ, set `FRONTEND_ORIGIN` to the website's exact origin
in the API terminal. Set the browser's API address in
`proj_3/frontend/.env.local`, then restart the frontend:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The default addresses above work without either override. Other available
settings are documented in [`proj_3/.env.example`](proj_3/.env.example).

## 7. Check it works

| Open                                                        | You should see                                                                                    |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [API health](http://localhost:8000/health)                  | `"db": "ok"` and `"schema": "current"`                                                            |
| [Interactive API documentation](http://localhost:8000/docs) | endpoints for accounts, profiles, recommendations, chat, and the assistant, alongside dining data |
| [PackPlate](http://localhost:3000)                          | the PackPlate website                                                                             |

Then check the Project 3 features:

1. **Accounts (M1):** open [Sign up](http://localhost:3000/signup) and create
   an account. Usernames use 3–30 letters, numbers, or underscores;
   passwords use 8–128 characters and cannot equal the username.
2. **Crowd forecasts (M2):** open [How Busy Is It?](http://localhost:3000/busy).
   Loaded locations with known open hours can show a forecast even without
   student reports. Forecasts are estimates; closed locations or unknown
   hours can have no forecast.
3. **Dining assistant (M3):** while signed in, open
   [Dining Assistant](http://localhost:3000/assistant) and ask "What's open
   now?" Answers use the database's dining data; an empty or stale database
   can limit the answer.
4. **Group chat (M4):** create a second account in another browser or a private
   window. In [Group Chat](http://localhost:3000/chat), invite that exact
   username. Accept from the other account, exchange messages, then leave.
   A room starts pending, becomes active with two members, and becomes
   read-only for the remaining member if only one is left. Updates poll
   about every five seconds. See [the M4 milestone](proj_3/docs/m4-chat-room.md).
5. **Saved diet and recommendations (M5):** save a profile on
   [My Dietary Profile](http://localhost:3000/profile) while signed in.
   Log out and back in to confirm it loads from the account. Logged-out
   profiles are kept in the browser. In the interactive API docs, try
   `POST /recommendations` with `{"goal": "high_protein"}`. Include a `profile`
   in the request body to apply dietary constraints. Results require menus
   for the requested day (today by default) with suitable nutrition data;
   an empty list can be expected if you chose the no-label scrape.

These are installation checks to run on your setup. Test commands and CI
checks are described in [CONTRIBUTING.md](CONTRIBUTING.md).

## 8. Optional assistant services

The dining assistant is enabled by default (`ASSISTANT_ENABLED=true`). Its
optional integrations are also enabled by default and fall back when a
service is unavailable:

| Setting                     | Default                  | Used for                                                                                   |
| --------------------------- | ------------------------ | ------------------------------------------------------------------------------------------ |
| `ASSISTANT_LLM_ENABLED`     | `true`                   | Interpreting questions with a local Ollama model; falls back to built-in rules             |
| `ASSISTANT_LLM_URL`         | `http://localhost:11434` | Address of the Ollama server                                                               |
| `ASSISTANT_LLM_MODEL`       | `qwen2.5:1.5b`           | Model to use in Ollama                                                                     |
| `ASSISTANT_GEOCODE_ENABLED` | `true`                   | Looking up typed places outside the built-in campus list through OpenStreetMap's Nominatim |
| `ASSISTANT_ROUTING_ENABLED` | `true`                   | Looking up driving distances through OSRM; falls back to straight-line distances           |

To use the model, install and start Ollama separately, then download the
configured model:

```bash
ollama pull qwen2.5:1.5b
```

To use built-in rules and campus places without these optional service
requests, set the following in the API terminal before starting or restarting
it:

```bash
# Git Bash / macOS / Linux
export ASSISTANT_LLM_ENABLED=false
export ASSISTANT_GEOCODE_ENABLED=false
export ASSISTANT_ROUTING_ENABLED=false
```

```powershell
$env:ASSISTANT_LLM_ENABLED = "false"
$env:ASSISTANT_GEOCODE_ENABLED = "false"
$env:ASSISTANT_ROUTING_ENABLED = "false"
```

The assistant allows 10 messages per account per minute by default
(`ASSISTANT_RATE_PER_MINUTE`) and 500 characters per message
(`ASSISTANT_MAX_MESSAGE_CHARS`). Its dining answers still depend on loaded
menus and hours. See [`proj_3/.env.example`](proj_3/.env.example) for service
URL overrides.

## Troubleshooting

| Problem                                                                                                | Fix                                                                                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/health` says `"db": "unreachable"`                                                                   | `DATABASE_URL` isn't set in that terminal, or the database isn't running (`docker compose up -d db` in `proj_3/`)                                                                                                            |
| `/health` says `"schema": "outdated"`                                                                  | For a local database, check the API startup log and `MIGRATE_ON_START`, then run `python -m alembic -c db/alembic.ini upgrade head` from `proj_3/` with `DATABASE_URL` set. For the shared database, contact its maintainer. |
| An error mentions missing `chat_*`, `assistant_messages`, `location_points`, or `diet_profiles` tables | The Project 3 migrations have not all been applied to the database the API uses. Follow the schema check above.                                                                                                              |
| The website loads but shows no data                                                                    | Confirm the API is running and `NEXT_PUBLIC_API_URL` points to it. For a local database, load menus in step 5. Menus are dated; old scraped data may not cover today.                                                        |
| Login succeeds but chat or the assistant still asks you to log in                                      | Use the same hostname for the website and API, check `FRONTEND_ORIGIN`, and leave `COOKIE_SECURE` unset on local HTTP.                                                                                                       |
| The assistant returns 404                                                                              | Make sure `ASSISTANT_ENABLED` is not `false` in the API terminal.                                                                                                                                                            |
| The assistant returns 429                                                                              | Wait for the per-account rate limit to reset; the default is 10 messages per minute.                                                                                                                                         |
| The assistant can't reach Ollama                                                                       | Start Ollama and pull the configured model, or set `ASSISTANT_LLM_ENABLED=false` to use the built-in rules.                                                                                                                  |
| Recommendations are empty                                                                              | Load menus for the requested date with nutrition labels; relax any profile constraints and check again.                                                                                                                      |
| Changing `proj_3/.env` has no effect on the local API                                                  | Export the values in the API terminal and restart it; the command in step 6 does not load `.env`.                                                                                                                            |
| A CORS error in the browser console                                                                    | The website isn't on port 3000 (Next.js uses 3001 if 3000 is taken). Free port 3000, or set `FRONTEND_ORIGIN` to the website's address before starting the API.                                                              |
| PowerShell won't run `Activate.ps1`                                                                    | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or skip activating and call `proj_3\.venv\Scripts\python` directly                                                                                           |
| `ModuleNotFoundError: No module named 'app'` or `'db'`                                                 | Run the API from `proj_3/`, with `--app-dir backend` as shown                                                                                                                                                                |
