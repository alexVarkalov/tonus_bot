from __future__ import annotations

from datetime import date

from tonus_bot.db import Database
from tonus_bot.persistence import Checkin


class CheckinRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def save(
        self,
        *,
        user_id: int,
        checkin_date: date,
        mood: int,
        productivity: int,
        note: str | None,
        tags: list[str] | None = None,
    ) -> Checkin:
        return await self._db.upsert_checkin(
            user_id=user_id,
            checkin_date=checkin_date,
            mood=mood,
            productivity=productivity,
            note=note,
            tags=tags,
        )

    async def get(self, user_id: int, checkin_date: date) -> Checkin | None:
        return await self._db.get_checkin(user_id, checkin_date)

    async def get_range(self, user_id: int, start_date: date, end_date: date) -> list[Checkin]:
        return await self._db.get_checkins_range(user_id, start_date, end_date)

    async def update_enrichment(
        self, user_id: int, checkin_date: date, sleep_hours: float | None, steps: int | None
    ) -> Checkin | None:
        return await self._db.update_enrichment(user_id, checkin_date, sleep_hours, steps)
