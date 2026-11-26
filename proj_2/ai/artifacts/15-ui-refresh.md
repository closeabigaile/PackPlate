# 15 — UI refresh and demo videos

|                  |                                   |
| ---------------- | --------------------------------- |
| **Author**       | Aditya                            |
| **Date**         | 2026-11-25                        |
| **Tool / model** | Claude Code, Claude Opus 5.5 (CLI) |

## 1. Request

- Pull the merged Project 3 work and get it running locally without Docker.
- "The UI as is looks quite boring": a list of problems, tiered by relevance.
- Implement the changes while keeping the old UI as a backup, so the two can
  be compared A/B.
- More ideas for the pages beyond Home, then build the ones I picked.
- For the video: pretend it's a day with real data (it's Thanksgiving break),
  add sample data so every feature shows, and record the walk-through and
  teaser.

## 2. AI proposal

- **Audit:** screenshot every page at desktop and phone width with headless
  Chrome, then a tiered list. Top tier: no visual identity; Home clashing
  and missing Compare, Chat and Assistant; a ten-link nav; Menus being a plain
  list; empty logged-out pages for Chat and Assistant. Second tier:
  inconsistent capitalization, Compare styled differently from the rest, How
  busy contradicting What's open, repeated badges, a freshness bar that looked
  like an error.
- **A/B setup:** the old UI as a separate git worktree (tag `ui-baseline`) on
  port 3001 with its own API process, the new one on port 3000, both on the
  same database.
- **Round 2 ideas:** two-pane Menus with pinned meal tabs; a What's open grid
  with an hours bar and filters; richer dishes (diet icons, nutrition bars, a
  "fits your profile" summary); group avatars; a Compare explainer and bar
  comparison; a crowd meter; loading placeholders; a live preview on My diet;
  dark mode; toasts.
- **Demo:** a `DEMO_NOW` clock override (backend and frontend) starting
  Monday 11/30 at 12:45, real NC State labels for that day, and seeded crowd
  reports, accounts and chat; videos recorded by a script driving Chrome.

## 3. Human review

- **Background color:** I rejected the new off-white page background; it
  went back to the original grey.
- **Scope of round 2:** I picked ideas 1–8 and left out dark mode and toasts.
- **Kept the old UI runnable** until I'd compared both, then committed it
  myself.
- **AI corrections caught during review:**
  - The first attempt at the Menus toggle shortened "Hide items that don't
    fit (items that need a check stay visible)" and lost the safety note; it
    was restored.
  - A screenshot showed the My diet preview picking Thanksgiving (one dish);
    it now skips near-empty days.
  - Screenshots showed nothing sticky worked: `overflow-x: hidden` on
    `html, body` had broken the header since before this work. Changed to
    `clip`.
  - The doc's test descriptions were checked against the real test names,
    and two claims with no test behind them were removed.
- **Assistant:** I asked why its answers were so fast. They're rule-based
  templates (no LLM writes them); the optional local model only classifies,
  and wasn't running.
- **Demo data stays local and is to be disclosed:** the demo clock and sample
  data (crowd reports, accounts, chat) exist only in my local database, and
  the narration should say the clock is set to a Monday.

## 4. Final version

- UI refresh: commit `19a3542` on `Aditya/UI_improvements` (frontend only, no
  API changes). The full list of changes is in
  [m1-accounts.md, "UI refresh"](../../docs/m1-accounts.md#ui-refresh).
- Demo videos: a 4:16 walk-through and a 26-second teaser, recorded by
  script, so retakes are identical.
- Not part of the UI commit: the `DEMO_NOW` clock, which only exists to record
  the videos.

## 5. Verification

- [x] Tests pass: frontend lint, typecheck, Prettier and `next build`; 389/389
      backend, 85/85 ingestion and 110/110 eval tests (backend run against a
      local Postgres set to UTC, matching CI).
- [x] Ran it manually: every page screenshotted at desktop and phone width,
      logged in and out, before and after, plus scripted runs through the
      interactive states (diet set, meals compared, group searched, chat
      message sent, assistant questions asked) with no page errors.
- [x] A/B compared against the old UI running side by side.
