"""Tests for finding a typed place that isn't in the list (M3).

No real search service is ever called: a stand-in answers, or a tiny local HTTP
server plays the part of OpenStreetMap's search.
"""

import json
import socketserver
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.services.assistant import chat, geocode, settings
from app.services.assistant.intents import where_phrase
from app.services.hours import campus_time

DAY = date(2026, 10, 6)
NOON = campus_time(datetime(2026, 10, 6, 12, 0))
COX_HALL = ("Cox Hall", (35.78606, -78.67094))  # next to Fountain


class FakeGeocoder:
    """Stands in for the search: returns one answer and records what it was asked."""

    def __init__(self, found):
        self.found = found
        self.asked = []

    def lookup(self, phrase):
        self.asked.append(phrase)
        return self.found


def fountain(seed):
    """Fountain with a dinner menu, so there is a hall to rank."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Dinner")
    seed.item(11, "Steamed Rice")
    seed.point(1, 35.78547, -78.67764)


@pytest.mark.parametrize(
    "text, phrase",
    [
        ("I'm at Cox Hall, which dining hall is close?", "cox hall"),
        ("closest dining hall to Lee Hall", "lee hall"),
        ("which dining hall is near Talley Student Union?", "talley student union"),
        ("I'm at 2610 Cates Avenue, what's close", "2610 cates avenue"),
        (
            "I AM AT 3843 CARY GLEN BLVD which dining hall is close?",
            "3843 cary glen blvd",
        ),
        ("I am in main campus which dining hall is close", None),
        ("which dining hall is closest to me", None),
        ("which dining hall is near my location", None),
        ("I'm at the dining hall", None),
    ],
)
def test_the_typed_place_is_cut_out_of_the_message(text, phrase):
    """The place after "at", "near" or "closest to" is found; "me", "main campus" and the like are not places."""
    assert where_phrase(text) == phrase


def test_a_place_that_is_not_listed_is_looked_up(db, seed):
    """ "Cox Hall" isn't in the list here, so the typed words go to the search and its answer is used."""
    fountain(seed)
    finder = FakeGeocoder(("Cox Hall", (35.78606, -78.67094)))
    reply = chat.respond(
        db,
        "I'm at the gazebo, which dining hall is close?",
        None,
        NOON,
        geocoder=finder,
    )["reply"]

    assert finder.asked == ["gazebo"]
    assert reply.splitlines()[0] == "Closest to Cox Hall:"
    assert "- Fountain Dining Hall (about " in reply


def test_a_listed_place_never_goes_to_the_search(db, seed):
    """ "Talley" is in the list, so nothing the student typed is sent anywhere."""
    fountain(seed)
    finder = FakeGeocoder(COX_HALL)

    reply = chat.respond(
        db, "I'm at Talley, which dining hall is close?", None, NOON, geocoder=finder
    )["reply"]

    assert finder.asked == []
    assert reply.startswith("Closest to Talley Student Union:")


def test_a_place_the_search_cannot_find_asks_where_you_are(db, seed):
    """No match near campus: say so, and ask for a place instead of guessing."""
    fountain(seed)
    finder = FakeGeocoder(None)

    reply = chat.respond(
        db,
        "I'm at the gazebo, which dining hall is close?",
        None,
        NOON,
        geocoder=finder,
    )["reply"]

    assert reply.startswith("I couldn't find that place near campus. Where are you?")
    assert "gazebo" not in reply  # what was typed is never repeated back


def test_with_the_search_off_an_unlisted_place_asks_where_you_are(db, seed):
    """No search is configured: the reply is the plain question, and nothing is looked up."""
    fountain(seed)

    reply = chat.respond(
        db, "I'm at the gazebo, which dining hall is close?", None, NOON
    )["reply"]

    assert reply.startswith("Where are you?")


def test_a_bare_reply_to_where_are_you_is_looked_up(db, seed):
    """After "Where are you?", whatever the student types next is taken as the place."""
    fountain(seed)
    finder = FakeGeocoder(COX_HALL)
    history = [
        {"role": "user", "text": "which dining hall is close"},
        {"role": "assistant", "text": "Where are you? Type a campus place"},
    ]

    reply = chat.respond(db, "the gazebo", None, NOON, history, geocoder=finder)[
        "reply"
    ]

    assert finder.asked == ["the gazebo"]
    assert reply.startswith("Closest to Cox Hall:")


