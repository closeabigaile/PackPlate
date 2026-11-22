"""services/crowd_forecast.py: no database."""

from datetime import date, datetime, timedelta

from app.services import crowd_forecast as cf
from app.services.hours import CAMPUS_TZ

WINDOW = timedelta(minutes=30)


def at(h, m=0, day=6):  # 2026-10-06 is a Tuesday
    return datetime(2026, 10, day, h, m, tzinfo=CAMPUS_TZ)


def period(day=6):
    return (
        datetime(2026, 10, day, 7, 0, tzinfo=CAMPUS_TZ),
        datetime(2026, 10, day, 21, 0, tzinfo=CAMPUS_TZ),
    )


def test_closed_has_no_forecast():
    assert cf.forecast(at(12), None).level is None


def test_weekday_lunch_is_crowded_and_mid_afternoon_is_not():
    assert cf.forecast(at(12, 15), period()).level == "crowded"
    assert cf.forecast(at(15, 30), period()).level == "not_busy"


def test_dinner_busier_than_late_evening():
    assert cf.forecast(at(18), period()).score > cf.forecast(at(20, 30), period()).score


def test_weekend_lunch_quieter_than_weekday_lunch():
    sat = cf.forecast(at(12, 30, day=10), period(10)).score  # Saturday
    assert sat < cf.forecast(at(12, 30), period()).score


def test_just_after_opening_is_damped():
    opens = datetime(2026, 10, 6, 12, 0, tzinfo=CAMPUS_TZ)
    closes = opens + timedelta(hours=3)
    early = cf.forecast(at(12, 2), (opens, closes)).score
    later = cf.forecast(at(12, 30), (opens, closes)).score
    assert early < later


def test_calendar_factor_scales_down(monkeypatch):
    monkeypatch.setattr(cf, "CALENDAR", [(date(2026, 10, 6), date(2026, 10, 6), 0.3)])
    assert cf.forecast(at(12, 15), period()).level != "crowded"


def test_no_reports_uses_forecast():
    assert cf.blend(0.9, [], at(12), WINDOW) == ("crowded", "forecast")


def test_no_forecast_no_reports_is_unknown():
    assert cf.blend(None, [], at(12), WINDOW) == (None, "none")


def test_fresh_reports_pull_the_level_down_from_forecast():
    reports = [("not_busy", at(11, 58))] * 4
    level, source = cf.blend(0.9, reports, at(12), WINDOW)
    assert (level, source) == ("not_busy", "forecast+reports")


def test_stale_reports_ignored():
    reports = [("not_busy", at(11, 0))]  # outside the window
    assert cf.blend(0.9, reports, at(12), WINDOW) == ("crowded", "forecast")


class Row:
    """Stands in for a HoursDay row."""

    def __init__(self, day, windows, status="open"):
        self.date, self.windows, self.status = day, windows, status


def test_current_period_finds_the_open_window():
    today = Row(date(2026, 10, 6), [[420, 1260]])
    opens, closes = cf.current_period(at(12), today, None)
    assert (opens.hour, closes.hour) == (7, 21)


def test_current_period_closed_or_unknown_is_none():
    today = Row(date(2026, 10, 6), [[420, 600]])
    assert cf.current_period(at(12), today, None) is None
    assert cf.current_period(at(12), None, None) is None
    unknown = Row(date(2026, 10, 6), [], status="unknown")
    assert cf.current_period(at(12), unknown, None) is None


def test_current_period_after_midnight_uses_yesterday():
    yesterday = Row(date(2026, 10, 5), [[420, 1500]])  # closes 1:00am
    assert cf.current_period(at(0, 30), None, yesterday) is not None
