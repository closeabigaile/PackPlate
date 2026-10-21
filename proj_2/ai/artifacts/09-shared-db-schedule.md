# 09 — Shared database and daily scrape

| | |
|---|---|
| **Author** | Morgan Simon |
| **Date** | 2026-10-19 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

Give the team one shared database filled by the scraper, run the first full
scrape, and schedule it daily within NC State Dining's terms (issue #3).

## 2. AI proposal

A hosted Postgres database that the scraper and the API both point at through
`DATABASE_URL`, a daily GitHub Actions run, and alerts so a broken scraper is
noticed.

## 3. Human review

- **Permission first.** I got NC State Dining's permission before the full
  scrape. Their terms (public data only, at most once or twice a day, served
  from a cache) fit the scraper's design, so the schedule is one run a day.
- **Choosing a host.** I questioned the first suggestion (Neon) and compared
  options; we chose Supabase for its table browser.
- **Public alerts.** Alerts become GitHub issues in a public repo, so I chose
  review alerts that give a count only, while failure alerts include the run's
  errors.

## 4. Final version

On `feature/scheduled-scrape`: README sections on the permission and the shared
database; `ingestion.scrape_alerts` (failed or partial runs, stale data,
pending reviews); `.github/workflows/scrape.yml`, which runs daily at 4am
Eastern Standard Time and opens or updates one issue per kind of alert. The
schedule starts once `dev` is merged into `main` and the `SUPABASE_URL` secret
is set.

## 5. Verification

- First full scrape: 24 locations, 6,239 items, 0 errors, 1,699 requests; later
  daily runs about 370 requests.
- `pytest ingestion backend eval`: 257 passed, including 5 alert tests; the
  alerts returned none on the live database after a good run.
- The workflow's issue logic was dry-run in a Linux container with a stand-in
  `gh`. The scheduled run itself is untested until it is on `main`.

Human checks (tick what was actually done):

- [ ] Read the diff on `feature/scheduled-scrape`
- [ ] Ran the daily scrape by hand
- [ ] Added the `SUPABASE_URL` repo secret
