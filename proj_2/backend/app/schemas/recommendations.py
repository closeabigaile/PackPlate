"""Request and response schemas for PackPlate M5 recommendations."""

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.filters import Profile
from app.schemas.locations import Nutrition

NutritionGoal = Literal[
    "high_protein",
    "lower_calories",
    "lower_sodium",
]


class RecommendationRequest(BaseModel):
    """Nutrition goal, menu filters, and optional dietary profile."""

    goal: NutritionGoal
    date: Date | None = None
    meal: str | None = None
    profile: Profile | None = None


class RecommendationItem(BaseModel):
    """A ranked meal with location, meal periods, and nutrition details."""

    rank: int
    item_id: int
    name: str
    location_id: int
    location_name: str
    meal: str
    meal_periods: list[str]
    nutrition: Nutrition
    reason: str


class RecommendationResponse(BaseModel):
    """The list of meals matching the recommendation request."""

    recommendations: list[RecommendationItem] = Field(default_factory=list)
