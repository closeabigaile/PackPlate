"""Evaluate Project 3's accounts and private chat using synthetic users.

Run from proj_2/: python eval_project3/m0.py [--check].
M0_DATABASE_URL must name the local packplate_m0_project3 test database.
"""

# The eval stays here so I do not need to change anyone else's feature files.
# Imports below the path setup are intentional: app lives in backend/.
# ruff: noqa: E402

import argparse
import hashlib
import json
import os
import sys
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, make_url, select, text, update

from app.api.auth import get_login_limiter
from app.deps import get_db
from app.main import app
from app.repositories import chat_rooms
from app.services.auth import SESSION_COOKIE, LoginLimiter, token_hash
from db.chat_models import ChatMessage
from db.migrate import upgrade
from db.models import AuthSession, Base
from db.session import make_session_factory, sqlalchemy_url

HERE = Path(__file__).resolve().parent
SCENARIOS = HERE / "scenarios.json"
RESULTS = HERE / "results.json"
PASSWORD = "PackPlate-M0-Test-123!"  # Fictional accounts only.
AUTHORIZED_IDS = {
    "round_trip",
    "separate_rooms",
    "leave_active",
    "leave_inactive",
    "delete_active",
    "delete_inactive",
}
DENIED_IDS = {
    "outsider",
    "invited",
    "declined",
    "former_member",
    "missing_session",
    "invalid_session",
    "expired_session",
    "logged_out_session",
    "deleted_account",
    "pending_room",
    "inactive_room",
    "spoofed_sender",
}


class CaseFailure(Exception):
    """A journey did not behave as the frozen scenario requires."""


def need(condition, message):
    """Stop this case with a useful explanation when a check fails."""
    if not condition:
        raise CaseFailure(message)


def load_scenarios():
    """Read the fixed cases and refuse missing, repeated, or unknown categories."""
    data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    for key, expected in (("authorized", AUTHORIZED_IDS), ("denied", DENIED_IDS)):
        ids = [case["id"] for case in data[key]]
        need(len(ids) == len(set(ids)) and set(ids) == expected, f"invalid {key} cases")
    need(
        data["thresholds"]
        == {
            "authorized_completion_rate": 1.0,
            "unauthorized_accesses": 0,
        },
        "the claim's thresholds changed",
    )
    need(
        sum(len(case["operations"]) for case in data["denied"]) == 21,
        "expected 21 denied attempts",
    )
    for case in data["denied"]:
        expected_ops = (
            ["write"]
            if case["id"]
            in {
                "pending_room",
                "inactive_room",
                "spoofed_sender",
            }
            else ["read", "write"]
        )
        expected_status = (
            409
            if case["id"] in {"pending_room", "inactive_room"}
            else (
                422
                if case["id"] == "spoofed_sender"
                else (
                    401
                    if case["id"]
                    in {
                        "missing_session",
                        "invalid_session",
                        "expired_session",
                        "logged_out_session",
                        "deleted_account",
                    }
                    else 403
                )
            )
        )
        need(
            case["operations"] == expected_ops and case["status"] == expected_status,
            f"unexpected permission reference for {case['id']}",
        )
    return data


@contextmanager
def test_database():
    """Migrate a private temporary schema, then remove only that schema."""
    raw = os.getenv("M0_DATABASE_URL")
    if not raw:
        raise CaseFailure("set M0_DATABASE_URL to the disposable local M0 database")
    url = make_url(sqlalchemy_url(raw))
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or url.database != "packplate_m0_project3"
    ):
        raise CaseFailure("M0_DATABASE_URL must name local packplate_m0_project3")
    schema = "m0_" + uuid4().hex
    admin = create_engine(url, connect_args={"connect_timeout": 3})
    engine = None
    created = False
    try:
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        created = True
        engine = create_engine(
            url,
            connect_args={
                "connect_timeout": 3,
                "options": f"-csearch_path={schema}",
            },
        )
        with engine.begin() as connection:
            upgrade(connection)
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with admin.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


