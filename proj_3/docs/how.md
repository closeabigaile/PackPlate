# How to use PackPlate

Worked examples for common tasks in PackPlate, including features added
in Project 3. The original API examples were run on 2026-10-19 using the
team's shared database. Your results may differ as menus and hours change.
The new Project 3 examples illustrate API usage but have not been rerun.

To follow along, install and start PackPlate first ([INSTALL.md](../../INSTALL.md)).
The API runs at `http://localhost:8000`, the website at `http://localhost:3000`.

## Contents

- [Using the website](#using-the-website)
  - [Create and manage an account](#create-and-manage-an-account)
  - [Save dietary preferences](#save-dietary-preferences)
  - [Compare meals](#compare-meals)
  - [Use group chat](#use-group-chat)
  - [Ask the dining assistant](#ask-the-dining-assistant)
  - [View crowd forecasts](#view-crowd-forecasts)
- Using the API:
  [find where a group can eat](#find-where-a-group-can-eat),
  [check a menu against your needs](#check-a-menu-against-your-needs),
  [see what's open](#see-whats-open),
  [check how fresh the data is](#check-how-fresh-the-data-is),
  [report how busy a place is](#report-how-busy-a-place-is),
  [find meal recommendations](#find-meal-recommendations),
  [use authenticated endpoints](#use-authenticated-endpoints)
- For developers:
  [reproduce the M0 eval](#reproduce-the-m0-eval),
  [reproduce the Project 3 M0 eval](#reproduce-the-project-3-m0-eval),
  [change a filter rule safely](#change-a-filter-rule-safely),
  [run the scraper](#run-the-scraper),
  [update the generated docs](#update-the-generated-docs)

## Using the website

Open `http://localhost:3000`. The menu at the top has:

| Page | What it's for |
|---|---|
| **Home** | Access PackPlate's dining features |
| **What's open** | Dining locations and opening hours |
| **Menus** | Menus, allergens, diets, and nutrition |
| **Compare Meals** | Find and compare meals based on nutrition goals |
| **Eat as a group** | Find locations that match multiple dietary profiles |
| **Group Chat** | Coordinate dining plans with other students |
| **Assistant** | Ask questions about campus dining |
| **How busy** | View crowd reports and forecasts, or submit a report |
| **My diet** | Save dietary preferences and nutrition goals |
| **About** | Learn about PackPlate |
| **Log in / Username** | Sign in or manage your account |

Most dining features work without an account. Group Chat and the
Dining Assistant require users to sign in.

### Create and manage an account

1. Open **Log in** and navigate to the signup page.
2. Create an account with a username and password.
3. Once signed in, your username appears in the navigation menu.
4. Select your username to manage your account, change your Open to
   Chat preference, log out, or delete your account.

No email address, real name, or student ID is required. Password
recovery is not currently supported.

### Save dietary preferences

1. Open **My diet**.
2. Select your allergies and dietary preferences.
3. Enter any desired nutrition goals.
4. Save your profile.

When logged out, preferences are stored in the browser. When signed in,
preferences are saved to your account. They can be accessed again after
logging in.

If an account has no saved profile, preferences created while logged
out can be saved to that account on login. An existing account profile
takes priority over the browser's profile.

Saved preferences are used by Menus, Compare Meals, Eat as a group,
and the Dining Assistant.

Logging out clears the account's profile from the browser without
deleting it from the account.

### Compare meals

Suppose you want to find a high-protein lunch that matches your
dietary preferences.

1. Open **Compare Meals**.
2. Choose High Protein, Lower Calories, or Lower Sodium.
3. Select a menu date and meal period.
4. Click **Find Recommendations**.
5. Choose two results using **Select to Compare**.

PackPlate returns up to 20 ranked recommendations across campus.
Saved dietary preferences are automatically applied.

The side-by-side comparison displays calories, protein, carbohydrates,
fat, sodium, and serving size.

Nutrition values are based on the listed serving size, which may differ
between meals. Missing values are shown as N/A rather than zero.

If no eligible meals are found, try another goal, date, or meal period.

### Use group chat

1. Sign in and open **Group Chat**.
2. Find other users by username or through the Open to Chat directory.
3. Create a room and invite other users.
4. Once the room becomes active, exchange messages and coordinate
   dining plans.

Users can accept or decline invitations and leave conversations.
Conversation history remains available to permitted members.

Open to Chat is disabled by default and can be changed in account
settings. Users who know your exact username can still find and invite
you.

### Ask the dining assistant

Sign in and open **Assistant** to ask questions using PackPlate's
dining data and saved dietary preferences.

Example questions:

- What dining halls are open right now?
- Where can I find a high-protein lunch?
- What vegan options are available?
- How busy is Fountain Dining Hall?
- Which dining hall is closest?

The assistant supports follow-up questions and saves conversation
history to your account. Users can also clear their conversation.

Answers depend on available dining data and are not a guarantee of
allergen safety.

### View crowd forecasts

Open **How busy** to view reported and predicted crowd levels.

Reported crowd levels come from student submissions within the last
30 minutes. Forecasts are estimates based on time and opening hours,
rather than direct measurements.

Submit a report by selecting Not busy, Moderate, or Crowded.

No recent reports means the current crowd level is unknown, not
that the location is empty.

## Using the API

The examples use `curl` in Git Bash, macOS, or Linux. In PowerShell, `curl` is
a different command, so use **`http://localhost:8000/docs`** instead: it lets
you try every endpoint from the browser. All endpoints are listed in
[api.md](api.md).

Times are campus time. Endpoints that depend on the time take `?at=` (default:
now), so you can ask "what about Tuesday at 12:30?" at any time.

### Find where a group can eat

Three friends: Sam is vegan, Alex avoids nuts, Jordan eats halal. Where can
they all eat on Tuesday at 12:30?

```bash
curl -X POST "http://localhost:8000/filters/group?at=2026-10-20T12:30:00-04:00" \
  -H "Content-Type: application/json" \
  -d '{"profiles": [
        {"name": "Sam", "diets": ["vegan"]},
        {"name": "Alex", "avoid": ["nuts"]},
        {"name": "Jordan", "diets": ["halal"]}
      ]}'
```

You get every location, best first: places where everyone has something that
fits, then places that are open, then by name. The first one:

```json
{
  "id": 1,
  "name": "Fountain Dining Hall",
  "is_open": true,
  "closes_at": "2026-10-20T19:00:00-04:00",
  "opens_next_at": null,
  "items_checked": 218,
  "everyone_fits": true,
  "profiles": [
    {"name": "Sam", "fits": 125, "incomplete": 28, "conflicts": 65},
    {"name": "Alex", "fits": 218, "incomplete": 0, "conflicts": 0},
    {"name": "Jordan", "fits": 118, "incomplete": 95, "conflicts": 5}
  ]
}
```

So Fountain is open until 7 pm, and each of them has dozens of options. In
this run, 11 of the 24 locations had something for all three, and 5 of those
were open at 12:30.

Each profile can have:

| Field | Meaning |
|---|---|
| `name` | Optional label, echoed back |
| `avoid` | Allergens: `dairy`, `egg`, `gluten`, `nuts`, `pork`, `seafood`, `sesame`, `soy` |
| `diets` | Required diets, all of them: `halal`, `vegan`, `vegetarian` |
| `min_protein_g`, `max_calories`, `max_sodium_mg` | Nutrition goals |

You can send 1 to 10 profiles. A typo is an error, never ignored: `"avoid":
["peanuts"]` returns **422** with the allowed values, because ignoring it
would quietly make every item "fit".

### Check a menu against your needs

Which lunch items at Fountain (location 1) suit Riley, who avoids dairy and
wants at least 20 g of protein?

```bash
curl -X POST "http://localhost:8000/filters/locations/1/menus?date=2026-10-20" \
  -H "Content-Type: application/json" \
  -d '{"profiles": [{"name": "Riley", "avoid": ["dairy"], "min_protein_g": 20}]}'
```

Every item gets a verdict for each profile, with reasons when it isn't `fits`.
At lunch, 3 of 85 items fit Riley. Two of the items:

| Item | Verdict | Reasons |
|---|---|---|
| Chimichurri Chicken Thigh (23 g protein) | `fits` | none |
| Bananas (0 g protein) | `conflicts` | `protein 0g below 20g` |

The third verdict is `incomplete`: the data can't show the item is OK. For Sam
(vegan), the Chimichurri Chicken Thigh is `incomplete` with the reason `not
labeled vegan`. It isn't tagged vegan, and PackPlate never assumes an
untagged item is fine. Only `fits` means the available data matches the profile's requirements. It is not a guarantee of allergen safety.

### See what's open

```bash
curl "http://localhost:8000/locations?at=2026-10-14T12:30:00-04:00"
```

Each location has `is_open`, `closes_at`, `opens_next_at`, today's hours, and
its crowd level. `is_open: null` means the hours aren't published: unknown,
not closed. One location, a few fields shown:

```json
{"id": 3, "name": "Case Dining Hall", "is_open": true,
 "closes_at": "2026-10-14T13:30:00-04:00", "crowd": {"level": null, ...}}
```

For one location's next 7 days of hours and its menus, use
`/locations/{id}`. For a day's full menus with nutrition, use
`/locations/{id}/menus?date=YYYY-MM-DD`. An unknown id returns **404**.

### Check how fresh the data is

```bash
curl http://localhost:8000/freshness
```

```json
{"last_run_finished_at": "2026-10-18T23:54:39.815106Z", "last_run_status": "ok",
 "stale": false, "stale_after_hours": 36}
```

`stale` turns true when the last completed scrape is more than 36 hours old.

### Report how busy a place is

```bash
curl -X POST "http://localhost:8000/crowd/1" \
  -H "Content-Type: application/json" \
  -d '{"level": "moderate"}'
```

`level` is `not_busy`, `moderate`, or `crowded`. The answer (**201**) is the
location's new crowd level, worked out from the last 30 minutes of reports,
with newer ones counting more. Reporting the same location again within a
minute returns **429**. Nothing about you is stored.

This one wasn't run for this guide: it writes a real report into the shared
database. Try it against a local database instead
([INSTALL.md, option B](../../INSTALL.md)).

### Find meal recommendations

Which lunch options across campus are high in protein and match a
vegetarian diet?

```bash
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"goal": "high_protein", "meal": "lunch",
       "profile": {"diets": ["vegetarian"]}}'
```

The response contains up to 20 ranked recommendations, including dining
locations, meal periods, nutrition information, and recommendation reasons.

| Goal | Meaning |
|---|---|
| `high_protein` | Prioritize meals with more protein |
| `lower_calories` | Prioritize meals with fewer calories |
| `lower_sodium` | Prioritize meals with less sodium |

Omit `meal` to search all meal periods. Omit `date` to use the current
campus date.

### Use authenticated endpoints

Log in with an existing local test account and save the session cookie:

```bash
curl -c cookies.txt -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password1"}'
```

View the signed-in account:

```bash
curl -b cookies.txt http://localhost:8000/auth/me
```

Save and retrieve a dietary profile:

```bash
curl -b cookies.txt -X PUT "http://localhost:8000/profile" \
  -H "Content-Type: application/json" \
  -d '{"diets": ["vegetarian"], "min_protein_g": 20}'

curl -b cookies.txt http://localhost:8000/profile
```

Ask the dining assistant:

```bash
curl -b cookies.txt -X POST "http://localhost:8000/assistant/messages" \
  -H "Content-Type: application/json" \
  -d '{"text": "What dining halls are open right now?",
       "profile": {"diets": ["vegetarian"]}}'
```

The assistant uses the profile supplied in the request.

Log out and remove the cookie file:

```bash
curl -b cookies.txt -X POST "http://localhost:8000/auth/logout"
rm cookies.txt
```

Protected endpoints return **401** without a valid session.
The assistant returns **404** if disabled.

Use a local test account and database for requests that modify stored
data. Do not commit cookie files.

## For developers

Run these from `proj_3/` with the virtual environment active.
[CONTRIBUTING.md](../../CONTRIBUTING.md) covers setup, tests, and checkers.

### Reproduce the M0 eval

```bash
python -m eval.m0            # print the results and write eval/results.json
python -m eval.m0 --check    # compare with the committed results instead
```

It needs no database: it reads the frozen snapshot in `eval/data/`. The
plan, method, and limits are in [m0-eval.md](Project%202%20docs/m0-eval.md).

Loop 2, the re-test after the fixes, is separate and runs the same way:

```bash
python -m eval_loop2.m0            # print the results and write eval_loop2/results.json
python -m eval_loop2.m0 --check    # compare with the committed results instead
```

It reads its own snapshot and hand-check sheet in `eval_loop2/data/`.

### Reproduce the Project 3 M0 eval

Project 3 adds a separate evaluation of account and chat reliability
and privacy. It checks six authorized collaboration journeys and
21 unauthorized access attempts.

Follow the disposable PostgreSQL setup instructions in
[m0-eval-project3.md](m0-eval-project3.md). Once the database is
running and `M0_DATABASE_URL` is configured, run from `proj_3/`:

```bash
python eval_project3/m0.py --check
```

The original evaluation completed all six authorized journeys and
allowed zero unauthorized reads or writes across 21 attempts.

This evaluation uses synthetic accounts and a local database, not
the team's shared database. Passing does not establish security
under every possible scenario.

### Change a filter rule safely

The rules that decide `fits`, `conflicts`, and `incomplete` are at the top of
`backend/app/services/filter_engine.py`. They decide what a student with an
allergy is told, so after changing one:

1. **Run the tests.** `cd backend && pytest` has a test for every rule. Add one
   for your change.
2. **Rerun M0.** `python -m eval.m0 --check` (back in `proj_3/`) fails if your
   change moved the M0 numbers. If that's intended, run `python -m eval.m0`
   and commit the new `eval/results.json` with your change, so the results
   always match the code. Do the same for loop 2 with `eval_loop2.m0` and
   `eval_loop2/results.json`. If a change moves loop 2's sample, its
   `--check` refuses the old hand-check sheet: the 50 rows have to be drawn
   and judged again.
3. **Update the docs** if you changed a docstring or the API (below).

### Run the scraper

The team's shared database is filled by one teammate, so don't run the
scraper against it. On a local database ([INSTALL.md, option
B](../../INSTALL.md)):

```bash
python -m ingestion.run --units 1 --days 1 --no-nutrition   # quick: Fountain, today
python -m ingestion.run                                     # everything: 24 units, 7 days
```

NC State Dining allows scraping at most once or twice a day. All the options
are in [proj_3/README.md](../README.md).

### Update the generated docs

[reference.md](reference.md) and [api.md](api.md) are generated from the code.
After changing a docstring, a function signature, or an API route:

```bash
python docs/generate.py
```

and commit the result. CI fails if they're out of date.
