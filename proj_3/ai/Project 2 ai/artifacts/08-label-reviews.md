# 08 — Review queue for contradicted diet tags

| | |
|---|---|
| **Author** | Morgan Simon |
| **Date** | 2026-10-19 |
| **Tool / model** | Claude Code (VS Code extension), Claude Opus 5.5 |

## 1. Request

PackPlate should not show an item as vegan or vegetarian when NC State's own
ingredient list names meat (issue #18). After #15 the filter already marked such
items `incomplete`, but the menu still showed NC State's tag.

## 2. AI proposal

Withhold contradicted diet tags automatically in the backend, using the diet
rules from #15, and return the reason with each item.

## 3. Human review

- **A person decides, not the scanner.** I asked for contradictions to be
  flagged for a developer to approve before any tag is removed. The design
  became a review queue: the scraper records each case as `pending`, and a
  command records approve or reject with who, when, and why.
- **Standard practice.** I asked how production apps handle corrections to
  third-party data. The AI compared a file in the repo with a database table;
  we chose a database-backed queue with an audit trail, the usual curation
  pattern, with a command standing in for an admin page.

## 4. Final version

On `feature/label-reviews`: migration `0004` adds `label_reviews`; the scraper
queues contradicted tags after each run and reports `label_reviews_pending`;
`ingestion.review_labels` lists and decides reviews; the menu and filter APIs
remove approved tags and return the reason in `diets_removed`. NC State's data
is stored unchanged. A decision is tied to the dish and a fingerprint of its
ingredient text, so a recipe change sends it back for review.

## 5. Verification

- `pytest ingestion backend eval`: 267 passed against Postgres 16, including
  tests that pending reviews keep NC State's tags and approved ones remove them
  from both the menu and the filter.
- A read-only preview on a week of real data queued 2 dishes, both genuine
  contradictions; the review command was tried end to end on a local database.

Human checks (tick what was actually done):

- [ ] Read the diff on `feature/label-reviews`
- [ ] Ran `pytest` locally
- [ ] Tried `python -m ingestion.review_labels`
