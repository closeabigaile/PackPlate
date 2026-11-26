"""Queries for logged-in users' saved dietary profiles (M5)."""

from sqlalchemy import delete
from sqlalchemy.orm import Session

from db.models import DietProfile

FIELDS = ("name", "avoid", "diets", "min_protein_g", "max_calories", "max_sodium_mg")


def get(db: Session, user_id: int) -> DietProfile | None:
    """The account's saved profile, if it has one."""
    return db.get(DietProfile, user_id)


def save(db: Session, user_id: int, values: dict) -> DietProfile:
    """Create or replace the account's profile with these FIELDS."""
    row = db.get(DietProfile, user_id)
    if row is None:
        row = DietProfile(user_id=user_id)
        db.add(row)
    for field in FIELDS:
        setattr(row, field, values.get(field))
    db.commit()
    return row


def delete_for(db: Session, user_id: int):
    """Remove the account's profile. Does nothing if there isn't one."""
    db.execute(delete(DietProfile).where(DietProfile.user_id == user_id))
    db.commit()
