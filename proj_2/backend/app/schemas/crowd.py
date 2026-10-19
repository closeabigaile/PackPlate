"""Request and response models for crowd reports."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

CrowdLevel = Literal["not_busy", "moderate", "crowded"]


class CrowdReportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: CrowdLevel


class Crowd(BaseModel):
    level: CrowdLevel | None  # null = no recent reports: unknown, not "not busy"
    report_count: int  # reports in the window
    last_reported_at: datetime | None
