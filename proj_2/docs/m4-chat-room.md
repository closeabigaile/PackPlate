# M4 — Group chat rooms

**Status (2026-11-24):** backend and frontend implemented and merged into
`dev`. Includes saved rooms, invitations, messages, Open to Chat, M1 account
integration, and backend tests. Browser validation is listed separately below.

## Goal

Let students make dining plans together inside PackPlate. A signed-in student
can find other users, invite them to a room, and exchange messages once someone
accepts. Joining is a choice: an invitation does not make someone a member.

## What was completed

### Rooms and invitations

- A student can create a room and invite one or several other accounts.
  The creator joins immediately; everyone else gets a pending invitation.
- Invitees can accept or decline. Only accepted invitations add members.
- Duplicate invitee IDs are removed. Empty invite lists, self-invitations,
  and unknown accounts are rejected.
- Students see their joined rooms and their own pending invitations.
  They cannot respond to someone else's invitation.
- Members can leave a room. Leaving removes access to its messages and
  updates the room's status.

### Room rules

The rules live in
[`backend/app/services/chat_room.py`](../backend/app/services/chat_room.py).

| Status     | Members                                     | What members can do                                              |
| ---------- | ------------------------------------------- | ---------------------------------------------------------------- |
| `pending`  | Only the creator; invitations do not count  | Wait for an acceptance or leave; sending is disabled             |
| `active`   | At least two joined members                 | Read history, send messages, or leave                            |
| `inactive` | Fewer than two members after someone leaves | Remaining members can read history or leave; sending is disabled |

The first acceptance makes a room active. If someone leaves and at least two
members remain, it stays active. Otherwise it becomes inactive and any pending
invitations are cancelled, so they cannot reopen it. Declining an invitation
does not change the room's status. Accepting an already accepted invitation
does not add the same member twice.

### Messages

- Messages are saved in Postgres and returned in order by timestamp, then ID.
- Only joined members can read history; only members of an active room can
  send. Pending invitees and people who have left have no access.
- The sender comes from the signed-in account. The request contains only
  `text`; supplying a sender ID is rejected.
- Empty or whitespace-only messages are rejected.
- The backend assigns a timezone-aware timestamp and returns it in UTC.
  The frontend displays it in the reader's local time.

### Finding people and Open to Chat

- Students can find another account by exact username, ignoring case, and
  select it when creating a room.
- Open to Chat is off by default. Turning it on adds the account to the
  discovery list shown to other signed-in students.
- The list excludes the current user and is sorted by username.
- Turning it off removes the account from that list. People who know the
  exact username can still find and invite the account.
- The chat page and account page use the same saved preference.

### Frontend

The [`/chat` page](../frontend/src/app/chat/page.tsx) includes a room list with
status labels, pending invitations with Accept and Decline buttons, room
creation by username or the Open to Chat list, and a conversation view with
message history, a composer, and a Leave room button.

Signed-out visitors see links to log in or sign up. Loading, empty, and error
states are shown, with retry controls for failed reads. Pending and inactive
rooms explain why sending is unavailable. A failed send keeps the draft.
Switching accounts resets the workspace so rooms and drafts stay separate.

The room list, invitations, discovery list, and selected room's messages are
refreshed by polling, with a five-second delay after each request finishes.
The conversation scrolls to new messages when the reader is near the bottom.

## Accounts and saved data