class Journey:
    """Three fictional students using the real API and their own cookies."""

    def __init__(self, engine, client):
        self.sessions = make_session_factory(engine)
        self.client = client
        self.users = {}
        self.tokens = {}

    def request(self, actor, method, path, status=None, body=None):
        """Send only this user's cookie, without sharing the client's cookie jar."""
        self.client.cookies.clear()
        headers = {}
        if actor is not None:
            headers["Cookie"] = f"{SESSION_COOKIE}={self.tokens[actor]}"
        response = self.client.request(method, path, headers=headers, json=body)
        if status is not None:
            need(
                response.status_code == status,
                f"{method} {path}: expected {status}, got {response.status_code}",
            )
        return response

    def register_users(self):
        """Register through the API rather than inserting already-signed-in users."""
        for actor in ("alice", "bob", "charlie"):
            response = self.request(
                None,
                "POST",
                "/auth/register",
                201,
                {
                    "username": f"m0_{actor}",
                    "password": PASSWORD,
                },
            )
            self.users[actor] = response.json()["id"]
            self.tokens[actor] = response.cookies[SESSION_COOKIE]
            me = self.request(actor, "GET", "/auth/me", 200).json()
            need(me["id"] == self.users[actor], "session belongs to the wrong user")

    def create_room(self, invitees):
        """Create a room as Alice and check its starting membership."""
        room = self.request(
            "alice",
            "POST",
            "/chat/rooms",
            201,
            {
                "invitee_ids": [self.users[actor] for actor in invitees],
            },
        ).json()
        need(
            room["status"] == "pending" and room["member_ids"] == [self.users["alice"]],
            "room did not start pending with only its creator",
        )
        return room["id"]

    def invitation(self, actor, room):
        """Find the invitation for this room in the invited user's own list."""
        invitations = self.request(actor, "GET", "/chat/invitations", 200).json()
        matching = [item for item in invitations if item["room_id"] == room]
        need(len(matching) == 1, "expected exactly one invitation for this room")
        return matching[0]["id"]

    def join(self, actor, room):
        """Accept the actual invitation and check that membership becomes active."""
        invitation = self.invitation(actor, room)
        joined = self.request(
            actor, "POST", f"/chat/invitations/{invitation}/accept", 200
        ).json()
        need(
            joined["status"] == "active" and self.users[actor] in joined["member_ids"],
            "accepting the invitation did not join the active room",
        )

    def active_room(self, three=False):
        """Create a two- or three-person group through the invitation workflow."""
        invitees = ["bob", "charlie"] if three else ["bob"]
        room = self.create_room(invitees)
        for actor in invitees:
            self.join(actor, room)
        return room

    def message_rows(self):
        """Read stored effects independently of the API's permission checks."""
        with self.sessions() as session:
            return [
                tuple(row)
                for row in session.execute(
                    select(
                        ChatMessage.id,
                        ChatMessage.room_id,
                        ChatMessage.sender_id,
                        ChatMessage.text,
                    ).order_by(ChatMessage.id)
                )
            ]

    def send(self, actor, room, message):
        """Check the returned sender and the message actually saved in the room."""
        saved = self.request(
            actor, "POST", f"/chat/rooms/{room}/messages", 201, {"text": message}
        ).json()
        expected = (saved["id"], room, self.users[actor], message)
        need(
            saved["sender_id"] == self.users[actor]
            and saved["text"] == message
            and expected in self.message_rows(),
            "wrong sender, room, or stored message",
        )

    def history(self, actor, room, expected):
        """Compare the complete history with our independently specified messages."""
        rows = self.request(actor, "GET", f"/chat/rooms/{room}/messages", 200).json()
        need(
            [(row["sender_id"], row["text"]) for row in rows] == expected,
            "history has missing, extra, or incorrectly attributed messages",
        )
        need(
            all(datetime.fromisoformat(row["created_at"]).tzinfo for row in rows),
            "message time is missing its time zone",
        )

    def finish_membership(self, actor, room, delete=False):
        """Leave normally, or delete the account using its real password."""
        if delete:
            self.request(actor, "DELETE", "/auth/me", 204, {"password": PASSWORD})
        else:
            self.request(actor, "POST", f"/chat/rooms/{room}/leave", 204)

    def authorized(self, case_id):
        """Complete one of the six declared journeys without guessing its outcome."""
        if case_id == "separate_rooms":
            rooms = [self.active_room(), self.create_room(["charlie"])]
            self.join("charlie", rooms[1])
            for room, actor, message in zip(
                rooms,
                ["bob", "charlie"],
                ["Fountain at noon.", "Case at six."],
                strict=True,
            ):
                self.send(actor, room, message)
                self.history("alice", room, [(self.users[actor], message)])
                self.history(actor, room, [(self.users[actor], message)])
                listed = self.request(actor, "GET", "/chat/rooms", 200).json()
                need(
                    [item["id"] for item in listed] == [room],
                    "a user's room list contains the wrong group",
                )
            return
        three = case_id.endswith("active") and not case_id.endswith("inactive")
        room = self.active_room(three=three)
        self.send("alice", room, "Fountain at noon?")
        self.send("bob", room, "Noon works for me.")
        expected = [
            (self.users["alice"], "Fountain at noon?"),
            (self.users["bob"], "Noon works for me."),
        ]
        if case_id == "round_trip":
            self.history("alice", room, expected)
            self.history("bob", room, expected)
            old_token = self.tokens["bob"]
            self.request("bob", "POST", "/auth/logout", 204)
            login = self.request(
                None,
                "POST",
                "/auth/login",
                200,
                {
                    "username": "m0_bob",
                    "password": PASSWORD,
                },
            )
            self.tokens["bob"] = login.cookies[SESSION_COOKIE]
            need(self.tokens["bob"] != old_token, "login reused a logged-out session")
            need(
                login.json()["id"] == self.users["bob"],
                "login returned another account",
            )
            self.history("bob", room, expected)
            return
        delete = case_id.startswith("delete")
        self.finish_membership("bob", room, delete=delete)
        state = self.request("alice", "GET", f"/chat/rooms/{room}", 200).json()
        members = [self.users["alice"]] + ([self.users["charlie"]] if three else [])
        need(
            state["status"] == ("active" if three else "inactive")
            and sorted(state["member_ids"]) == sorted(members),
            "leaving or deletion left the wrong room state or members",
        )
        if delete:
            expected[1] = (None, expected[1][1])
        self.history("alice", room, expected)
        if three:
            self.history("charlie", room, expected)
            self.send("charlie", room, "We can still meet.")
            self.history(
                "alice",
                room,
                expected + [(self.users["charlie"], "We can still meet.")],
            )

    def denied_setup(self, case_id):
        """Set the declared role or session state without using permission helpers."""
        if case_id == "pending_room":
            room = self.create_room(["bob"])
            self.history("alice", room, [])
            return "alice", room
        room = self.active_room()
        self.send("alice", room, "Private plan: Fountain at noon.")
        actor = "charlie" if case_id in {"outsider", "invited", "declined"} else "bob"
        if case_id in {"invited", "declined"}:
            # Charlie is invited to this second room but has not joined it.
            room = self.create_room(["bob", "charlie"])
            self.join("bob", room)
            self.send("alice", room, "Private plan: Case at six.")
            if case_id == "declined":
                invitation = self.invitation("charlie", room)
                self.request(
                    "charlie", "POST", f"/chat/invitations/{invitation}/decline", 204
                )
        elif case_id in {"former_member", "inactive_room"}:
            self.finish_membership("bob", room)
            if case_id == "inactive_room":
                actor = "alice"
                self.history(
                    "alice",
                    room,
                    [(self.users["alice"], "Private plan: Fountain at noon.")],
                )
        elif case_id == "missing_session":
            actor = None
        elif case_id == "invalid_session":
            self.tokens["bob"] = "not-a-real-m0-session"
        elif case_id == "expired_session":
            # Change only this test session's expiry. There is no need to wait 30 days.
            with self.sessions() as session:
                session.execute(
                    update(AuthSession)
                    .where(
                        AuthSession.token_hash == token_hash(self.tokens["bob"]),
                    )
                    .values(expires_at=datetime(2000, 1, 1, tzinfo=UTC))
                )
                session.commit()
        elif case_id == "logged_out_session":
            self.request("bob", "POST", "/auth/logout", 204)
            # Keep the old token so the next request really tries to replay it.
        elif case_id == "deleted_account":
            self.finish_membership("bob", room, delete=True)
        return actor, room

    def denied_attempt(self, case, actor, room, operation):
        """Check both the response and stored effects, even when access is refused."""
        before = self.message_rows()
        payload = {"text": "This message must not be saved."}
        if case["id"] == "spoofed_sender":
            payload["sender_id"] = self.users["alice"]
        method = "GET" if operation == "read" else "POST"
        response = self.request(
            actor,
            method,
            f"/chat/rooms/{room}/messages",
            body=None if operation == "read" else payload,
        )
        changed = self.message_rows() != before
        leaked = any(row[3] in response.text for row in before)
        violation = response.is_success or changed or leaked
        correct = response.status_code == case["status"] and not violation
        return {
            "id": f"{case['id']}.{operation}",
            "expected_status": case["status"],
            "actual_status": response.status_code,
            "unauthorized_access": violation,
            "passed": correct,
            "executed": True,
            "stored_messages_changed": changed,
            "private_content_returned": leaked,
        }


