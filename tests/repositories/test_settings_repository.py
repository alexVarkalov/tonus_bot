from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from tonus_bot.repositories.settings_repository import SettingsRepository


@pytest.mark.asyncio
async def test_get_delegates_to_db() -> None:
    db = AsyncMock()
    repo = SettingsRepository(db)

    await repo.get(1)

    db.get_settings.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_ensure_forwards_defaults() -> None:
    db = AsyncMock()
    repo = SettingsRepository(db)

    await repo.ensure(1, default_timezone="Europe/Warsaw", default_checkin_hour=21)

    db.ensure_settings.assert_awaited_once_with(1, default_timezone="Europe/Warsaw", default_checkin_hour=21)


@pytest.mark.asyncio
async def test_setters_delegate_to_db() -> None:
    db = AsyncMock()
    repo = SettingsRepository(db)

    await repo.set_checkin_hour(1, 8)
    await repo.set_timezone(1, "UTC")
    await repo.set_reminders_enabled(1, False)

    db.set_checkin_hour.assert_awaited_once_with(1, 8)
    db.set_timezone.assert_awaited_once_with(1, "UTC")
    db.set_reminders_enabled.assert_awaited_once_with(1, False)
