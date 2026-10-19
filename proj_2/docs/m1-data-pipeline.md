# M1 — Data pipeline

**Status (2026-10-18):** built and merged into `dev` (ingestion job and read
API). The shared Supabase database is up and the first full scrape ran
(issue #3). Scheduling, monitoring, and dining-only locations are still open.

## Goal

Answer "what can I eat right now?" from one place. Today that takes roughly
20 navigations across two NC State sites: hours on dining.ncsu.edu, menus and
nutrition on NetNutrition, which has no hours.

## What exists

- **Ingestion job** (`ingestion/`): fetch → parse → normalize → write.
  - Menus and nutrition labels from NetNutrition (24 units), hours from
    dining.ncsu.edu, up to 7 days ahead.
  - Polite by design: 1 request per second, sequential, identifying
    User-Agent, labels cached for 7 days.
  - Every run records an `ingest_runs` row (`ok` / `partial` / `failed`, with
    stats and errors). A failure at one location doesn't stop the run.
- **Shared schema** (`db/`): SQLAlchemy models plus Alembic migrations. Each
  table names its single writer.
- **Read API:**
  - `GET /locations`: hours, open now, closes at, opens next.
  - `GET /locations/{id}`: the same, plus a week of hours and upcoming menus.
  - `GET /locations/{id}/menus`: every menu for a day, with items, allergens,
    diets, and nutrition.
  - `GET /freshness`: when data was last scraped, and whether it is stale
    (older than 36 hours).
  - Unknown stays unknown: `is_open: null` and `nutrition: null` mean "not
    published", never closed or safe.
- **Tests:** 43 ingestion tests (offline parsing on captured pages, plus
  database tests) and the backend's read-API tests.

## Checklist

- [x] Ingestion job: fetch → parse → normalize → write, with `ingest_runs`
  records
- [x] Shared schema and Alembic migrations
- [x] Read API: `/locations`, `/locations/{id}`, `/locations/{id}/menus`,
  `/freshness`
- [x] Ingestion and read-API tests, run in CI against Postgres (see M3)
- [x] Shared team database on Supabase (issue #3)
- [x] First full scrape: 24 locations, 7 days, labels on; `ok`, 0 errors
  (2026-10-11)
- [ ] README scraping note updated with NC State's permission (PR #7 was
  closed without merging, so `dev` still says "do not schedule")
- [ ] **Scheduled scrape.** A run fills every location daily without anyone
  running it. NC State Dining allows at most once or twice a day.
- [ ] **Monitoring.** A failed or stale run is visible to the team without
  opening the database. The architecture critique named an unnoticed scraper
  break as the most likely week-3 failure.
- [x] AI-usage artifact for the database and scrape work (`ai/artifacts/`)
- [x] Database access shared with the team privately (not in the repo)
