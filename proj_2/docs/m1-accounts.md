# M1 — User accounts and UI refresh

**Owner:** Aditya.

**Status (2026-11-25):** accounts merged into `dev` with M4 chat (PR #7);
saving diets to accounts merged with M5 (PR #10). The UI refresh is on
`Aditya/UI_improvements`. See [UI refresh](#ui-refresh) below.

## Goal

Two parts:

1. **Accounts.** Let students sign up, log in, and log out, so features that
   need to know who someone is (M4 group chat, M5 saved diets, M3's assistant)
   have accounts to build on.
2. **UI refresh.** Project 3 added five features to a site designed for
   three. Make the site look like one product again, put the new features
   where people can find them, and make the screens the demo relies on
   (menus, what's open) easier to read at a glance.

## What an account is

| Stored | Not stored |
|---|---|
| username (3–30 of `a-z 0-9 _`, case-insensitive, unique) | email, real name, student ID |
| scrypt hash of the password (salted, never the password) | anything about crowd reports |
| Open to Chat (off by default) | |
| when the account was made | |

Fewer fields means less to protect. The dietary profile is kept in its own
`diet_profiles` table (M5), only once a logged-in user saves one on My diet;
logged out, it stays in the browser as before. See "Saved diet" below.

## How sign-in works

- `POST /auth/register` or `/auth/login` sets a `packplate_session` cookie:
  a random 256-bit token, **HttpOnly** (page scripts, and so XSS, can't read
  it), **SameSite=Lax** (not sent on cross-site POSTs, so no CSRF), and
  **Secure** when `COOKIE_SECURE=1`.
- The database stores only the token's SHA-256 in `auth_sessions`. Logging out
  deletes the row, so the cookie is dead even if someone copied it. Sessions
  last `SESSION_DAYS` (30).
- Wrong username and wrong password give the same 401 and take the same time,
  so the login form doesn't reveal who has an account. After 10 failures for
  one username from one client in 15 minutes, logins are refused (429).
- Passwords use `hashlib.scrypt` from the standard library: no new
  dependency. The cost is stored in each hash and old hashes are upgraded on
  login if it's raised.
- Deleting an account needs the password, and deletes everything tied to it
  (`ON DELETE CASCADE`).

Everything that worked logged out still works logged out.

## Building on accounts (M4, M5, M3)

**Backend.** Require a login with one dependency:

```python
from app.deps import current_user, optional_user
from db.models import User

@router.get("/chat/rooms")
def my_rooms(user: User = Depends(current_user), db: Session = Depends(get_db)):
    ...  # 401 is automatic when logged out; user.id, user.username

@router.get("/something")
def either(user: User | None = Depends(optional_user)):
    ...  # None when logged out
```

**Database.** Your migration goes after this one: `down_revision = "0005"`
(and renumber if two features land at once: Alembic needs one head). Reference
`users.id` with `ondelete="CASCADE"` so account deletion cleans up, or
`SET NULL` for records other people still need (like chat messages). If your
feature's rows need cleanup rules beyond a cascade, call them from
`delete_me` in `api/auth.py` before the user is deleted, as chat does.

### M4 chat, connected

| Need | Provided by |
|---|---|

| A unique account ID for members, invites, and senders | `users.id` (`user.id` from `current_user`) |
| A unique username to find people and invite them | `users.username`, unique and lowercased |
| Open to Chat, off by default | `users.open_to_chat`. Chat's `PUT /chat/open-to-chat` and the `/account` checkbox (`PATCH /auth/me`) both set it; `GET /chat/open-to-chat` lists everyone else who has it on |
| Who is asking | every `/chat` route takes `current_user`; the sender of a message is always the logged-in user |

- Chat's tables (`db/chat_models.py`, migration `0006`) reference `users.id`.
  Memberships and invitations cascade; `chat_messages.sender_id` is
  `SET NULL`, so a deleted user's messages stay for the others as
  `sender_id: null`.
- Deleting an account first leaves each of its rooms through chat's normal
  rules (`chat_rooms.leave_all_rooms`). A plain cascade would leave an
  "active" room with one member, which the rules refuse to load, or a pending
  room with no creator.
- Open to Chat controls whether an account appears in the discovery list.
  A signed-in user who knows someone's exact username can still look them up
  and invite them by ID.

**Username lookup.** `GET /chat/users/{username}` returns the other account's
`id` and `username`. Use the ID in `POST /chat/rooms`. Usernames are
case-insensitive.

**Tests.** `client` in `backend/tests/conftest.py` keeps cookies between calls,
so register and you're logged in:

```python
client.post("/auth/register", json={"username": "alice", "password": "password1"})
client.get("/chat/rooms")  # as alice
```

For a second user, make a second `TestClient(app)` (same overrides apply).

**Frontend.** All `api.ts` calls already send the cookie
(`credentials: "include"`); add your calls to `api` or use the same
`request` pattern in your own file. For who's logged in:

```tsx
import { useSession } from "@/lib/session";
const session = useSession(); // "loading" | "signed_in" | "signed_out" | "unknown"
if (session.status === "signed_in") session.user.username;
```

Send logged-out users to `/login`.

## Deploying

- The frontend and API must be **same-site** for the cookie: `localhost:3000`
  with `localhost:8000` works; `localhost` with `127.0.0.1` doesn't. In
  production, serve them from one domain (e.g. `packplate.app` and
  `api.packplate.app`), with `FRONTEND_ORIGIN` set to the frontend's exact
  origin and `COOKIE_SECURE=1`.
- The login limiter is in memory, like the crowd throttle: fine for one API
  process, resets on restart.

## Saved diet (M5)

- `GET /profile` returns the logged-in user's profile (or `null`), `PUT
  /profile` saves one, `DELETE /profile` removes it. Same fields and limits as a
  filter request's profile, so a typo is a 422, not a profile that silently
  matches everything.
- `diet_profiles.user_id` references `users.id` with `ON DELETE CASCADE`:
  deleting the account deletes the diet (migration `0009`; it was `0007` on
  its own branch and was renumbered after M3's migrations merged first).
- The frontend still reads the profile from the browser (`useSavedProfile()`),
  so My diet, Menus, Compare Meals, and Eat as a group didn't change.
  `lib/accountProfile.ts` keeps that copy in sync:
  - on login, the account's profile replaces the browser's; if the account has
    none, a profile made while logged out is saved to it (never one that came
    from a different account);
  - saving or clearing on My diet while logged in changes the account first,
    then the browser;
  - logging out (in any tab) clears it from the browser, so the next person on
    a shared computer doesn't see it.

## UI refresh

The site worked, but every page was black text on grey in a stack of
identical white cards, the nav had ten equal links, and Home only showed the
five Project 2 features. Nothing about the backend changed: same API, same
`fits` / `conflicts` / `incomplete` rules, same data. All changes are in
`frontend/src`.

### Look and feel (every page)

- **NC State red used with intent.** A red stripe on the header, a red logo
  mark, red for the active page, primary buttons and selected chips. Colors
  stay as tokens in `app/globals.css`.
- **A heading font with character** (Bricolage Grotesque, via `next/font`) for
  titles and the logo; Geist stays for body text.
- **Line icons instead of emoji** (`components/Icon.tsx`, inline SVG from
  Lucide, no new package). Each page title has an icon tile.
- **Softer cards:** 1 px borders, larger radius, light shadows, hover states.
- **Dark footer** with the brand and the allergy disclaimer.
- **Sentence case everywhere** ("What's open", "Compare meals", "Find meals").
  Before, nav, titles and the Compare page each used a different style.
- **Data freshness as a chip** ("Hours and menus updated 1 hour ago") when the
  data is fresh. Stale, partial or missing data still gets the full warning
  banner, as `m4-web-app.md` requires.
- **Loading placeholders:** grey shimmering cards instead of "Loading…" text
  (`components/StateMessage.tsx`), with the words still read to screen
  readers, and no animation when the system asks for reduced motion.
- **Sticky header that actually sticks.** `html, body { overflow-x: hidden }`
  quietly turned `body` into a scroll box, so nothing sticky ever stuck. It's
  now `overflow-x: clip`, which still stops sideways scrolling.

### Navigation

- Six main links (What's open, Menus, Compare, Eat as a group, Group chat,
  Assistant) and a **More** menu (How busy, My diet, About). On phones, the menu
  button lists all of them. The More menu closes on Escape or an outside click.
- Signed in, the account link shows your username with a person icon.

### Pages

| Page | Before | Now |
|---|---|---|
| **Home** (`/home`) | Five colored cards with 3D emoji; Compare, Chat and Assistant missing | Red hero ("Where are you eating today?") with *See what's open* and *Ask the assistant*, a live "N of M locations open right now" line, and all eight features in two groups (*Find something to eat*, *Plan with friends*); new ones tagged **New** |
| **About** (`/`) | Three features | Six features with icons, matching hero |
| **What's open** | One long column; every unknown location had its own yellow pill | Three-column grid; each card has **today's hours as a bar** with a line at now, **"Closes in 40 min"** when closing is near, closing time in bold, buttons for *View menu* and *Dining page*. Filters: *All / Dining halls / Cafés and food courts* and an **Open now only** switch. Open places sorted by who closes first |
| **Menus** | Every location a collapsed row; opening one from What's open put it at the bottom of the page | **Two panes:** locations on the left (open / closed dot and "Until 8:00 PM"), the menu on the right. The location you came from is selected and scrolled into view. Meal tabs stay pinned while you scroll. On phones, the location list is a sideways-scrolling row |
| **Menu items** | One line of text per dish | Calories and protein under the name ("320 cal · 12 g protein"); vegan, vegetarian and halal with icons; opened, the nutrition label shows as **bars** (a missing value says "not listed" and has no bar). With a diet set, each meal starts with **"19 of 33 dishes fit your profile"** and a green / amber / red bar |
| **Compare** | Fields stacked full width; blank page before searching; plain table | Three fields in a row; a three-step **How it works** panel before searching; results as ranked cards with calories / protein / sodium tiles; the side-by-side comparison as paired **bars** with a legend |
| **How busy** | Listed unknown-hours places under "Open now" (so it disagreed with What's open); three big buttons per card | *Open now* and *Hours unknown* are separate. A **three-step crowd meter** says what it's based on ("predicted + 4 reports"); reporting is one compact segmented control |
| **Eat as a group** | Plain list of counts | Each person gets a **colored initials avatar**; every result card shows everyone's avatar with ✓ / ✕ and "Something for everyone" or "1 left out"; results in two columns |
| **My diet** | Form only | **Live preview:** "N of M dishes at Fountain fit this profile on Mon, Nov 30", updating as you edit (debounced), with a picker for the location. It skips holiday days that list only one dish |
| **Group chat, Assistant** (logged out) | One dashed "Log in" box | A preview of what the feature does, *Create an account* / *Log in*, and, for the assistant, example questions as chat bubbles |
| **Group chat** (logged in) | — | Your own messages as red bubbles on the right |

### New frontend files

| File | What it is |
|---|---|
| `components/Icon.tsx` | The icon set |
| `components/OpenNowStrip.tsx` | The live "open right now" line on Home |
| `components/SignInPrompt.tsx` | The logged-out preview for chat and the assistant |
| `components/HoursTimeline.tsx` | Today's hours as a bar |
| `components/NutritionBars.tsx` | Nutrition as bars (menu items and Compare) |
| `components/CrowdMeter.tsx` | The three-step crowd meter |
| `components/Avatar.tsx` | Initials avatars for Eat as a group |
| `components/DietPreview.tsx` | The live preview on My diet |
| `lib/clock.ts` | The current time for "closes in" and the hours bar, ticking every 30 s outside rendering |
| `lib/locationKind.ts` | Dining hall vs. café / food court (by name: NC State's data has no such field) |

### How it was checked

- `npm run lint`, `npm run typecheck`, `npm run format:check` and
  `npm run build` pass.
- Every page screenshotted at desktop and phone width, logged in and out,
  before and after, with a scripted Chrome (puppeteer) clicking through the
  interactive states: a diet set, two meals compared, a group searched, a
  chat message sent, assistant questions asked. No page errors.
- The old UI was kept running side by side (tag `ui-baseline`) to compare
  A/B before committing.

## Testing

Account tests are in `backend/tests/`; all 42 pass against a local Postgres:

| File | Tests | Covers |
|---|---|---|
| `test_auth.py` | 9 | Unit: a hash verifies only the right password, is salted, malformed hashes never verify, rehash when the cost changes; username and password rules; tokens are random and stored hashed; the login limiter blocks, recovers, and forgets after a success |
| `test_auth_api.py` | 13 | Register stores only a hash; bad input and duplicate usernames (ignoring case) are refused; logout revokes the session on the server; a new login replaces the old session; expired and forged sessions are rejected; too many failed logins; delete account; Open to Chat; other features can require a login; everything that worked logged out still does |
| `test_chat_accounts.py` | 11 | Chat on accounts: the sender is always the logged-in user; every chat route needs a login; no inviting yourself; invite by exact username; Open to Chat is off by default and matches the account page; deleting an account keeps its messages for others, removes its invitations, closes the room for the remaining members, and cancels the pending invitations it sent |
| `test_profile_api.py` | 9 | Saved diets: 401 logged out; none until saved; save, read back, replace, delete; rejects what a filter request would; works as a filter profile; each account sees only its own; deleted with the account |

The UI refresh has no automated tests (the frontend has none); it was
checked as described in [How it was checked](#how-it-was-checked).

## Not done (on purpose)

- Password reset: there's no email to send a link to. A user who forgets
  their password makes a new account.
- Changing username or password.
- Dark mode: the colors are tokens, so it's mostly one CSS block, but it
  wasn't needed for the demo.

## Limitations

- The login limiter lives in memory: one API process only, and it resets on
  restart.
- "Dining hall" vs. "café" is decided by the location's name.
- The hours bar shows 6 am to midnight; anything open past midnight is drawn
  to the end of the bar.

## Checklist

- [x] Account requirements and design (this doc)
- [x] `users` and `auth_sessions` tables, migration 0005
- [x] Register, login, logout, who-am-I, delete account
- [x] Open to Chat setting (off by default) for M4
- [x] `current_user` / `optional_user` for other features
- [x] Login, signup, and account pages; header shows Log in or your username
- [x] Tests: hashing, rules, limiter (unit); every route and the cookie (API)
- [x] Diets saved to accounts for M5 (`/profile`, migration 0009)
- [x] UI refresh: navigation, Home, every page above
- [x] UI checked with lint, typecheck, build, and screenshots of every page
- [ ] Tried in a browser by a teammate against the shared database