M4 uses [M1's accounts and session cookie](m1-accounts.md). Every `/chat` route
requires a login and uses `users.id` for membership, invitations, and senders.

| Table               | Stores                                                                 |
| ------------------- | ---------------------------------------------------------------------- |
| `chat_rooms`        | Room ID and status                                                     |
| `chat_room_members` | Joined account IDs, unique within each room                            |
| `chat_invitations`  | Invitee, room, and response: pending, accepted, declined, or cancelled |
| `chat_messages`     | Room, sender, text, and timestamp                                      |

The models are in [`db/chat_models.py`](../db/chat_models.py), with migration
[`0006_chat.py`](../db/migrations/versions/0006_chat.py), after M1's `0005`.
Routes handle requests, the service owns room rules, and the repository owns
database queries. Changes to an existing room use a database lock and commit
together so membership, invitations, and status stay consistent.

Deleting an account first leaves its rooms through the normal room rules.
Memberships and invitations are removed. Its messages remain for the other
members, with `sender_id: null`; the frontend labels these as "Deleted user".

## API

All routes below require a signed-in account (`401` otherwise). Full request
and response models are in the [HTTP API reference](api.md).

| Endpoint                                         | Purpose                                       |
| ------------------------------------------------ | --------------------------------------------- |
| `GET /chat/rooms`                                | List the current user's joined rooms          |
| `POST /chat/rooms`                               | Create a room with `{"invitee_ids": [...]}`   |
| `GET /chat/rooms/{room_id}`                      | Read a joined room's status and member IDs    |
| `POST /chat/rooms/{room_id}/leave`               | Leave the room                                |
| `GET /chat/invitations`                          | List the current user's pending invitations   |
| `POST /chat/invitations/{invitation_id}/accept`  | Accept and join                               |
| `POST /chat/invitations/{invitation_id}/decline` | Decline without joining                       |
| `GET /chat/rooms/{room_id}/messages`             | Read message history as a member              |
| `POST /chat/rooms/{room_id}/messages`            | Send `{"text": "..."}` in an active room      |
| `GET /chat/users/{username}`                     | Find another account by exact username        |
| `GET /chat/open-to-chat`                         | List other accounts that opted into discovery |
| `PUT /chat/open-to-chat`                         | Set `{"open_to_chat": true}` or `false`       |

Nonmembers and users acting on someone else's invitation receive `403`.
Missing rooms, invitations, or accounts return `404`. Sending in a pending or
inactive room returns `409`. Invalid request fields return `422`;
self-invitations and invalid username lookups return `400`.

## Evidence

The implementation includes automated tests in three files:

- [`test_chat_room.py`](../backend/tests/test_chat_room.py): membership,
  invitation responses, room status changes, repeated acceptance, and
  cancellation of invitations when a room becomes inactive.
- [`test_chat_room_api.py`](../backend/tests/test_chat_room_api.py): room
  creation, invalid and duplicate invitees, invitation ownership, access
  controls, messages, timestamps, invalid text, sender spoofing, inactive
  history, and Open to Chat changes.
- [`test_chat_accounts.py`](../backend/tests/test_chat_accounts.py): login
  requirements, sender identity, exact username lookup, discovery defaults,
  the shared account preference, and account deletion cleanup.

Run these from `proj_2/` with the backend dependencies installed:

```bash
cd backend
python -m pytest tests/test_chat_room.py tests/test_chat_room_api.py tests/test_chat_accounts.py
```

The API and account integration tests require `TEST_DATABASE_URL` pointing to
a disposable local Postgres database. The fixtures rebuild and empty it; see
[Contributing](../../CONTRIBUTING.md). Without that setting, database tests
skip locally; CI requires them to run.

## Checklist

- [x] Room rules for pending, active, and inactive rooms
- [x] Persistent rooms, memberships, invitations, and messages; migration 0006
- [x] Create rooms, accept or decline invitations, and leave rooms
- [x] Member-only history and active-room-only sending
- [x] M1 login integration and account deletion cleanup
- [x] Exact username lookup and Open to Chat discovery
- [x] `/chat` frontend connected to the API, including polling and error states
- [x] Backend unit, API, and account integration tests added
- [x] Backend and frontend merged into `dev`
- [x] Record a two-account browser walkthrough: invite, accept, exchange
      messages, leave, and confirm the remaining member's history is read-only
- [x] Record checks on phone and desktop layouts
- [x] Automated browser coverage of the chat flow

## Current limits

Updates use polling, so another person's messages can take a refresh cycle to
appear. History is returned in full; pagination and message editing or deletion
are not implemented. Sender names use usernames known to the current page,
with `Member #ID` as the fallback.
