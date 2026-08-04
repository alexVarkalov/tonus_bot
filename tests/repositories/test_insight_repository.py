from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock

import pytest

from tonus_bot.repositories.insight_repository import InsightRepository


@pytest.mark.asyncio
async def test_save_forwards_fields() -> None:
    db = AsyncMock()
    repo = InsightRepository(db)

    await repo.save(user_id=1, week_start=date(2026, 1, 5), insight_text="text", raw_stats={"a": 1})

    db.save_insight.assert_awaited_once_with(
        user_id=1, week_start=date(2026, 1, 5), insight_text="text", raw_stats={"a": 1}
    )


@pytest.mark.asyncio
async def test_get_latest_delegates_to_db() -> None:
    db = AsyncMock()
    repo = InsightRepository(db)

    await repo.get_latest(1)

    db.get_latest_insight.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_for_week_delegates_to_db() -> None:
    db = AsyncMock()
    repo = InsightRepository(db)

    await repo.get_for_week(1, date(2026, 1, 5))

    db.get_insight_for_week.assert_awaited_once_with(1, date(2026, 1, 5))
