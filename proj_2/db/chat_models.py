"""Draft tables for Chat Rooms, members, invitations, and messages."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models import Base

# These account IDs are integers for now, like the IDs in the chat tests.
# Match M1's ID type and add the account foreign keys when we make the migration.


class ChatRoomRecord(Base):
    """One saved Chat Room and its status. Writer: backend."""

    __tablename__ = "chat_rooms"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'inactive')", name="ck_chat_rooms_status"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(10))
    memberships: Mapped[list["ChatRoomMember"]] = relationship(
        cascade="all, delete-orphan"
    )
    invitations: Mapped[list["ChatInvitation"]] = relationship(
        cascade="all, delete-orphan"
    )

    @property
    def member_ids(self) -> list[int]:
        """Return the account IDs of people who have joined the Chat Room."""
        return sorted(member.user_id for member in self.memberships)


class ChatRoomMember(Base):
    """One account that has joined a Chat Room. Writer: backend."""

    __tablename__ = "chat_room_members"

    # The two IDs together stop the same person from joining a room twice.
    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)


class ChatInvitation(Base):
    """An invitation and its response, so retries can find it. Writer: backend."""

    __tablename__ = "chat_invitations"
    __table_args__ = (
        UniqueConstraint("room_id", "invitee_id", name="uq_chat_invitation_room_user"),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'cancelled')",
            name="ck_chat_invitations_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE")
    )
    invitee_id: Mapped[int] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(10))


class ChatMessage(Base):
    """One message saved in a Chat Room. Writer: backend."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_room_time_id", "room_id", "created_at", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("chat_rooms.id", ondelete="CASCADE")
    )
    # Keep the sender ID with the message even after the sender leaves.
    sender_id: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
