from __future__ import annotations

from datetime import UTC, date, datetime

from tonus_bot.persistence import Checkin, UserSettings, WeeklyInsight


def make_checkin(**overrides: object) -> Checkin:
    defaults: dict[str, object] = {
        "id": 1,
        "user_id": 123,
        "date": date(2026, 1, 1),
        "mood": 5,
        "productivity": 4,
        "note": None,
        "tags": None,
        "sleep_hours": None,
        "steps": None,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Checkin(**defaults)


def make_user_settings(**overrides: object) -> UserSettings:
    defaults: dict[str, object] = {
        "user_id": 123,
        "checkin_hour": 21,
        "timezone": "Europe/Warsaw",
        "reminders_enabled": True,
    }
    defaults.update(overrides)
    return UserSettings(**defaults)


def make_weekly_insight(**overrides: object) -> WeeklyInsight:
    defaults: dict[str, object] = {
        "id": 1,
        "user_id": 123,
        "week_start": date(2026, 1, 5),
        "insight_text": "insight",
        "raw_stats": None,
        "created_at": datetime(2026, 1, 5, tzinfo=UTC),
    }
    defaults.update(overrides)
    return WeeklyInsight(**defaults)
