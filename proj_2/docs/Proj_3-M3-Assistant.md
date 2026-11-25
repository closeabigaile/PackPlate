# Project 3, M3 — Dining assistant

**Status (2026-11-25):** done on `Demaris/M3_implementation`: backend,
migrations, frontend page, and tests (196 assistant tests and 10 startup
tests). Some known gaps are listed under "Not done".

## Goal

Let a signed-in student ask PackPlate a question in plain words and get an
answer built only from PackPlate's own data: menus, diets, hours, crowds, and
which dining hall is close. The assistant must never make up a fact and never
tell someone a food is safe.

It lives at `/assistant` and is private to each account.

## What it can answer

| Kind of question | Example |
|---|---|
| Menu | "What's for dinner at Fountain tonight?" |
| Diet and nutrition | "Vegan, high-protein options at Case", "Dairy-free lunch under 600 calories" |
| Hours | "What's open right now?", "When does Clark close tonight?", "What's open tomorrow?" |
| Crowd | "Is Fountain busy right now?" |
| Recommendation | "Which dining hall do you recommend?", "Where can I eat right now?" |
| How many | "How many dining halls are there?" |
| Closest hall | "I'm at Hunt Library, which dining hall is closest?" |

Medical questions ("is this safe for my diabetes?") get a fixed refusal. Words
that claim safety are never used. Food answers say **"fits your filters"** and
carry the warning **"Labels can be wrong; check ingredients."**

A student's saved diet applies to every question. A restriction typed into a
message is added for that question only and can never loosen a saved one. The
diet is not stored by the assistant.

## How a message is answered

```
message
  → rules read it                  intents.py     kind, place, meal, day, diet
  → follow-up carry-over           chat.py        "what about tomorrow?" reuses the last place
  → optional model classifies      llm.py         only if the rules could not tell
  → read-only lookup               tools.py       the facts, from the database
  → fixed template                 answers.py     every word of the reply
  → checker                        validate.py    the reply may say only what the lookup said
  → reply, or a plain fallback
```

- **The rules go first.** Most questions are understood without any model.
- **The model never writes the reply.** The optional local model
  (Ollama, `qwen2.5:1.5b`) only picks the kind of question and the place. Its
  answer is checked against the known locations and meals. If it is off or
  returns nonsense, the rules alone are used.
- **The tools only read.** They call the same menu, filter, hours, and crowd
  code the rest of the app uses, so the assistant and the website agree.
- **The checker is the safety net.** Every number, time, dish, and place in a
  reply must appear in the lookup result. The words "safe", "guarantee",
  "allergy-free", and "risk-free" are banned. A reply that fails the check is
  replaced by a plain fallback.

## Which dining hall is close

A student types where they are. The browser's location is never requested and
nothing the student types is stored.

1. **Campus places.** About 57 spots (halls, libraries, residence halls) with
   aliases in `campus_places.json`.
2. **Online lookup.** If the place is not on the list, OpenStreetMap Nominatim
   is asked: the campus area first, then the Raleigh–Durham–Cary area. It is
   cached and kept to one request a second.
3. **Not found.** The assistant says so and asks where the student is.

Dining hall positions are in the `location_points` table, kept apart from the
scraper's `locations` table. `seed_location_points.py` adds any that are
missing the first time the assistant needs them.

Distance is straight-line (haversine). Walking time is the distance × 1.25 ÷
80 m per minute, and replies call it a rough estimate. Beyond 3 km from every
hall the reply gives miles, and the public OSRM server gives a driving time
("about 18 mi, 27 min by car") when it is reachable.

Ranking is open places first, then (with a diet) places with food that fits,
then the nearest. Outlets in the same building (within 75 m) count once.

## Optional services

All three are free, need no account, and are on by default. Each falls back
safely when it is off or unreachable.

| Setting | Does | Without it |
|---|---|---|
| `ASSISTANT_LLM_ENABLED` | Local model classifies the question | Rules only |
| `ASSISTANT_GEOCODE_ENABLED` | Looks up typed places not on the campus list | Only listed places are found |
| `ASSISTANT_ROUTING_ENABLED` | Driving distance to far places | Straight-line miles |

Other settings: `ASSISTANT_ENABLED` (routes return 404 when `false`),
`ASSISTANT_RATE_PER_MINUTE` (10), `ASSISTANT_MAX_MESSAGE_CHARS` (500),
`ASSISTANT_HISTORY_LIMIT` (200), and the three `*_URL` settings. See
`.env.example`.

## Data

| Table | Holds | Migration |
|---|---|---|
| `assistant_messages` | Each account's own chat history, capped at 200 | `0007_assistant` |
| `location_points` | Latitude and longitude of each dining location | `0008_location_points` |

Migrations run by themselves when the API starts on a local database
(`app/startup.py`). It never migrates a hosted database such as Supabase: run
`alembic -c db/alembic.ini upgrade head` once there. `MIGRATE_ON_START=false`
turns it off.

## API

All routes need a login (401 otherwise). Details are in [api.md](api.md).

| Route | Does |
|---|---|
| `POST /assistant/messages` | Ask a question, get the reply (201). 422 for an empty or too long message, 429 after 10 a minute. |
| `GET /assistant/messages` | The account's saved history |
| `DELETE /assistant/messages` | Clear it (204) |

The website page is `frontend/src/app/assistant/`.

## Tests

| File | Covers |
|---|---|
| `test_assistant_intents.py` | Reading questions, places, meals, diets |
| `test_assistant_chat.py` | The whole flow, follow-ups, refusals |
| `test_assistant_tools.py` | The lookups, including nearest-hall ranking |
| `test_assistant_validate.py` | The checker rejects invented facts |
| `test_assistant_llm.py` | The model layer and its fallback |
| `test_assistant_geocode.py`, `test_assistant_routing.py` | The online services, cached and failing |
| `test_assistant_places.py`, `test_assistant_points.py` | Campus list and stored positions |
| `test_assistant_api.py` | Login, limits, history |
| `test_startup.py` | Migrating on start |

No test calls an outside service: a fixture in `conftest.py` turns all three
off and `MIGRATE_ON_START` off.

## Not done (on purpose or not yet)

- **A closed hall can hide the closest one.** Open places rank first, so at
  Hunt Library the 3-minute-away On the Oval is left out when it is closed and
  a hall 28 minutes away is shown. Showing the closest hall and the nearest
  open one is not built.
- **A bare follow-up is not understood.** "What about oval?" after a distance
  question gets the "I didn't understand" reply, because only food, hours, and
  crowd questions carry their place forward.
- **Misspelled multi-word places** ("Dubney Hall") are not corrected.
- **A food question with no place** does not search every hall.
- **Cafés with no menu** are left out of "what's open" answers.
- **Coordinates** have not all been checked on a map, and Wolves' Den has none.
- **Docker** has not been tested with the assistant.
- **The shared Supabase database** needs migrations 0007 and 0008 run by a
  person.
- **Walking times** are estimates from straight-line distance, not routes.

s