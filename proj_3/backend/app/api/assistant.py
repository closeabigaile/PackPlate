"""Routes for the dining assistant (M3): send a message, read and clear history.

Every route needs a logged-in user (M1's current_user, 401 otherwise); the
account comes from the session cookie, never from the request body. The
assistant itself lives in services/assistant/; this file only checks the
request, applies the rate limit, and saves the conversation.

The dietary profile comes in the request body (POST), so it never lands in a URL
or a log, and it is not stored. Only the message text and the reply are.
"""

import math
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.deps import current_user, get_db
from app.repositories import assistant as assistant_repo
from app.schemas.assistant import MessageIn, MessageOut, ReplyOut
from app.schemas.filters import Profile
from app.services import filter_engine
from app.services.assistant import chat, settings
from app.services.assistant.limits import RateLimiter
from app.services.hours import campus_time
from db.models import User


def _require_enabled():
    """404 on every route while the assistant is switched off (ASSISTANT_ENABLED=false)."""
    if not settings.enabled():
        raise HTTPException(status_code=404, detail="the assistant is turned off")


router = APIRouter(
    prefix="/assistant", tags=["assistant"], dependencies=[Depends(_require_enabled)]
)

_limiter = RateLimiter(settings.RATE_PER_MINUTE, 60)


def get_limiter() -> RateLimiter:
    """The shared per-account limiter, as a dependency so tests can swap in their own."""
    return _limiter


def _engine_profile(profile: Profile | None) -> filter_engine.Profile:
    """The request's profile in the form the filter engine reads (none = no restrictions)."""
    if profile is None:
        return filter_engine.Profile()
    return filter_engine.Profile(
        avoid=frozenset(profile.avoid),
        diets=frozenset(profile.diets),
        min_protein_g=profile.min_protein_g,
        max_calories=profile.max_calories,
        max_sodium_mg=profile.max_sodium_mg,
    )


@router.post("/messages", response_model=ReplyOut, status_code=201)
def send_message(
    body: MessageIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    limiter: RateLimiter = Depends(get_limiter),
):
    """Ask the assistant something. Returns its reply, and saves both messages.

    429 (with Retry-After) when the account is asking too fast.
    """
    retry_after = limiter.hit(user.id)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="you are asking too fast; wait a moment",
            headers={"Retry-After": str(math.ceil(retry_after))},
        )
    # The latest few messages, read before this one is saved, give a follow-up
    # question like "what about tomorrow?" something to refer to.
    history = [
        {"role": m.role, "text": m.text}
        for m in assistant_repo.recent(db, user.id, settings.MODEL_HISTORY_MESSAGES)
    ]
    answer = chat.respond(
        db, body.text, _engine_profile(body.profile), body.at, history
    )
    now = campus_time()
    assistant_repo.add_message(db, user.id, "user", body.text, [], now)
    assistant_repo.add_message(
        db, user.id, "assistant", answer["reply"], answer["cards"], now
    )
    assistant_repo.trim(db, user.id, settings.HISTORY_LIMIT)
    db.commit()
    return answer


@router.get("/messages", response_model=list[MessageOut])
def list_messages(
    limit: int = Query(50, ge=1, le=settings.HISTORY_LIMIT),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """The logged-in account's latest messages, oldest first. Never anyone else's."""
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            text=m.text,
            cards=m.cards,
            created_at=m.created_at.astimezone(UTC),
        )
        for m in assistant_repo.recent(db, user.id, limit)
    ]


@router.delete("/messages", status_code=204)
def clear_messages(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Delete the logged-in account's whole conversation."""
    assistant_repo.clear(db, user.id)
    db.commit()
    return Response(status_code=204)
