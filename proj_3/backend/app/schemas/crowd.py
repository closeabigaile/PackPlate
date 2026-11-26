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


class CrowdForecast(BaseModel):
    """Predicted crowd level from the time of day and opening hours: no student input needed."""

    level: CrowdLevel | None  # the forecast alone; null = closed or hours unknown
    estimate: CrowdLevel | None  # forecast combined with any recent student reports
    source: Literal["forecast", "reports", "forecast+reports", "none"]
