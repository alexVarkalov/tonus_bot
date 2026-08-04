from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock

import pytest

from tonus_bot.repositories.checkin_repository import CheckinRepository


@pytest.mark.asyncio
async def test_save_forwards_fields() -> None:
    db = AsyncMock()
    repo = CheckinRepository(db)

    await repo.save(user_id=1, checkin_date=date(2026, 1, 1), mood=5, productivity=4, note="note")

    db.upsert_checkin.assert_awaited_once_with(
        user_id=1, checkin_date=date(2026, 1, 1), mood=5, productivity=4, note="note", tags=None
    )


@pytest.mark.asyncio
async def test_get_delegates_to_db() -> None:
    db = AsyncMock()
    repo = CheckinRepository(db)

    await repo.get(1, date(2026, 1, 1))

    db.get_checkin.assert_awaited_once_with(1, date(2026, 1, 1))


@pytest.mark.asyncio
async def test_get_range_delegates_to_db() -> None:
    db = AsyncMock()
    repo = CheckinRepository(db)

    await repo.get_range(1, date(2026, 1, 1), date(2026, 1, 7))

    db.get_checkins_range.assert_awaited_once_with(1, date(2026, 1, 1), date(2026, 1, 7))


@pytest.mark.asyncio
async def test_update_enrichment_delegates_to_db() -> None:
    db = AsyncMock()
    repo = CheckinRepository(db)

    await repo.update_enrichment(1, date(2026, 1, 1), 7.5, 5000)

    db.update_enrichment.assert_awaited_once_with(1, date(2026, 1, 1), 7.5, 5000)