def serve(handler):
    """A local stand-in for the search service. Returns (server, base URL)."""

    class QuietServer(HTTPServer):
        def server_bind(self):
            socketserver.TCPServer.server_bind(self)
            self.server_name, self.server_port = self.server_address[:2]

    server = QuietServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def search_handler(results, seen):
    """A handler that records each request's path and User-Agent and answers `results`."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("User-Agent")))
            body = json.dumps(results).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


def test_the_search_request_is_limited_to_campus_and_says_who_is_asking():
    """Only the place text is sent, bounded to the campus box, with a User-Agent."""
    seen = []
    hit = [
        {
            "lat": "35.78",
            "lon": "-78.67",
            "name": "Cox Hall",
            "display_name": "Cox Hall, X",
        }
    ]
    server, url = serve(search_handler(hit, seen))
    try:
        found = geocode.Geocoder(url, 5, sleep=lambda s: None).lookup("cox hall")
    finally:
        server.shutdown()

    assert found == ("Cox Hall", (35.78, -78.67))
    [(path, agent)] = seen
    assert "bounded=1" in path and "viewbox=" in path and "cox+hall" in path
    assert agent.startswith("PackPlate/")


def test_answers_are_cached_and_misses_too():
    """Asking for the same place twice calls the service once, even when it found nothing."""
    seen = []
    server, url = serve(search_handler([], seen))
    try:
        finder = geocode.Geocoder(url, 5, sleep=lambda s: None)
        assert finder.lookup("Nowhere Hall") is None
        assert finder.lookup("nowhere  hall") is None
    finally:
        server.shutdown()

    # Each new place is tried on campus, then in the wider area; the repeat is cached.
    assert len(seen) == 2


def test_calls_are_spaced_a_second_apart():
    """A second new place right after the first waits, as the service's rules ask."""
    clock = {"now": 100.0}
    waits = []
    seen = []
    server, url = serve(search_handler([], seen))
    try:
        finder = geocode.Geocoder(
            url,
            5,
            clock=lambda: clock["now"],
            sleep=lambda s: (waits.append(s), clock.update(now=clock["now"] + s)),
        )
        finder.lookup("one place")
        finder.lookup("another place")
    finally:
        server.shutdown()

    assert waits and waits[0] == pytest.approx(geocode.MIN_SECONDS_BETWEEN_CALLS)


def test_a_failing_service_gives_nothing_and_is_not_remembered():
    """An unreachable service returns None (never an error), and the next try asks again."""
    finder = geocode.Geocoder("http://127.0.0.1:1", 1, sleep=lambda s: None)

    assert finder.lookup("cox hall") is None
    assert finder._cache == {}


@pytest.mark.parametrize("phrase", ["", "   ", "x" * 200])
def test_empty_or_oversized_text_is_never_sent(phrase):
    """Nothing is sent for blank text or a very long message."""
    finder = geocode.Geocoder("http://127.0.0.1:1", 1)
    assert finder.lookup(phrase) is None


def test_the_search_is_on_unless_switched_off(monkeypatch):
    """Unset means on (no setup for a new machine); "false" turns it off."""
    monkeypatch.setenv("ASSISTANT_GEOCODE_ENABLED", "false")
    assert geocode.default() is None

    monkeypatch.delenv("ASSISTANT_GEOCODE_ENABLED", raising=False)
    assert settings.geocode_enabled()
    assert geocode.default() is geocode.default()  # one shared object


def test_a_place_off_campus_is_searched_for_in_the_wider_area():
    """Nothing on campus, so the second search (the Triangle area) finds the street."""
    seen = []
    street = [
        {
            "lat": "35.8187",
            "lon": "-78.9038",
            "display_name": "3843, Cary Glen Boulevard, Cary, Wake County",
        }
    ]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            on_campus = "viewbox=-78.71" in self.path
            body = json.dumps([] if on_campus else street).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server, url = serve(Handler)
    try:
        found = geocode.Geocoder(url, 5, sleep=lambda s: None).lookup(
            "3843 cary glen blvd"
        )
    finally:
        server.shutdown()

    assert found == ("3843 Cary Glen Boulevard", (35.8187, -78.9038))
    assert len(seen) == 2 and "viewbox=-78.71" in seen[0] and "viewbox=-79.3" in seen[1]


def test_a_far_away_place_gets_miles_and_a_plain_note(db, seed):
    """From Cary the halls are ranked in miles with no walking time, and the reply says why."""
    fountain(seed)
    finder = FakeGeocoder(("3843 Cary Glen Boulevard", (35.8187, -78.9038)))

    reply = chat.respond(
        db,
        "I AM AT 3843 CARY GLEN BLVD which dining hall is close?",
        None,
        NOON,
        geocoder=finder,
    )["reply"]

    lines = reply.splitlines()
    assert lines[0] == "Closest to 3843 Cary Glen Boulevard:"
    assert lines[1].startswith("- Fountain Dining Hall (about 1")
    assert " mi away in a straight line" in lines[1]
    assert "min walk" not in reply
    assert "too far to walk" in reply
