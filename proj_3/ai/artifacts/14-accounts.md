# 14 — User accounts, chat integration, and saved diets

|                  |                                   |
| ---------------- | --------------------------------- |
| **Author**       | Aditya                            |
| **Date**         | 2026-11-09 to 2026-11-16          |
| **Tool / model** | Claude Code, Claude Opus 5.5 (CLI) |

Written from the saved Claude Code session transcripts of 2026-11-09 and
2026-11-16.

## 1. Request

- **Accounts (Nov 9):** "Create user accounts. I think the actual accounts is
  gonna be easy, not sure about integrations, maybe look into that." With one
  constraint: **do not push to the remote.**
- **Chat's needs (Nov 9):** Abigail (M4) listed what group chat needed from
  accounts: a unique account ID, a unique username, and an Open to Chat
  setting that is off by default. I asked whether we could provide those
  without her code, then to pull her branch and check that both worked
  together, then to bring her work into our branch and make it work.
- **Saved diets (Nov 16):** Supreme (M5) wanted the dietary profile saved to
  user accounts, building on his branch.

## 2. AI proposal

**Accounts.** Build on the existing `M1User-accounts` branch:

- Store only a username and a password hash: no email, no real name.
- Hash passwords with the standard library's scrypt, so there is no new
  dependency.
- Sessions as a random token in an HttpOnly, SameSite=Lax cookie, with only
  the token's hash in the database, so logging out really ends the session.
- A login limiter against password guessing.
- `current_user` / `optional_user` dependencies for other features to use.
- Migration `0005`, unit and API tests, and login, signup and account pages.
- A doc (`docs/m1-accounts.md`) with an integration guide for teammates.

**Chat.** All three of Abigail's needs only depend on accounts: ID and
username already existed, so add an `open_to_chat` column (off by default), a
`PATCH /auth/me` to change it, and a checkbox on `/account`; leave the list of
people who are open to chat to her, since that's chat functionality.
Integration plan: fast-forward her two commits onto our branch so her history
and authorship stay intact, then wire her placeholder routes to the database
and to `current_user`, and add tests for how chat and accounts interact.

**Saved diets.** A `diet_profiles` table (one per account, deleted with it),
`GET` / `PUT` / `DELETE /profile`, and `lib/accountProfile.ts` to keep the
browser's copy and the account's copy in sync, so the pages that read the
profile don't change.

## 3. Human review

- **No push until coordinated.** I kept everything local on Nov 9. On Nov 16
  I had it pushed to my own branch, `M5_User_diet_data_intergrations`, not
  Supreme's, so I could coordinate with him before opening a PR.
- **Chat without waiting.** I chose to deliver Abigail's three asks
  (ID, username, Open to Chat) from the accounts side instead of waiting for
  her code.
- **Check before merging.** I asked for her pushed branch to be tested against
  our work in a scratch copy first. That found that her API tests expected an
  email and a bearer token, and that her chat tables weren't registered with
  Alembic, before anything touched our branch.
- **Keep her authorship.** Her commits were brought in as they were, and the
  integration went on top as our own change.
- **Privacy decision left to the team.** Saving diets to accounts reverses
  the earlier rule that the diet stays only in the browser. The AI flagged it
  as something to agree with Supreme rather than decide in code. Logged out,
  the diet still stays only in the browser.
- **No Docker.** Docker doesn't work on my machine, so testing used a local
  Postgres instead of the documented Docker setup.

## 4. Final version

- **Accounts:** commit `5f9deee`; merged into `dev` with M4 chat via PR #7.
- **Chat connected to accounts:** routes require a login, the sender is always
  the logged-in user, a deleted account's messages stay for others with
  `sender_id: null`, and deleting an account leaves its rooms through chat's
  own rules.
- **Saved diets:** commit `a700f75`, merged into `dev` via PR #10. Its
  migration became `0009` after M3's migrations landed first.

See [m1-accounts.md](../../docs/m1-accounts.md) for the design and the
integration guide.

## 5. Verification

- [x] Tests pass: on Nov 9, 144 backend tests plus 233 ingestion and eval
      tests, against a throwaway local Postgres. Two failures there were the
      database's local timezone (CI uses UTC) and passed with `PGTZ=UTC`.
- [x] Ran it manually: an end-to-end check of the cookie and CORS behavior
      against a running API (Nov 9).
- [x] Frontend lint, typecheck, and build passed (Nov 9).
- [ ] The 9 saved-diet tests could not run when `a700f75` was committed (no
      local database); the commit message says so.
- [x] Re-checked 2026-11-25: all 42 account tests (`test_auth.py`,
      `test_auth_api.py`, `test_chat_accounts.py`, `test_profile_api.py`)
      pass against a local Postgres.
