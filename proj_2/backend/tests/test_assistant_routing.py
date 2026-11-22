"""Tests for driving distances from a place too far to walk from (M3).

No real routing service is ever called: a stand-in answers, or a tiny local HTTP
server plays the part of the OSRM server.
"""

import json
import socketserver
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.services.assistant import chat, routing, settings
from app.services.hours import campus_time

DAY = date(2026, 10, 6)
NOON = campus_time(datetime(2026, 10, 6, 12, 0))
CARY = ("3843 Cary Glen Boulevard", (35.8187, -78.9038))


class FakeGeocoder:
    """Always finds the same place."""

    def lookup(self, phrase):
        return CARY


class FakeRouter:
    """Stands in for the routing service: gives the answer it was built with."""

    def __init__(self, routes):
        self.routes = routes
        self.asked = []

    def driving(self, origin, destinations):
        self.asked.append((origin, destinations))
        return self.routes(destinations) if callable(self.routes) else self.routes


FOUNTAIN_AT = (35.78547, -78.67764)
CASE_AT = (35.782872, -78.669417)


def by_place(**routes):
    """A route answer keyed by hall, whatever order the halls are asked about in."""
    table = {FOUNTAIN_AT: routes.get("fountain"), CASE_AT: routes.get("case")}
    return lambda destinations: [table[tuple(d)] for d in destinations]


def two_halls(seed):
    """Fountain (id 1) and Case (id 3), both with a dinner menu, with saved positions."""
    seed.location(1)
    seed.location(3, name="Case Dining Hall", slug="case")
    seed.point(1, 35.78547, -78.67764)
    seed.point(3, 35.782872, -78.669417)
    for loc, menu in ((1, 11), (3, 31)):
        seed.menu(menu, loc, DAY, "Dinner")
        seed.item(menu, "Rice")


def ask_from_cary(db, router, **extra):
    """Ask "which hall is close?" from the far-away place."""
    return chat.respond(
        db,
        "I AM AT 3843 CARY GLEN BLVD which dining hall is close?",
        None,
        NOON,
        geocoder=FakeGeocoder(),
        router=router,
        **extra,
    )["reply"]


def test_a_far_place_is_ranked_by_driving_time_and_shown_in_miles_and_minutes(db, seed):
    """Fountain is nearer in a straight line, but Case is quicker by road, so Case is first."""
    two_halls(seed)
    router = FakeRouter(by_place(fountain=(29000.0, 2400.0), case=(28000.0, 1800.0)))

    reply = ask_from_cary(db, router)

    lines = reply.splitlines()
    assert lines[0] == "Closest to 3843 Cary Glen Boulevard:"
    assert lines[1].startswith("- Case Dining Hall (about 17.4 mi, 30 min by car")
    assert lines[2].startswith("- Fountain Dining Hall (about 18 mi, 40 min by car")
    assert "light traffic" in reply
    assert "straight line" not in reply


def test_when_the_route_lookup_fails_straight_line_miles_are_shown_and_said_so(
    db, seed
):
    """No driving distances: the reply falls back to straight-line miles and says it couldn't get more."""
    two_halls(seed)

    reply = ask_from_cary(db, FakeRouter(None))

    assert "mi away in a straight line" in reply
    assert "I couldn't get driving distances" in reply
    assert "by car" not in reply


def test_a_hall_with_no_road_to_it_is_left_out(db, seed):
    """If the service finds no route to one hall, only the reachable one is listed."""
    two_halls(seed)

    reply = ask_from_cary(db, FakeRouter(by_place(case=(28000.0, 1800.0))))

    assert "Case Dining Hall" in reply
    assert "Fountain Dining Hall" not in reply


def test_a_campus_place_never_asks_for_a_route(db, seed):
    """From Talley the halls are walkable: walking minutes are shown and no route is asked for."""
    two_halls(seed)
    router = FakeRouter(by_place(fountain=(1.0, 1.0), case=(1.0, 1.0)))

    reply = chat.respond(
        db, "I'm at Talley, which dining hall is close?", None, NOON, router=router
    )["reply"]

    assert router.asked == []
    assert "mins walk" in reply and "by car" not in reply


def serve(handler):
    """A local stand-in for the routing service. Returns (server, base URL)."""

    class QuietServer(HTTPServer):
        def server_bind(self):
            socketserver.TCPServer.server_bind(self)
            self.server_name, self.server_port = self.server_address[:2]

    server = QuietServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def table_handler(answer, seen):
    """A handler that records each request and answers `answer` as JSON."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("User-Agent")))
            body = json.dumps(answer).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


TABLE = {
    "code": "Ok",
    "distances": [[0, 29023.5, 30656.2]],
    "durations": [[0, 1500.0, None]],
}


def test_the_request_sends_only_coordinates_and_says_who_is_asking():
    """Longitude,latitude pairs go in the path, origin first, with a User-Agent and nothing else."""
    seen = []
    server, url = serve(table_handler(TABLE, seen))
    try:
        router = routing.Router(url, 5, sleep=lambda s: None)
        routes = router.driving((35.8187, -78.9038), [(35.78, -78.67), (35.79, -78.66)])
    finally:
        server.shutdown()

    [(path, agent)] = seen
    assert path.startswith(
        "/table/v1/driving/-78.9038,35.8187;-78.67,35.78;-78.66,35.79"
    )
    assert "sources=0" in path
    assert agent.startswith("PackPlate/")
    assert routes == [(29023.5, 1500.0), None]  # a missing time means no route


def test_the_same_trip_is_asked_once():
    """A repeat of the same origin and halls is answered from memory."""
    seen = []
    server, url = serve(table_handler(TABLE, seen))
    try:
        router = routing.Router(url, 5, sleep=lambda s: None)
        for _ in range(3):
            router.driving((35.8187, -78.9038), [(35.78, -78.67), (35.79, -78.66)])
    finally:
        server.shutdown()

    assert len(seen) == 1


def test_a_failing_or_odd_answer_gives_nothing_and_is_not_remembered():
    """An unreachable service, an error code, or a wrong-sized table all return None."""
    down = routing.Router("http://127.0.0.1:1", 1, sleep=lambda s: None)
    assert down.driving((35.8, -78.9), [(35.78, -78.67)]) is None
    assert down._cache == {}

    seen = []
    server, url = serve(table_handler({"code": "NoRoute"}, seen))
    try:
        router = routing.Router(url, 5, sleep=lambda s: None)
        assert router.driving((35.8, -78.9), [(35.78, -78.67)]) is None
    finally:
        server.shutdown()

    assert routing.Router._parse is not None
    with pytest.raises(ValueError):
        routing.Router._parse(TABLE, 5)  # asked for 5 destinations, got 2


def test_nothing_is_sent_for_no_halls_or_too_many():
    """An empty list or an oversized one never reaches the service."""
    router = routing.Router("http://127.0.0.1:1", 1)
    assert router.driving((35.8, -78.9), []) is None
    assert router.driving((35.8, -78.9), [(35.7, -78.6)] * 100) is None


def test_routing_is_on_unless_switched_off(monkeypatch):
    """Unset means on (no setup for a new machine); "false" turns it off."""
    monkeypatch.setenv("ASSISTANT_ROUTING_ENABLED", "false")
    assert routing.default() is None

    monkeypatch.delenv("ASSISTANT_ROUTING_ENABLED", raising=False)
    assert settings.routing_enabled()
    assert routing.default() is routing.default()
