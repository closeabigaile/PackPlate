"""Save and load the dining assistant's chat history.

Each account has one running conversation. The queries only flush; the route
commits once the whole request has worked.
"""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db.assistant_models import AssistantMessage


def add_message(
    db: Session, user_id: int, role: str, text: str, cards: list[dict], at: datetime
) -> AssistantMessage:
    """Save one message ('user' or 'assistant') for an account, timestamped `at`."""
    message = AssistantMessage(
        user_id=user_id, role=role, text=text, cards=cards, created_at=at
    )
    db.add(message)
    db.flush()
    return message


def _newest_first(user_id: int):
    return (
        select(AssistantMessage)
        .where(AssistantMessage.user_id == user_id)
        .order_by(AssistantMessage.created_at.desc(), AssistantMessage.id.desc())
    )


def recent(db: Session, user_id: int, limit: int) -> list[AssistantMessage]:
    """An account's latest `limit` messages, oldest first."""
    newest = db.scalars(_newest_first(user_id).limit(limit)).all()
    return list(reversed(newest))


def trim(db: Session, user_id: int, keep: int) -> None:
    """Delete an account's messages except the newest `keep`."""
    old = _newest_first(user_id).with_only_columns(AssistantMessage.id).offset(keep)
    db.execute(delete(AssistantMessage).where(AssistantMessage.id.in_(old)))


def clear(db: Session, user_id: int) -> None:
    """Delete all of an account's messages."""
    db.execute(delete(AssistantMessage).where(AssistantMessage.user_id == user_id))
