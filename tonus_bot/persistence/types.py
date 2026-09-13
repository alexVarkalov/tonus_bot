from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Checkin:
    id: int
    user_id: int
    date: date
    mood: int
    productivity: int
    note: str | None
    tags: tuple[str, ...] | None
    sleep_hours: float | None
    steps: int | None
    created_at: datetime


@dataclass(frozen=True)
class WeeklyInsight:
    id: int
    user_id: int
    week_start: date
    insight_text: str
    raw_stats: dict | None
    created_at: datetime


@dataclass(frozen=True)
class UserSettings:
    user_id: int
    checkin_hour: int
    timezone: str
    reminders_enabled: bool
    language: str