@contextmanager
def run_case(engine):
    """Start each case with clean synthetic data and restore application overrides."""
    with engine.begin() as connection:
        tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    sessions = make_session_factory(engine)

    def database_session():
        with sessions() as session:
            yield session

    overrides = app.dependency_overrides.copy()
    limiter = LoginLimiter()
    app.dependency_overrides[get_db] = database_session
    app.dependency_overrides[get_login_limiter] = lambda: limiter
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            journey = Journey(engine, client)
            journey.register_users()
            yield journey
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(overrides)


def authorized_result(engine, case, control=False):
    """Record an entire journey as failed if any required step fails."""
    try:
        with run_case(engine) as journey, ExitStack() as stack:
            if control:
                # This broken version refuses a real member. The eval must catch it.
                stack.enter_context(
                    patch.object(
                        chat_rooms,
                        "list_messages",
                        side_effect=PermissionError("M0 control: deny a member"),
                    )
                )
            journey.authorized(case["id"])
        return {"id": case["id"], "passed": True, "error": None}
    except CaseFailure as error:
        return {"id": case["id"], "passed": False, "error": str(error)}


def denied_results(engine, case, control=False):
    """Record every planned denied attempt; setup failures cannot silently vanish."""
    try:
        with run_case(engine) as journey:
            actor, room = journey.denied_setup(case["id"])

            def unsafe_history(session, room_id, user_id):
                # Deliberately omit membership checks in this isolated control only.
                return list(
                    session.scalars(
                        select(ChatMessage)
                        .where(ChatMessage.room_id == room_id)
                        .order_by(ChatMessage.id)
                    )
                )

            def unsafe_message(session, room_id, sender_id, message):
                # The matching broken write also skips membership checks.
                saved = ChatMessage(
                    room_id=room_id,
                    sender_id=sender_id,
                    text=message,
                    created_at=datetime.now(UTC),
                )
                session.add(saved)
                session.flush()
                return saved

            with ExitStack() as stack:
                if control:
                    stack.enter_context(
                        patch.object(chat_rooms, "list_messages", unsafe_history)
                    )
                    stack.enter_context(
                        patch.object(chat_rooms, "add_message", unsafe_message)
                    )
                return [
                    journey.denied_attempt(case, actor, room, operation)
                    for operation in case["operations"]
                ]
    except CaseFailure as error:
        return [
            {
                "id": f"{case['id']}.{operation}",
                "passed": False,
                "executed": False,
                "unauthorized_access": False,
                "error": str(error),
            }
            for operation in case["operations"]
        ]


