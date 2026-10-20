"""Request and response models for dietary filtering.

Profiles are checked and returned, never stored. Unknown fields and unknown
allergen or diet keys are rejected (422): a typo must not be ignored and
quietly turn every item into "fits".
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.locations import MenuItem, MenuSummary

# Must match services/filter_engine.py ALLERGEN_KEYS / DIET_KEYS (a test checks).
Allergen = Literal["dairy", "egg", "gluten", "nuts", "pork", "seafood", "sesame", "soy"]
Diet = Literal["halal", "vegan", "vegetarian"]
Verdict = Literal["fits", "conflicts", "incomplete"]

MAX_PROFILES = 10


class Profile(BaseModel):
    """One person's dietary needs in a filter request.

    Unknown fields, allergens, or diets are rejected (422), never ignored.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, max_length=50)  # echoed back, e.g. "Sam"
    avoid: list[Allergen] = []  # allergens to avoid
    diets: list[Diet] = []  # diets the item must meet, all of them
    min_protein_g: float | None = Field(None, ge=0, le=1000)
    max_calories: float | None = Field(None, ge=0, le=10000)
    max_sodium_mg: float | None = Field(None, ge=0, le=100000)


class FilterRequest(BaseModel):
    """The body of both filter endpoints: 1 to MAX_PROFILES profiles."""

    model_config = ConfigDict(extra="forbid")
    profiles: list[Profile] = Field(min_length=1, max_length=MAX_PROFILES)


class ItemResult(BaseModel):
    """One item's verdict for one profile, and why it isn't "fits"."""

    verdict: Verdict
    reasons: list[
        str
    ]  # why it doesn't fit, or what we couldn't check; empty for "fits"


class FilteredItem(MenuItem):
    """A menu item with one result per profile, in request order."""

    results: list[ItemResult]  # one per profile, in request order


class FilteredMenu(MenuSummary):
    """A menu whose items are each checked against every profile."""

    items: list[FilteredItem]


class ProfileCounts(BaseModel):
    """For one profile at one location: how many items fit, are incomplete, or conflict."""

    name: str | None
    fits: int
    incomplete: int
    conflicts: int


class GroupLocation(BaseModel):
    """One location's answer for a group: is it open, and does everyone have something that fits."""

    id: int
    name: str
    is_open: bool | None  # at `at`; null = hours unknown
    closes_at: datetime | None
    opens_next_at: datetime | None
    items_checked: int  # menu items that day; 0 = no menu scraped
    everyone_fits: bool  # every profile has at least one item that fits
    profiles: list[ProfileCounts]  # one per profile, in request order
