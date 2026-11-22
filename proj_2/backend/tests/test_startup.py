"""Tests for migrating a local database when the API starts."""

import os

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect

from app import startup
from db.migrate import alembic_config, check_current


class NeverUsed:
    """An engine that fails the test if anything touches it."""

    def __getattr__(self, name):
        raise AssertionError(f"the database was touched ({name})")


@pytest.mark.parametrize(
    "url, local",
    [
        ("postgresql://u:p@localhost:5432/packplate", True),
        ("postgresql://u:p@127.0.0.1:5433/packplate", True),
        ("postgresql://u:p@db:5432/packplate", True),  # the Docker service
        ("postgresql:///packplate", True),  # a local socket
        ("postgresql://u:p@db.abcdefgh.supabase.co:5432/postgres", False),
        ("postgresql://u:p@10.0.0.7:5432/packplate", False),
    ],
)
def test_only_a_database_on_this_machine_counts_as_local(url, local):
    """localhost, the Docker `db` service and sockets are local; a hosted or remote database is not."""
    assert startup.is_local(url) is local


def test_nothing_is_touched_when_off_unset_or_remote(monkeypatch):
    """Turned off, no database set, or a shared database: it reports why and never connects."""
    local = "postgresql://u:p@localhost:5432/x"
    remote = "postgresql://u:p@db.abcdefgh.supabase.co:5432/postgres"

    monkeypatch.setenv("MIGRATE_ON_START", "false")
    assert startup.migrate_if_local(local, NeverUsed()) == "disabled"

    monkeypatch.setenv("MIGRATE_ON_START", "true")
    assert startup.migrate_if_local("", NeverUsed()) == "no database set"
    assert startup.migrate_if_local(remote, NeverUsed()) == "not local"


def test_a_database_that_is_up_to_date_is_left_alone(pg_engine, monkeypatch):
    """Nothing to do when the schema is already at the newest revision."""
    monkeypatch.setenv("MIGRATE_ON_START", "true")
    url = os.environ["TEST_DATABASE_URL"]

    assert startup.migrate_if_local(url, pg_engine) == "current"


def test_a_database_that_is_behind_is_brought_up_to_date(pg_engine, monkeypatch):
    """Put the test database back to revision 0007, and starting migrates it forward again."""
    monkeypatch.setenv("MIGRATE_ON_START", "true")
    url = os.environ["TEST_DATABASE_URL"]
    cfg = alembic_config()
    with pg_engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "0007")
    assert "location_points" not in inspect(pg_engine).get_table_names()

    result = startup.migrate_if_local(url, pg_engine)

    assert result == "migrated"
    assert "location_points" in inspect(pg_engine).get_table_names()
    check_current(pg_engine)  # raises if it isn't at the newest revision


def test_an_unreachable_database_is_retried_and_then_reported_not_raised(monkeypatch):
    """A database still starting gets a few tries; if it never answers, the API starts anyway."""
    monkeypatch.setenv("MIGRATE_ON_START", "true")
    waits = []
    nowhere = create_engine(
        "postgresql+psycopg://u:p@127.0.0.1:1/x", connect_args={"connect_timeout": 1}
    )

    result = startup.migrate_if_local(
        "postgresql://u:p@127.0.0.1:1/x", nowhere, sleep=waits.append
    )

    assert result == "failed"
    assert len(waits) == startup.WAIT_TRIES - 1
