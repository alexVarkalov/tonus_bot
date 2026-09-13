from __future__ import annotations

from tonus_bot.db import Database
from tonus_bot.persistence import UserSettings


class SettingsRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def get(self, user_id: int) -> UserSettings | None:
        return await self._db.get_settings(user_id)

    async def ensure(self, user_id: int, *, default_timezone: str, default_checkin_hour: int) -> UserSettings:
        return await self._db.ensure_settings(
            user_id, default_timezone=default_timezone, default_checkin_hour=default_checkin_hour
        )

    async def set_checkin_hour(self, user_id: int, hour: int) -> UserSettings:
        return await self._db.set_checkin_hour(user_id, hour)

    async def set_timezone(self, user_id: int, timezone: str) -> UserSettings:
        return await self._db.set_timezone(user_id, timezone)

    async def set_reminders_enabled(self, user_id: int, enabled: bool) -> UserSettings:
        return await self._db.set_reminders_enabled(user_id, enabled)

    async def set_language(self, user_id: int, language: str) -> UserSettings:
        return await self._db.set_language(user_id, language)
