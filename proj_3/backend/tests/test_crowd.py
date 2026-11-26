"""services/crowd.py: no database."""

from datetime import datetime, timedelta

from app.services.crowd import WINDOW, Throttle, aggregate
from app.services.hours import CAMPUS_TZ

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=CAMPUS_TZ)


def ago(minutes):
    return NOW - timedelta(minutes=minutes)


def test_no_reports_is_unknown_not_quiet():
    assert vars(aggregate([], NOW)) == {
        "level": None,
        "report_count": 0,
        "last_reported_at": None,
    }


def test_single_report():
    crowd = aggregate([("crowded", ago(5))], NOW)
    assert (crowd.level, crowd.report_count, crowd.last_reported_at) == (
        "crowded",
        1,
        ago(5),
    )


def test_reports_outside_the_window_or_after_at_are_ignored():
    reports = [
        ("crowded", NOW - WINDOW),
        ("crowded", NOW + timedelta(minutes=1)),
        ("not_busy", ago(1)),
    ]
    crowd = aggregate(reports, NOW)
    assert (crowd.level, crowd.report_count) == ("not_busy", 1)


def test_newer_reports_count_more():
    assert (
        aggregate([("crowded", ago(25)), ("not_busy", ago(1))], NOW).level == "not_busy"
    )
    assert (
        aggregate([("not_busy", ago(25)), ("crowded", ago(1))], NOW).level == "crowded"
    )


def test_mixed_reports_average_to_moderate():
    reports = [("crowded", ago(2)), ("not_busy", ago(2))]
    assert aggregate(reports, NOW).level == "moderate"


def test_throttle_allows_once_per_key_per_period():
    clock = [100.0]
    throttle = Throttle(60, clock=lambda: clock[0])
    assert throttle.hit(("a", 1)) == 0
    assert throttle.hit(("b", 1)) == 0  # another client
    assert throttle.hit(("a", 2)) == 0  # another location
    clock[0] = 130.0
    assert throttle.hit(("a", 1)) == 30
    clock[0] = 160.0
    assert throttle.hit(("a", 1)) == 0
