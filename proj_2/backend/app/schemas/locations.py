"""Response models for locations, hours, and menus.

Unknown stays unknown: null means "not published" or "not scraped", never
zero, closed, or safe.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.crowd import Crowd


class Period(BaseModel):
    """One opening period, from opens_at to closes_at (campus time)."""

    opens_at: datetime
    closes_at: datetime


class HoursDay(BaseModel):
    """A location's hours on one date, as published on dining.ncsu.edu."""

    date: date
    status: Literal[
        "open", "closed", "unknown"
    ]  # unknown = no hours published or scraped
    periods: list[Period]
    raw_text: str | None  # as shown on dining.ncsu.edu


class LocationSummary(BaseModel):
    """A location with today's hours, whether it's open, and its crowd level."""

    id: int
    name: str
    description: str | None
    dining_url: str | None  # the location's dining.ncsu.edu page, if we know it
    is_open: bool | None  # null = today's hours are unknown
    closes_at: datetime | None
    opens_next_at: datetime | None  # next opening later today
    today: HoursDay
    crowd: Crowd  # from recent student reports (services/crowd.py)


class MenuSummary(BaseModel):
    """One meal's menu on one day, without its items."""

    id: int
    date: date
    meal: str
    scraped: bool  # false = listed by NetNutrition, items not scraped yet


class LocationDetail(LocationSummary):
    """A location's summary plus 7 days of hours (from today) and its menus from today on."""

    hours: list[HoursDay]  # today and the next 6 days
    menus: list[MenuSummary]  # today onward


class Nutrition(BaseModel):
    """An item's nutrition label from NetNutrition. Values it doesn't give are null, not zero."""

    serving_size: str | None
    calories: float | None
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None
    sodium_mg: float | None
    ingredients: str | None
    contains: list[str]  # the label's "Contains:" names, as printed
    missing_fields: list[str]  # nutrients the label doesn't give
    # Possible allergens the ingredients mention, e.g. {"dairy": ["whey"]}. Never
    # confirmed: shown as "check the label", never as "contains".
    ingredient_flags: dict[str, list[str]]
    fetched_at: datetime


class MenuItem(BaseModel):
    """One dish on a menu, with its allergens, diets, and nutrition label if it has one."""

    id: int
    name: str
    course: str | None  # station, e.g. "Grill Stations"
    serving_size: str | None
    allergens: list[str]  # icon traits plus the label's "Contains:" list
    diets: list[str]  # NC State's diet tags, minus any removed after review
    # Tags removed because a reviewer confirmed the ingredients contradict them,
    # with the reason, e.g. {"vegan": "ingredients list chicken"}.
    diets_removed: dict[str, str] = {}
    unrecognized_traits: list[str]  # names we have no key for: treat as data incomplete
    nutrition: Nutrition | None  # null = no label, so allergens come from icons only


class Menu(MenuSummary):
    """One meal's menu on one day, with its items."""

    items: list[MenuItem]
