# How to use PackPlate

Worked examples for the common tasks. Every example below was run against the
real API on 2026-10-19, using the team's shared database. Your numbers will
differ: menus change every day.

To follow along, install and start PackPlate first ([INSTALL.md](../../INSTALL.md)).
The API runs at `http://localhost:8000`, the website at `http://localhost:3000`.

## Contents

- Using the website
- Using the API:
  [find where a group can eat](#find-where-a-group-can-eat),
  [check a menu against your needs](#check-a-menu-against-your-needs),
  [see what's open](#see-whats-open),
  [check how fresh the data is](#check-how-fresh-the-data-is),
  [report how busy a place is](#report-how-busy-a-place-is)
- For developers:
  [reproduce the M0 eval](#reproduce-the-m0-eval),
  [change a filter rule safely](#change-a-filter-rule-safely),
  [run the scraper](#run-the-scraper),
  [update the generated docs](#update-the-generated-docs)

## Using the website

Open `http://localhost:3000`. The menu at the top has:

| Page | What it's for |
|---|---|
| **What's open** | Every location, and whether it's open right now |
| **Menus** | A location's menus for a day, with allergens, diets, and nutrition |
| **Eat as a group** | Add each person's needs with **Add a person**, then **Find a match** to see where everyone can eat |
| **How busy** | Each location's crowd level; tap a level to report how busy it is |
| **My diet** | Your own allergies and diets, saved in this browser only |

The website is still being built, so details may change.

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
untagged item is fine. Only `fits` means "you can eat this".

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

## For developers

Run these from `proj_2/` with the virtual environment active.
[CONTRIBUTING.md](../../CONTRIBUTING.md) covers setup, tests, and checkers.

### Reproduce the M0 eval

```bash
python -m eval.m0            # print the results and write eval/results.json
python -m eval.m0 --check    # compare with the committed results instead
```

It needs no database: it reads the frozen snapshot in `eval/data/`. The
plan, method, and limits are in [m0-eval.md](m0-eval.md).

### Change a filter rule safely

The rules that decide `fits`, `conflicts`, and `incomplete` are at the top of
`backend/app/services/filter_engine.py`. They decide what a student with an
allergy is told, so after changing one:

1. **Run the tests.** `cd backend && pytest` has a test for every rule. Add one
   for your change.
2. **Rerun M0.** `python -m eval.m0 --check` (back in `proj_2/`) fails if your
   change moved the M0 numbers. If that's intended, run `python -m eval.m0`
   and commit the new `eval/results.json` with your change, so the results
   always match the code.
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
are in [proj_2/README.md](../README.md).

### Update the generated docs

[reference.md](reference.md) and [api.md](api.md) are generated from the code.
After changing a docstring, a function signature, or an API route:

```bash
python docs/generate.py
```

and commit the result. CI fails if they're out of date.
