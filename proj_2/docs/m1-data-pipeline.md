# M1 — Data pipeline

**Status (2026-10-12):** built and merged into `dev` (ingestion job and read
API). Scheduling, monitoring, and dining-only locations are still open.

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

## Still to do

- [ ] **Scheduled scrape.** NC State Dining allows scraping at most once or
  twice a day. See `feature/scheduled-scrape`.
- [ ] **Monitoring.** Alert someone when a run fails or data goes stale. The
  architecture critique named an unnoticed scraper break as the most likely
  week-3 failure.
- [ ] **Dining-only locations.** Chick-fil-A, the markets, and others appear
  on dining.ncsu.edu but not NetNutrition, so they are missing.
- [ ] **Talley 1887 Bistro** has no matching hours page, so its hours are always
  unknown.

## Done when

- [ ] A scheduled run fills every location daily without anyone running it
- [ ] A failed or stale run is visible to the team without opening the database
- [ ] Every location on dining.ncsu.edu appears, even if it has no menu
