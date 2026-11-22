"""The `forecast` field in /locations, against the test database."""

from datetime import datetime, timedelta

from app.services.hours import CAMPUS_TZ

NOON = datetime(2026, 10, 6, 12, 15, tzinfo=CAMPUS_TZ)  # a Tuesday lunch rush


def _listed(seed, location_id, menu_id):
    """Locations are listed only once they have menu data."""
    seed.menu(menu_id, location_id, NOON.date(), "Lunch")
    seed.item(menu_id, "Soup")


def _locations(client, at):
    response = client.get("/locations", params={"at": at.isoformat()})
    return {loc["id"]: loc for loc in response.json()}


def test_open_location_gets_a_forecast_without_any_reports(client, seed):
    seed.location(1)
    _listed(seed, 1, 31)
    seed.hours(1, NOON.date(), windows=[(420, 1260)])
    loc = _locations(client, NOON)[1]
    assert loc["forecast"] == {
        "level": "crowded",
        "estimate": "crowded",
        "source": "forecast",
    }
    assert loc["crowd"]["level"] is None  # the report-based field is unchanged


def test_closed_or_unknown_hours_have_no_forecast(client, seed):
    seed.location(1)
    seed.location(2, "Case Dining Hall", "case")
    _listed(seed, 1, 31)
    _listed(seed, 2, 32)
    seed.hours(1, NOON.date(), windows=[(420, 600)])  # closed by noon
    # location 2 has no hours row at all
    by_id = _locations(client, NOON)
    for loc_id in (1, 2):
        assert by_id[loc_id]["forecast"] == {
            "level": None,
            "estimate": None,
            "source": "none",
        }


def test_recent_reports_pull_the_estimate_but_not_the_forecast(client, seed):
    seed.location(1)
    _listed(seed, 1, 31)
    seed.hours(1, NOON.date(), windows=[(420, 1260)])
    for minutes in (1, 2, 3, 4):
        seed.crowd(1, "not_busy", NOON - timedelta(minutes=minutes))
    forecast = _locations(client, NOON)[1]["forecast"]
    assert forecast["level"] == "crowded"
    assert forecast["estimate"] == "not_busy"
    assert forecast["source"] == "forecast+reports"
