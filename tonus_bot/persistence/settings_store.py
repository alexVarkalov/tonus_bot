from __future__ import annotations

import asyncio

from sqlalchemy import select

from tonus_bot.persistence.models import UserSettingsRecord
from tonus_bot.persistence.types import UserSettings
from tonus_bot.persistence.utils import to_user_settings


class SettingsStore:
    async def get_settings(self, user_id: int) -> UserSettings | None:
        return await asyncio.to_thread(self._get_settings_sync, user_id)

    def _get_settings_sync(self, user_id: int) -> UserSettings | None:
        with self._session_factory() as session:
            record = session.scalar(select(UserSettingsRecord).where(UserSettingsRecord.user_id == user_id))
            return to_user_settings(record) if record is not None else None

    async def ensure_settings(self, user_id: int, *, default_timezone: str, default_checkin_hour: int) -> UserSettings:
        return await asyncio.to_thread(self._ensure_settings_sync, user_id, default_timezone, default_checkin_hour)

    def _ensure_settings_sync(self, user_id: int, default_timezone: str, default_checkin_hour: int) -> UserSettings:
        with self._session_factory() as session:
            record = session.scalar(select(UserSettingsRecord).where(UserSettingsRecord.user_id == user_id))
            if record is None:
                record = UserSettingsRecord(
                    user_id=user_id,
                    checkin_hour=default_checkin_hour,
                    timezone=default_timezone,
                    reminders_enabled=True,
                    language="en",
                )
                session.add(record)
                session.commit()
            return to_user_settings(record)

    async def set_checkin_hour(self, user_id: int, hour: int) -> UserSettings:
        return await asyncio.to_thread(self._set_checkin_hour_sync, user_id, hour)

    def _set_checkin_hour_sync(self, user_id: int, hour: int) -> UserSettings:
        with self._session_factory() as session:
            record = session.scalar(select(UserSettingsRecord).where(UserSettingsRecord.user_id == user_id))
            if record is None:
                record = UserSettingsRecord(user_id=user_id, checkin_hour=hour)
                session.add(record)
            else:
                record.checkin_hour = hour
            session.commit()
            return to_user_settings(record)

    async def set_timezone(self, user_id: int, timezone: str) -> UserSettings:
        return await asyncio.to_thread(self._set_timezone_sync, user_id, timezone)

    def _set_timezone_sync(self, user_id: int, timezone: str) -> UserSettings:
        with self._session_factory() as session:
            record = session.scalar(select(UserSettingsRecord).where(UserSettingsRecord.user_id == user_id))
            if record is None:
                record = UserSettingsRecord(user_id=user_id, timezone=timezone)
                session.add(record)
            else:
                record.timezone = timezone
            session.commit()
            return to_user_settings(record)

    async def set_reminders_enabled(self, user_id: int, enabled: bool) -> UserSettings:
        return await asyncio.to_thread(self._set_reminders_enabled_sync, user_id, enabled)

    def _set_reminders_enabled_sync(self, user_id: int, enabled: bool) -> UserSettings:
        with self._session_factory() as session:
            record = session.scalar(select(UserSettingsRecord).where(UserSettingsRecord.user_id == user_id))
            if record is None:
                record = UserSettingsRecord(user_id=user_id, reminders_enabled=enabled)
                session.add(record)
            else:
                record.reminders_enabled = enabled
            session.commit()
            return to_user_settings(record)

    async def set_language(self, user_id: int, language: str) -> UserSettings:
        return await asyncio.to_thread(self._set_language_sync, user_id, language)

    def _set_language_sync(self, user_id: int, language: str) -> UserSettings:
        with self._session_factory() as session:
            record = session.scalar(select(UserSettingsRecord).where(UserSettingsRecord.user_id == user_id))
            if record is None:
                record = UserSettingsRecord(user_id=user_id, language=language)
                session.add(record)
            else:
                record.language = language
            session.commit()
            return to_user_settings(record)
