"""Routes for a logged-in user's saved dietary profile (M5).

Logged out, the profile lives only in the browser, as before. Logged in, the
frontend keeps a copy on the account here so it follows the user to any device
and is used by My diet, Menus, Compare Meals, and Eat as a group. The filter and
recommendation endpoints still take the profile in the request body.
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.deps import current_user, get_db
from app.repositories import profiles as profiles_repo
from app.schemas.filters import Profile
from db.models import User

router = APIRouter(prefix="/profile", tags=["profile"])


def _out(row) -> Profile | None:
    if row is None:
        return None
    return Profile(**{field: getattr(row, field) for field in profiles_repo.FIELDS})


@router.get("", response_model=Profile | None)
def get_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The logged-in user's saved profile, or null if they haven't saved one. 401 when logged out."""
    return _out(profiles_repo.get(db, user.id))


@router.put("", response_model=Profile)
def put_profile(
    body: Profile, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    """Save (create or replace) the logged-in user's profile. Same rules as a filter
    request's profile: unknown allergens, diets, or fields are a 422.
    """
    values = body.model_dump()
    values["name"] = (values["name"] or "").strip() or None
    # Keep each key once, in the order given.
    values["avoid"] = list(dict.fromkeys(values["avoid"]))
    values["diets"] = list(dict.fromkeys(values["diets"]))
    return _out(profiles_repo.save(db, user.id, values))


@router.delete("", status_code=204, response_class=Response)
def delete_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Remove the logged-in user's saved profile. Succeeds if there wasn't one."""
    profiles_repo.delete_for(db, user.id)
    return Response(status_code=204)
