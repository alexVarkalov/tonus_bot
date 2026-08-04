from __future__ import annotations

from datetime import date

from tonus_bot.db import Database
from tonus_bot.persistence import WeeklyInsight


class InsightRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def save(self, *, user_id: int, week_start: date, insight_text: str, raw_stats: dict | None) -> WeeklyInsight:
        return await self._db.save_insight(
            user_id=user_id, week_start=week_start, insight_text=insight_text, raw_stats=raw_stats
        )

    async def get_latest(self, user_id: int) -> WeeklyInsight | None:
        return await self._db.get_latest_insight(user_id)

    async def get_for_week(self, user_id: int, week_start: date) -> WeeklyInsight | None:
        return await self._db.get_insight_for_week(user_id, week_start)
