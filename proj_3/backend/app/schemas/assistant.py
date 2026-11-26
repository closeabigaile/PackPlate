"""Request and response models for the dining assistant (M3).

Unknown fields are rejected (422), and so are unknown allergens or diets in the
profile (the same Profile model the filter endpoints use), so a typo can't
quietly turn into "no restriction".
"""

from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.schemas.filters import Profile
from app.services.assistant import settings


class MessageIn(BaseModel):
    """A message to the assistant. The account comes from the login, not from here."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(pattern=r"\S", max_length=settings.MAX_MESSAGE_CHARS)
    # The person's dietary profile, sent with each message and never stored.
    profile: Profile | None = None
    at: AwareDatetime | None = None  # default now; lets tests and demos fix the time


class ReplyOut(BaseModel):
    """The assistant's reply, with result cards (menu items) to show beside it."""

    reply: str
    cards: list[dict[str, Any]]
    source: str  # "rules", or "fallback" when a built reply failed validation


class MessageOut(BaseModel):
    """One saved message in the account's history."""

    id: int
    role: Literal["user", "assistant"]
    text: str
    cards: list[dict[str, Any]]
    created_at: AwareDatetime
