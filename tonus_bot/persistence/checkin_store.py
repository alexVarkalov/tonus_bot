from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from tonus_bot.persistence.models import CheckinRecord
from tonus_bot.persistence.types import Checkin
from tonus_bot.persistence.utils import to_checkin, utc_now


class CheckinStore:
    async def upsert_checkin(
        self,
        *,
        user_id: int,
        checkin_date: date,
        mood: int,
        productivity: int,
        note: str | None,
        tags: list[str] | None = None,
    ) -> Checkin:
        return await asyncio.to_thread(self._upsert_checkin_sync, user_id, checkin_date, mood, productivity, note, tags)

    def _upsert_checkin_sync(
        self,
        user_id: int,
        checkin_date: date,
        mood: int,
        productivity: int,
        note: str | None,
        tags: list[str] | None,
    ) -> Checkin:
        now = utc_now()
        with self._session_factory() as session:
            stmt = pg_insert(CheckinRecord).values(
                user_id=user_id,
                date=checkin_date,
                mood=mood,
                productivity=productivity,
                note=note,
                tags=tags,
                created_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "date"],
                set_={
                    "mood": stmt.excluded.mood,
                    "productivity": stmt.excluded.productivity,
                    "note": stmt.excluded.note,
                    "tags": stmt.excluded.tags,
                },
            )
            session.execute(stmt)
            record = session.scalar(
                select(CheckinRecord).where(CheckinRecord.user_id == user_id, CheckinRecord.date == checkin_date)
            )
            session.commit()
            if record is None:
                msg = "failed to read checkin after upsert"
                raise RuntimeError(msg)
            return to_checkin(record)

    async def get_checkin(self, user_id: int, checkin_date: date) -> Checkin | None:
        return await asyncio.to_thread(self._get_checkin_sync, user_id, checkin_date)

    def _get_checkin_sync(self, user_id: int, checkin_date: date) -> Checkin | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(CheckinRecord).where(CheckinRecord.user_id == user_id, CheckinRecord.date == checkin_date)
            )
            return to_checkin(record) if record is not None else None

    async def get_checkins_range(self, user_id: int, start_date: date, end_date: date) -> list[Checkin]:
        return await asyncio.to_thread(self._get_checkins_range_sync, user_id, start_date, end_date)

    def _get_checkins_range_sync(self, user_id: int, start_date: date, end_date: date) -> list[Checkin]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(CheckinRecord)
                .where(
                    CheckinRecord.user_id == user_id,
                    CheckinRecord.date >= start_date,
                    CheckinRecord.date <= end_date,
                )
                .order_by(CheckinRecord.date)
            ).all()
            return [to_checkin(record) for record in rows]

    async def update_enrichment(
        self, user_id: int, checkin_date: date, sleep_hours: float | None, steps: int | None
    ) -> Checkin | None:
        return await asyncio.to_thread(self._update_enrichment_sync, user_id, checkin_date, sleep_hours, steps)

    def _update_enrichment_sync(
        self, user_id: int, checkin_date: date, sleep_hours: float | None, steps: int | None
    ) -> Checkin | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(CheckinRecord).where(CheckinRecord.user_id == user_id, CheckinRecord.date == checkin_date)
            )
            if record is None:
                return None
            record.sleep_hours = sleep_hours
            record.steps = steps
            session.commit()
            return to_checkin(record)
