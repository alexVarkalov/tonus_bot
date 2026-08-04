from __future__ import annotations

from datetime import UTC, datetime

from tonus_bot.persistence.models import CheckinRecord, UserSettingsRecord, WeeklyInsightRecord
from tonus_bot.persistence.types import Checkin, UserSettings, WeeklyInsight


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def to_checkin(record: CheckinRecord) -> Checkin:
    return Checkin(
        id=record.id,
        user_id=record.user_id,
        date=record.date,
        mood=record.mood,
        productivity=record.productivity,
        note=record.note,
        tags=tuple(record.tags) if record.tags else None,
        sleep_hours=record.sleep_hours,
        steps=record.steps,
        created_at=record.created_at,
    )


def to_weekly_insight(record: WeeklyInsightRecord) -> WeeklyInsight:
    return WeeklyInsight(
        id=record.id,
        user_id=record.user_id,
        week_start=record.week_start,
        insight_text=record.insight_text,
        raw_stats=record.raw_stats,
        created_at=record.created_at,
    )


def to_user_settings(record: UserSettingsRecord) -> UserSettings:
    return UserSettings(
        user_id=record.user_id,
        checkin_hour=record.checkin_hour,
        timezone=record.timezone,
        reminders_enabled=bool(record.reminders_enabled),
    )
