"""Tests for the dining assistant through the API (M3): sign-in, history, limits."""

from datetime import date

import pytest

from app.api.assistant import get_limiter
from app.main import app
from app.services.assistant import settings
from app.services.assistant.limits import RateLimiter
from app.services.auth import SESSION_COOKIE

MESSAGES = "/assistant/messages"
DAY = date(2026, 10, 6)
NOON = "2026-10-06T12:00:00-04:00"
PASSWORD = "PackPlate-Test-123!"


@pytest.fixture(autouse=True)
def roomy_limiter(client):
    """Give every test its own limiter so one test's requests don't count against another."""
    limiter = RateLimiter(100, 60)
    app.dependency_overrides[get_limiter] = lambda: limiter


@pytest.fixture
def make_user(client):
    """Create an account and return its id and the headers that sign requests in as it."""

    def make(name):
        account = client.post(
            "/auth/register", json={"username": name, "password": PASSWORD}
        )
        assert account.status_code == 201, account.text
        # Signing up logs in with a cookie. Take it out of the shared client so each
        # user sends only their own cookie, through their headers.
        token = client.cookies[SESSION_COOKIE]
        client.cookies.clear()
        return {
            "id": account.json()["id"],
            "headers": {"Cookie": f"{SESSION_COOKIE}={token}"},
        }

    return make


def fountain(seed):
    """Fountain with a dinner menu: rice fits a dairy-free profile, mac and cheese doesn't."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Dinner")
    seed.nutrition("1|rice|1 cup", location_id=1, serving_size="1 cup", calories=200.0)
    seed.nutrition("1|mac|1 cup", location_id=1, serving_size="1 cup", calories=400.0)
    seed.item(11, "Steamed Rice", nutrition_key="1|rice|1 cup")
    seed.item(11, "Mac and Cheese", nutrition_key="1|mac|1 cup", allergens=["dairy"])


def send(client, user, text, **extra):
    """Send a message as `user`, at noon on the test day."""
    return client.post(
        MESSAGES, headers=user["headers"], json={"text": text, "at": NOON, **extra}
    )


def test_every_route_needs_a_login(client):
    """Signed out, sending, reading, and clearing history are all refused with 401."""
    assert client.post(MESSAGES, json={"text": "hello"}).status_code == 401
    assert client.get(MESSAGES).status_code == 401
    assert client.delete(MESSAGES).status_code == 401


def test_a_message_gets_a_reply_and_both_are_saved(client, seed, make_user):
    """The reply comes back, and history then holds the question and the answer in order."""
    fountain(seed)
    alice = make_user("alice")

    reply = send(client, alice, "what's for dinner at Fountain tonight?")
    history = client.get(MESSAGES, headers=alice["headers"]).json()

    assert reply.status_code == 201
    assert "Steamed Rice" in reply.json()["reply"]
    assert reply.json()["source"] == "rules"
    assert [m["role"] for m in history] == ["user", "assistant"]
    assert history[0]["text"] == "what's for dinner at Fountain tonight?"
    assert history[1]["text"] == reply.json()["reply"]


def test_the_profile_in_the_request_filters_the_menu(client, seed, make_user):
    """A dairy restriction sent with the message hides the dairy dish, and cards are saved."""
    fountain(seed)
    alice = make_user("alice")

    reply = send(
        client,
        alice,
        "what's for dinner at Fountain tonight?",
        profile={"avoid": ["dairy"]},
    ).json()

    assert "Steamed Rice" in reply["reply"]
    assert "Mac and Cheese" not in reply["reply"]
    assert [c["name"] for c in reply["cards"]] == ["Steamed Rice"]
    saved = client.get(MESSAGES, headers=alice["headers"]).json()
    assert [c["name"] for c in saved[1]["cards"]] == ["Steamed Rice"]


def test_each_account_sees_only_its_own_history(client, seed, make_user):
    """One user's conversation never appears for, or gets cleared by, another user."""
    fountain(seed)
    alice, bob = make_user("alice"), make_user("bob")
    send(client, alice, "what's for dinner at Fountain tonight?")

    assert client.get(MESSAGES, headers=bob["headers"]).json() == []
    assert client.delete(MESSAGES, headers=bob["headers"]).status_code == 204
    assert len(client.get(MESSAGES, headers=alice["headers"]).json()) == 2


def test_clearing_history_deletes_the_conversation(client, seed, make_user):
    """DELETE removes every saved message for the account."""
    fountain(seed)
    alice = make_user("alice")
    send(client, alice, "hello")

    assert client.delete(MESSAGES, headers=alice["headers"]).status_code == 204
    assert client.get(MESSAGES, headers=alice["headers"]).json() == []


def test_bad_requests_are_rejected(client, make_user):
    """Blank or over-long text, extra fields, and an unknown allergen all give 422."""
    alice = make_user("alice")
    too_long = "a" * (settings.MAX_MESSAGE_CHARS + 1)

    for body in (
        {"text": "   "},
        {"text": too_long},
        {"text": "hi", "extra": 1},
        {"text": "hi", "profile": {"avoid": ["kryptonite"]}},
        {"text": "hi", "profile": {"avoid": [], "unknown": 1}},
    ):
        response = client.post(MESSAGES, headers=alice["headers"], json=body)
        assert response.status_code == 422, body


def test_asking_too_fast_is_limited(client, make_user):
    """Past the per-account limit the API answers 429 with a Retry-After."""
    alice = make_user("alice")
    limiter = RateLimiter(2, 60)
    app.dependency_overrides[get_limiter] = lambda: limiter

    codes = [send(client, alice, "hello").status_code for _ in range(3)]
    third = send(client, alice, "hello")

    assert codes == [201, 201, 429]
    assert int(third.headers["Retry-After"]) >= 1


def test_the_rate_limit_is_per_account(client, make_user):
    """One account using up its limit doesn't block another account."""
    alice, bob = make_user("alice"), make_user("bob")
    limiter = RateLimiter(1, 60)
    app.dependency_overrides[get_limiter] = lambda: limiter

    assert send(client, alice, "hello").status_code == 201
    assert send(client, alice, "hello").status_code == 429
    assert send(client, bob, "hello").status_code == 201


def test_deleting_the_account_deletes_its_history(client, db, make_user):
    """The assistant's messages are removed together with the account."""
    alice = make_user("alice")
    send(client, alice, "hello")

    deleted = client.request(
        "DELETE", "/auth/me", headers=alice["headers"], json={"password": PASSWORD}
    )

    assert deleted.status_code == 204
    from sqlalchemy import text

    assert db.execute(text("SELECT count(*) FROM assistant_messages")).scalar() == 0


def test_the_assistant_can_be_switched_off(client, make_user, monkeypatch):
    """With ASSISTANT_ENABLED=false every route answers 404."""
    alice = make_user("alice")
    monkeypatch.setenv("ASSISTANT_ENABLED", "false")

    assert send(client, alice, "hello").status_code == 404
    assert client.get(MESSAGES, headers=alice["headers"]).status_code == 404


def test_old_messages_are_trimmed_to_the_history_limit(db, make_user, client):
    """Only the newest messages are kept once an account goes over the limit."""
    from datetime import UTC, datetime, timedelta

    from app.repositories import assistant as repo

    alice = make_user("alice")
    start = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    for i in range(5):
        repo.add_message(
            db, alice["id"], "user", f"message {i}", [], start + timedelta(minutes=i)
        )

    repo.trim(db, alice["id"], 3)

    assert [m.text for m in repo.recent(db, alice["id"], 10)] == [
        "message 2",
        "message 3",
        "message 4",
    ]
