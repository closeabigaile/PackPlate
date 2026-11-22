"""Tables for the dining assistant (M3): chat history and dining locations' positions. Writer: backend.

Imported at the bottom of db/models.py, so the table is on Base.metadata for
Alembic and the tests. Each account has one running conversation, so a message
belongs to a user directly. Deleting the account deletes its messages.

The positions of the dining locations live in their own table, not on `locations`,
because the ingestion job owns that one and a scrape must never touch them.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.models import Base


class AssistantMessage(Base):
    """One message in an account's conversation with the assistant.

    role is 'user' (what the person typed) or 'assistant' (the reply). cards holds
    the result cards shown with a reply (menu items), so history can show them again.
    The dietary profile is never stored: it comes from the browser with each message.
    """

    __tablename__ = "assistant_messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')", name="ck_assistant_messages_role"
        ),
        Index("ix_assistant_messages_user_time_id", "user_id", "created_at", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(10))
    text: Mapped[str] = mapped_column(Text)
    cards: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LocationPoint(Base):
    """Where a dining location is: latitude and longitude, for "which hall is closest?".

    Writer: backend (db/seed_location_points.py). One row per location, kept apart from
    `locations` so the nightly ingestion never overwrites it. Deleted with its location.
    """

    __tablename__ = "location_points"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="ck_location_points_range",
        ),
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True
    )
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
