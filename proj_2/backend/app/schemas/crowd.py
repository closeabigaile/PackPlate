"""Request and response models for crowd reports."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

CrowdLevel = Literal["not_busy", "moderate", "crowded"]


class CrowdReportIn(BaseModel):
    """A student's report of how busy a location is right now. Extra fields are rejected."""

    model_config = ConfigDict(extra="forbid")
    level: CrowdLevel


class Crowd(BaseModel):
    """A location's current crowd level, worked out from recent student reports."""

    level: CrowdLevel | None  # null = no recent reports: unknown, not "not busy"
    report_count: int  # reports in the window
    last_reported_at: datetime | None
