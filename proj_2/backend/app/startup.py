"""Bring a local database up to date when the API starts, so nobody has to run
`alembic upgrade head` by hand after pulling new code.

Only a database on this machine (or the Docker `db` service) is changed. A shared
or hosted database is never touched here: someone runs the migration on purpose,
and a warning in the log says so. MIGRATE_ON_START=false turns this off.

A failure never stops the API from starting; /health still reports the schema as
"outdated" or the database as "unreachable".
"""

import logging
import os
import time

from sqlalchemy import make_url, text
from sqlalchemy.exc import OperationalError

from db.migrate import check_current, upgrade

log = logging.getLogger("uvicorn.error")

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db", "host.docker.internal"}
WAIT_TRIES = 15  # a database that is still starting gets about this many seconds
LOCK_KEY = 73050301  # one migration at a time if several API processes start together


def enabled() -> bool:
    """Whether migrating on start is allowed (MIGRATE_ON_START, on unless "false")."""
    return os.getenv("MIGRATE_ON_START", "true").lower() != "false"


def is_local(url: str) -> bool:
    """Whether a database URL points at this machine or the Docker `db` service."""
    host = make_url(url).host
    return host is None or host in LOCAL_HOSTS  # no host means a local socket


def migrate_if_local(url: str | None = None, engine=None, sleep=time.sleep) -> str:
    """Migrate a local database to the newest revision; returns what happened.

    One of "disabled", "no database set", "not local", "current" (nothing to do),
    "migrated", or "failed". `engine` and `sleep` are for tests.
    """
    url = url if url is not None else os.getenv("DATABASE_URL", "")
    if not enabled():
        return "disabled"
    if not url:
        return "no database set"
    if not is_local(url):
        log.warning(
            "Not migrating a database that isn't on this machine. "
            "Run `alembic -c db/alembic.ini upgrade head` from proj_2/ if it is outdated."
        )
        return "not local"
    if engine is None:
        from app.deps import get_engine

        engine = get_engine()
    for attempt in range(WAIT_TRIES):
        try:
            try:
                check_current(engine)
                return "current"
            except RuntimeError:
                pass
            # Hold a lock while migrating, so two starting processes don't collide.
            with engine.begin() as conn:
                conn.execute(
                    text("SELECT pg_advisory_xact_lock(:key)"), {"key": LOCK_KEY}
                )
                upgrade(conn)
            log.info("Migrated the database to the newest revision.")
            return "migrated"
        except OperationalError:
            if attempt == WAIT_TRIES - 1:
                break
            sleep(1)  # the database is probably still starting
        except Exception:
            log.exception("Could not migrate the database on start.")
            return "failed"
    log.warning("Could not reach the database to migrate it.")
    return "failed"