def file_hash(paths):
    """Identify the exact inputs without saving random cookies or timestamps."""
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(PROJECT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def evaluate(engine, scenarios):
    """Measure all fixed journeys and confirm both deliberately faulty controls fail."""
    authorized = [authorized_result(engine, case) for case in scenarios["authorized"]]
    denied = [
        result
        for case in scenarios["denied"]
        for result in denied_results(engine, case)
    ]
    denied_member = authorized_result(engine, scenarios["authorized"][0], control=True)
    allowed_outsider = denied_results(engine, scenarios["denied"][0], control=True)
    controls = {
        "blocked_member_detected": not denied_member["passed"],
        "outsider_read_detected": any(
            row["id"] == "outsider.read"
            and row["executed"]
            and row["unauthorized_access"]
            for row in allowed_outsider
        ),
        "outsider_write_detected": any(
            row["id"] == "outsider.write"
            and row["executed"]
            and row["unauthorized_access"]
            and row["stored_messages_changed"]
            for row in allowed_outsider
        ),
    }
    completed = sum(row["passed"] for row in authorized)
    violations = sum(row["unauthorized_access"] for row in denied)
    complete = all(row["executed"] for row in denied)
    sources = [
        *PROJECT.joinpath("backend/app").rglob("*.py"),
        *PROJECT.joinpath("db").rglob("*.py"),
    ]
    return {
        "issue": scenarios["issue"],
        "baseline_revision": scenarios["baseline_revision"],
        "simulation": "fixed fictional users; separate cookies; disposable PostgreSQL schema",
        "application_sha256": file_hash(sources),
        "evaluator_sha256": file_hash([Path(__file__).resolve()]),
        "scenarios_sha256": file_hash([SCENARIOS]),
        "thresholds": scenarios["thresholds"],
        "authorized": {
            "completed": completed,
            "total": len(authorized),
            "completion_rate": completed / len(authorized),
            "journeys": authorized,
        },
        "privacy": {
            "unauthorized_accesses": violations,
            "planned_attempts": len(denied),
            "executed_attempts": sum(row["executed"] for row in denied),
            "attempts": denied,
        },
        "controls": controls,
        "verdict": {
            "reliable_met": completed == len(authorized),
            "private_met": complete
            and violations == 0
            and all(row["passed"] for row in denied),
            "controls_met": all(controls.values()),
            "execution_complete": complete,
        },
    }


def main(argv=None):
    """Print the evidence; --check also compares it with the recorded baseline."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="compare with results.json"
    )
    args = parser.parse_args(argv)
    try:
        scenarios = load_scenarios()
        with test_database() as engine:
            result = evaluate(engine, scenarios)
    except Exception as error:
        # Database errors may contain connection details, so do not print raw errors.
        message = str(error) if isinstance(error, CaseFailure) else type(error).__name__
        print(f"M0 could not finish: {message}", file=sys.stderr)
        return 1
    a, p, verdict = result["authorized"], result["privacy"], result["verdict"]
    print(
        f"Authorized journeys: {a['completed']}/{a['total']} ({a['completion_rate']:.0%})"
    )
    print(
        f"Unauthorized accesses: {p['unauthorized_accesses']}/{p['executed_attempts']} attempts"
    )
    print("Reliable: " + ("MET" if verdict["reliable_met"] else "MISSED"))
    print("Private: " + ("MET" if verdict["private_met"] else "MISSED"))
    print("Faulty controls detected: " + ("YES" if verdict["controls_met"] else "NO"))
    print("Application source: " + result["application_sha256"])
    for row in [*a["journeys"], *p["attempts"]]:
        if not row["passed"]:
            print(
                f"Failed: {row['id']} — {row.get('error', 'unexpected access or response')}"
            )
    if not verdict["execution_complete"] or not verdict["controls_met"]:
        print(
            "Incomplete cases or failed evaluator controls; no valid result.",
            file=sys.stderr,
        )
        return 1
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULTS.exists():
            print("Missing eval_project3/results.json.", file=sys.stderr)
            return 1
        recorded = json.loads(RESULTS.read_text(encoding="utf-8"))
        measured = result.copy()
        # Keep the baseline's source hash, but compare behavior after teammates' edits.
        recorded.pop("application_sha256", None)
        measured.pop("application_sha256", None)
        if recorded != measured:
            print(
                "Results changed. Review the finding before replacing results.json.",
                file=sys.stderr,
            )
            return 1
        print(
            "Matches the recorded outcomes. Reproduction is separate from the claim's verdict."
        )
    else:
        RESULTS.write_text(rendered, encoding="utf-8")
        print("Wrote eval_project3/results.json. Record the review in Issue #8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
