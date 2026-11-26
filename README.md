# 🐺 PackPlate 🍽️

<!-- Badges report the dev branch. Each links to its workflow runs on dev. -->
[![Tests](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml?query=branch%3Adev)
[![Test count](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/EthanGoodman/723b874f576ec1c7acbc27ac884ffeca/raw/packplate-tests.json)](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml?query=branch%3Adev)
[![Coverage](https://codecov.io/gh/morgansimon425/PackPlate/branch/dev/graph/badge.svg)](https://app.codecov.io/gh/morgansimon425/PackPlate/tree/dev)
[![Ruff](https://github.com/morgansimon425/PackPlate/actions/workflows/ruff.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/ruff.yml?query=branch%3Adev)
[![Black](https://github.com/morgansimon425/PackPlate/actions/workflows/black.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/black.yml?query=branch%3Adev)
[![Prettier](https://github.com/morgansimon425/PackPlate/actions/workflows/prettier.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/prettier.yml?query=branch%3Adev)
[![ESLint](https://github.com/morgansimon425/PackPlate/actions/workflows/eslint.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/eslint.yml?query=branch%3Adev)
[![Typecheck](https://github.com/morgansimon425/PackPlate/actions/workflows/typecheck.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/typecheck.yml?query=branch%3Adev)
[![M0 loop 1](https://github.com/morgansimon425/PackPlate/actions/workflows/m0.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/m0.yml?query=branch%3Adev)
[![M0 loop 2](https://github.com/morgansimon425/PackPlate/actions/workflows/m0_loop2.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/m0_loop2.yml?query=branch%3Adev)
[![M0 Project 3](https://github.com/morgansimon425/PackPlate/actions/workflows/m0_project3.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/m0_project3.yml?query=branch%3Adev)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23521650.svg)](https://doi.org/10.5281/zenodo.23521650)

**Project 3 teaser (26 seconds):** [Watch the teaser](proj_3/vids/teaser.mp4)

**Project 3 feature walkthrough (4 minutes 12 seconds):** [Watch the walkthrough](proj_3/vids/Demo_vid_packplate.mp4)

A website that helps NC State students decide where to eat on campus. It puts
dining hours, menus, and nutrition information from every campus dining
location in one place, and filters the menus by dietary restrictions and goals
like allergies, vegetarian, halal, or a protein target. Students can enter
constraints for several people at once, so a group with different diets can
find a location where everyone has something to eat. Students can report how
busy each location is, make an account to save their diet, chat with friends,
and ask a dining assistant questions in plain words.

**Project 3.** This is the third round of the course project. Project 2 built the
menus, filters, and crowd reports. Project 3 adds user accounts, group chat,
saved diets and recommendations, a crowd forecast, and the dining assistant
(M1 to M5 below), and has its own M0 eval for accounts and chat.

**Status:** a working course project. The menu and hours data are NC State's own
and can be wrong, so PackPlate never says a dish is safe. It says `fits`,
`conflicts`, or `incomplete`, and `incomplete` is the answer whenever the data
has a gap.

## ✨ What it does

| | Milestone | What you get |
|---|---|---|
| **M0** | Risk-killer evals | Project 2: filters for a whole group, tested against NC State's real data. Project 3: accounts and private chat, tested with simulated users. See [the evidence](#-m0-risk-killer-eval). |
| **M1** | User accounts | Sign up with a username (3-30 letters, numbers, or `_`) and a password (8-128 characters). Passwords are hashed with scrypt. A login lasts 30 days in an HttpOnly cookie, and the database keeps only a hash of the token. Ten failed logins in 15 minutes lock that username for a while. You can delete your account. |
| **M2** | Crowd tracker | Tap not busy, moderate, or crowded for a location on the **How busy** page. Reports from the last 30 minutes count, newer ones count more, and one client can report a location once a minute. Nothing about the reporter is stored. When nobody has reported, a **forecast** from the time of day, the opening hours, and the campus calendar fills in. It is an estimate, and it is labeled as one. |
| **M3** | Dining assistant | Ask in plain words: what is for dinner, what fits my diet, what is open, how busy is it, which hall is closest to where I am. It answers only from PackPlate's own data, never says a food is safe, and refuses medical questions. |
| **M4** | Group chat | Logged-in students make a chat room, invite friends, and talk. Turn on **Open to Chat** (off by default) to appear on the list others can invite from. |
| **M5** | Saved diet and recommendations | A logged-in student saves their dietary profile to their account, and it follows them to any device. Logged out, it stays in the browser. Ask for meals that meet a goal, such as high protein or under 600 calories. |

### How the dining assistant answers

A message is read by rules, looked up with read-only tools, and answered from
fixed templates. A checker rejects any reply that has a number, time, dish, or
place that was not in the lookup. A diet or place you type is used for that
question only and is not stored.

Three services are optional, free, and on by default. Each falls back safely
when it is off or unreachable.

| Setting | What it does | Without it |
|---|---|---|
| `ASSISTANT_LLM_ENABLED` | A local [Ollama](https://ollama.com) model (`qwen2.5:1.5b`) works out what was asked. It never writes the reply. | The rules alone |
| `ASSISTANT_GEOCODE_ENABLED` | Looks up a place you type that is not on the campus list (OpenStreetMap Nominatim) | Only listed campus places are found |
| `ASSISTANT_ROUTING_ENABLED` | Driving distance to halls too far to walk (OSRM) | Straight-line miles |

No account or payment is needed for any of them. `ASSISTANT_ENABLED=false`
removes the assistant. All settings are in [`proj_3/.env.example`](proj_3/.env.example).

## 🚀 Quick start

You need Git, Python 3.12, Node 22, and Docker (for a local database). The full
steps, including Windows and the team's shared database, are in
[INSTALL.md](INSTALL.md).

```bash
git clone --branch dev https://github.com/closeabigaile/PackPlate.git
cd PackPlate
python3 -m venv proj_3/.venv
source proj_3/.venv/bin/activate
pip install -r proj_3/requirements-dev.txt
(cd proj_3/frontend && npm ci)

cd proj_3
cp .env.example .env
docker compose up -d db
export DATABASE_URL=postgresql://packplate:packplate@localhost:5432/packplate
export PYTHONPATH=$PWD
alembic -c db/alembic.ini upgrade head                       # create the tables
python -m ingestion.run --units 1 --days 1 --no-nutrition   # a little data to look at
python -m uvicorn app.main:app --app-dir backend --reload   # terminal 1: the API
cd frontend && npm run dev                                  # terminal 2: the website
```

Open http://localhost:3000. Check http://localhost:8000/health shows
`"db": "ok"` and `"schema": "current"`.

- After you pull new migrations, a local database updates itself when the API
  starts. A hosted database such as Supabase never does: run
  `alembic -c db/alembic.ini upgrade head` once from `proj_3/`.
- The app does not read `.env` by itself. Export the settings, or run
  `set -a; source .env; set +a` first.
- If the website runs on a port other than 3000, start the API with
  `FRONTEND_ORIGIN=http://localhost:<port>`, or the browser blocks its calls.
- Problems? See the troubleshooting table in [INSTALL.md](INSTALL.md).

## 🧱 Tech stack

| Layer | Technology |
|---|---|
| Website | Next.js 16, React 19, TypeScript |
| API | FastAPI, SQLAlchemy 2, Alembic |
| Database | PostgreSQL (Docker locally, Supabase shared) |
| Scraper | Python, runs daily from GitHub Actions |
| Checks | pytest, Ruff, Black, Prettier, ESLint |

Every library and its license is listed in
[THIRD_PARTY_LIBRARIES.md](THIRD_PARTY_LIBRARIES.md). The Python requirements
files don't pin most versions, so a fresh install may get newer ones.

## 🎯 M0: risk-killer eval

PackPlate has one M0 per project. The **Project 3 M0** comes first and is the
one for the new accounts and chat. The **Project 2 M0** (food safety, loops 1
and 2) follows it.

### Project 3: accounts and private chat

**The claim:** simulated students can complete every authorized account and
chat journey, and nobody without permission can read or write a private
message.

| Target | Result | |
|---|---|---|
| **Reliable:** 100% of authorized journeys complete | **6 of 6** | ✅ met |
| **Private:** 0 forbidden reads or writes accepted | **0 of 21** attempts | ✅ met |

- **Journeys:** a conversation across logout and sign-in, two separate groups,
  leaving a three-person and a two-person group, and deleting an account from
  each. The 21 denied attempts are reads and writes by outsiders, signed-out
  users, and removed members.
- **Users:** fictional Alice, Bob, and Charlie, with separate cookies, in a
  disposable local database. These are **simulated users, not real ones**, and
  the result does not show that students want chat.
- **Controls:** three deliberately broken versions are each caught, so the
  eval can fail.
- **Reproduce:** `cd proj_3 && python eval_project3/m0.py --check`. It needs a
  local `packplate_m0_project3` database (`M0_DATABASE_URL`). The **M0 Project
  3** badge means the committed numbers reproduce.
- **Details:** [the plan](proj_3/docs/m0-eval-project3.md) and
  [the result](proj_3/eval_project3/results.json).

### Project 2: food safety

**The claim**, posted in [issue #11](https://github.com/morgansimon425/PackPlate/issues/11)
before the first run: a group of friends with different diets can find
somewhere on campus where everyone can eat, using NC State's own data, without
PackPlate ever telling someone a dish is safe when it isn't.

| Target | Result | |
|---|---|---|
| **Safe:** 0 confirmed false fits | **6** in 7,926 "fits" answers checked | ❌ missed |
| **Useful:** at least 80% of simulated groups answered | **100%** of 1,000 groups | ✅ met |

- **Safe:** every "fits" answer's ingredient list was scanned, and a person
  read every flag. The 6 real ones come from NC State's own data missing an
  allergen icon, e.g. cooked chicken fat in a soup tagged Vegetarian, and whey
  in a pancake with no dairy icon. NetNutrition's own icon-only filter makes
  the same 6 mistakes.
- **Useful:** simulated groups of 2–5 people, with restriction rates from
  published studies. These are **simulated users, not real ones**.
- **Data:** a frozen snapshot of Oct 12–14, 2026, committed to the repo.
- **Reproduce:** `cd proj_3 && python -m eval.m0`. The **M0 loop 1** badge
  means the committed numbers reproduce, not that the targets were met.
- **Details:** [the plan](proj_3/docs/Project%202%20docs/m0-eval.md),
  [the result](proj_3/eval/results.json), and the review decision in
  [issue #11](https://github.com/morgansimon425/PackPlate/issues/11).

#### Loop 2: after the fixes

Loop 1 showed that NC State's icons leave allergens out, so PackPlate now reads
the ingredient lists itself and flags what the icons miss
([#17](https://github.com/morgansimon425/PackPlate/pull/17), tuned in
[#20](https://github.com/morgansimon425/PackPlate/pull/20)), lets the team
correct a dish's tags by hand
([#19](https://github.com/morgansimon425/PackPlate/pull/19)), and warns on the
menu that labels can be wrong
([#23](https://github.com/morgansimon425/PackPlate/pull/23)). Loop 2 re-tests
today's PackPlate on new days, with targets posted in
[issue #26](https://github.com/morgansimon425/PackPlate/issues/26) before the
run. Because the new scanner was built from loop 1's word list, loop 2 doesn't
use a word list: a person read the ingredients of 50 random "fits" answers.

| Target | Result | |
|---|---|---|
| **Safe:** 0 missed in 50 random "fits" answers | **0** missed (45 ok, 5 unclear) | ✅ met |
| **Useful:** at least 80% of simulated groups answered | **90.2%** of 1,000 groups | ✅ met |

- **Safe:** 0 misses in 45 decided answers means the true miss rate is at most
  6.4% (95% confidence), not that it's 0. The 5 unclear answers list "natural
  flavors" for a pork, halal, vegan, or vegetarian profile, where the label
  can't tell.
- **Useful:** lower than loop 1's 100%. The days and the filter both changed,
  so the eval can't say how much of the drop each one caused.
- **Data:** a frozen snapshot of Oct 20–22, 2026, committed to the repo.
- **Reproduce:** `cd proj_3 && python -m eval_loop2.m0`. It has its own
  **M0 loop 2** badge and shares no code with loop 1.
- **Details:** [the plan and limits](proj_3/docs/Project%202%20docs/m0-eval.md#loop-2-after-the-fixes)
  and [the result](proj_3/eval_loop2/results.json).

## 📚 Documentation

| | |
|---|---|
| [Why PackPlate](proj_3/docs/why.md) | The problem, who it's for, and the evidence that it works |
| [How to use it](proj_3/docs/how.md) | Worked examples: the website, the API, and common developer tasks |
| [Code reference](proj_3/docs/reference.md) | Every module, class, and function, generated from the code |
| [HTTP API](proj_3/docs/api.md) | Every endpoint and data model, generated from the API |
| [Install](INSTALL.md) | Getting PackPlate running on your machine |
| [Contributing](CONTRIBUTING.md) | Setup, tests, checkers, and how to make changes safely |
| [Code of conduct](CODE-OF-CONDUCT.md) · [License](LICENSE.md) · [Third-party libraries](THIRD_PARTY_LIBRARIES.md) | |

## ⚠️ Known limits

- **Labels can be wrong.** PackPlate reads NC State's data. Menus carry the
  warning "Labels can be wrong; check ingredients."
- **Estimates are estimates.** The crowd forecast is hand-tuned, and its
  campus-calendar breaks are not filled in yet. The assistant's walking times
  come from straight-line distance.
- **Some coordinates are unverified.** Not every campus place has been checked
  on a map, and Wolves' Den has no position yet.
- **Local data goes stale.** The daily scrape updates the shared database, not
  yours. Run `python -m ingestion.run` at most once or twice a day.
- **The assistant is not medical advice.** It refuses those questions.

## 📁 Structure

```
proj_1b/    Project 1b — requirements
proj_3/     Projects 2 and 3 — implementation (Next.js + FastAPI + Postgres)
            backend/ API · frontend/ website · ingestion/ scraper · db/ schema
            docs/ guides · eval/ M0 tests
```

## 🎓 Course

CSC 510 Software Engineering, NC State University, Fall 2026.
Course repository: https://github.com/txt/se26f
