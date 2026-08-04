from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import select

from tonus_bot.persistence.models import WeeklyInsightRecord
from tonus_bot.persistence.types import WeeklyInsight
from tonus_bot.persistence.utils import to_weekly_insight, utc_now


class InsightStore:
    async def save_insight(
        self, *, user_id: int, week_start: date, insight_text: str, raw_stats: dict | None
    ) -> WeeklyInsight:
        return await asyncio.to_thread(self._save_insight_sync, user_id, week_start, insight_text, raw_stats)

    def _save_insight_sync(
        self, user_id: int, week_start: date, insight_text: str, raw_stats: dict | None
    ) -> WeeklyInsight:
        with self._session_factory() as session:
            record = WeeklyInsightRecord(
                user_id=user_id,
                week_start=week_start,
                insight_text=insight_text,
                raw_stats=raw_stats,
                created_at=utc_now(),
            )
            session.add(record)
            session.commit()
            return to_weekly_insight(record)

    async def get_latest_insight(self, user_id: int) -> WeeklyInsight | None:
        return await asyncio.to_thread(self._get_latest_insight_sync, user_id)

    def _get_latest_insight_sync(self, user_id: int) -> WeeklyInsight | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(WeeklyInsightRecord)
                .where(WeeklyInsightRecord.user_id == user_id)
                .order_by(WeeklyInsightRecord.week_start.desc())
                .limit(1)
            )
            return to_weekly_insight(record) if record is not None else None

    async def get_insight_for_week(self, user_id: int, week_start: date) -> WeeklyInsight | None:
        return await asyncio.to_thread(self._get_insight_for_week_sync, user_id, week_start)

    def _get_insight_for_week_sync(self, user_id: int, week_start: date) -> WeeklyInsight | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(WeeklyInsightRecord).where(
                    WeeklyInsightRecord.user_id == user_id, WeeklyInsightRecord.week_start == week_start
                )
            )
            return to_weekly_insight(record) if record is not None else None
