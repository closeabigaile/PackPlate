"""Predicted crowd level: no student input needed.

Goes in backend/app/services/crowd_forecast.py. Pure functions, no database.

The forecast comes from three things PackPlate already knows or can know for free:
  1. The time of day: meal rushes (a hand-tuned curve, easy to adjust below).
  2. The opening hours already stored in HoursDay: crowds are thin right after
     opening and right before closing, and a closed location has no crowd.
  3. A campus-calendar factor: breaks and exam weeks (fill in CALENDAR below).

Student reports stay optional: if any exist in the window they pull the level
toward what students saw, but nobody is ever asked to report.
"""

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.services.hours import periods

LEVELS = ("not_busy", "moderate", "crowded")

# (peak hour in 24h decimal, spread in hours, height 0..1)
# Hand-tuned guesses: adjust after you compare with what you see in person.
WEEKDAY_PEAKS = [(8.25, 0.6, 0.45), (12.25, 0.8, 1.0), (18.0, 1.0, 0.85)]
WEEKEND_PEAKS = [(10.5, 0.8, 0.35), (12.5, 1.0, 0.6), (18.0, 1.0, 0.55)]

BASE_LOAD = 0.08  # some people eat at any hour while open
EDGE_MINUTES = 30  # crowds ramp up over the first / last 30 min of an open period

# Calendar factors: date range -> multiplier. Fill in from the official NC State
# academic calendar; the entry below is a placeholder, not a real date.
CALENDAR: list[tuple[date, date, float]] = [
    # (date(2026, 11, 25), date(2026, 11, 29), 0.3),  # Thanksgiving break
]

# Optional per-location scale if some places run bigger than others (by location id).
LOCATION_SCALE: dict[int, float] = {}

# Weight of the forecast when blended with live reports, counted like one fresh report.
PRIOR_WEIGHT = 1.0


@dataclass
class Forecast:
    level: str | None  # None = closed or unknown hours
    score: float | None  # 0..1 before bucketing


def _curve(hour: float, peaks) -> float:
    return min(
        1.0,
        BASE_LOAD
        + sum(h * math.exp(-((hour - p) ** 2) / (2 * s**2)) for p, s, h in peaks),
    )


def calendar_factor(day: date) -> float:
    for start, end, factor in CALENDAR:
        if start <= day <= end:
            return factor
    return 1.0


def _edge_factor(at: datetime, period: tuple[datetime, datetime]) -> float:
    opens, closes = period
    edge = timedelta(minutes=EDGE_MINUTES)
    since, until = at - opens, closes - at
    return max(0.2, min(1.0, since / edge, until / edge))


def bucket(score: float) -> str:
    return LEVELS[0] if score < 0.35 else LEVELS[1] if score < 0.7 else LEVELS[2]


def forecast(
    at: datetime, open_period: tuple[datetime, datetime] | None, location_id: int = 0
) -> Forecast:
    """open_period: the (opens, closes) period containing `at`, or None if closed/unknown."""
    if open_period is None:
        return Forecast(None, None)
    peaks = WEEKEND_PEAKS if at.weekday() >= 5 else WEEKDAY_PEAKS
    hour = at.hour + at.minute / 60
    score = (
        _curve(hour, peaks)
        * _edge_factor(at, open_period)
        * calendar_factor(at.date())
        * LOCATION_SCALE.get(location_id, 1.0)
    )
    score = max(0.0, min(1.0, score))
    return Forecast(bucket(score), score)


def blend(forecast_score: float | None, reports, at: datetime, window: timedelta):
    """Combine the forecast (as a prior) with optional reports. Returns (level, source).

    reports: (level, created_at) pairs. Each counts like in services.crowd.aggregate
    (weight 1 when new, falling to 0 at the window's end).
    """
    recent = [(lv, t) for lv, t in reports if at - window < t <= at]
    if forecast_score is None and not recent:
        return None, "none"
    if not recent:
        return bucket(forecast_score), "forecast"
    total = weights = 0.0
    if forecast_score is not None:
        total, weights = PRIOR_WEIGHT * forecast_score * 2, PRIOR_WEIGHT  # 0..1 -> 0..2
    for level, created in recent:
        w = 1 - (at - created) / window
        total += w * LEVELS.index(level)
        weights += w
    mean = total / weights
    level = LEVELS[0] if mean < 0.5 else LEVELS[1] if mean < 1.5 else LEVELS[2]
    return level, "forecast+reports" if forecast_score is not None else "reports"


def current_period(at: datetime, today, yesterday) -> tuple[datetime, datetime] | None:
    """The open period containing `at`, from HoursDay rows for at's date and the day before.

    Checks yesterday first because a close at or past midnight runs into today.
    Returns None if closed, or if the hours are unknown.
    """
    for row in (yesterday, today):
        if row is not None and row.status == "open":
            for opens, closes in periods(row.date, row.windows):
                if opens <= at < closes:
                    return opens, closes
    return None
