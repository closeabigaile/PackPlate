from datetime import UTC, datetime, timedelta

from db.models import IngestRun
from ingestion.scrape_alerts import alerts

NOW = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)


def add_run(db, status, finished_hours_ago=1, errors=(), stats=None):
    done = NOW - timedelta(hours=finished_hours_ago)
    db.add(
        IngestRun(
            started_at=done - timedelta(minutes=10),
            finished_at=done,
            status=status,
            options={},
            stats=stats or {},
            errors=list(errors),
        )
    )
    db.commit()


def titles(db):
    return [a["title"] for a in alerts(db, NOW)]


def test_no_alerts_after_a_recent_good_run(db):
    add_run(db, "ok")
    assert alerts(db, NOW) == []


def test_failed_run_alerts_with_its_errors_and_staleness(db):
    add_run(db, "ok", finished_hours_ago=40)
    add_run(db, "failed", errors=["fatal: ConnectTimeout()"])
    got = alerts(db, NOW)
    assert [a["title"] for a in got] == ["Daily scrape failed", "Menu data is stale"]
    assert "- fatal: ConnectTimeout()" in got[0]["body"]


def test_partial_run_alerts_but_data_is_fresh(db):
    add_run(db, "partial", errors=["hours Fountain Dining Hall: timeout"])
    assert titles(db) == ["Daily scrape finished with errors"]


def test_review_alert_is_a_count_only(db):
    add_run(db, "ok", stats={"label_reviews_pending": 2})
    [alert] = alerts(db, NOW)
    assert alert["title"] == "2 diet tags waiting for review"
    assert "review_labels" in alert["body"]


def test_never_run(db):
    assert titles(db) == ["Scraper has never run"]
