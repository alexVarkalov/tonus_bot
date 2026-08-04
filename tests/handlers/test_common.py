from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tonus_bot.config import Settings
from tonus_bot.handlers.common import ensure_user_settings, guard, is_allowed, local_today


def _settings(allowed_user_id: int = 100) -> Settings:
    return Settings(
        bot_token="token",
        database_url="postgresql+psycopg://u:p@localhost:5432/tonus",
        anthropic_api_key="key",
        allowed_user_id=allowed_user_id,
        gadgetbridge_db_path=None,
        default_timezone="UTC",
        checkin_reminder_hour=21,
    )


def test_is_allowed_true_for_matching_user() -> None:
    update = SimpleNamespace(effective_user=SimpleNamespace(id=100))
    assert is_allowed(update, _settings(100)) is True


def test_is_allowed_false_for_other_user() -> None:
    update = SimpleNamespace(effective_user=SimpleNamespace(id=999))
    assert is_allowed(update, _settings(100)) is False


def test_is_allowed_false_without_effective_user() -> None:
    update = SimpleNamespace(effective_user=None)
    assert is_allowed(update, _settings(100)) is False


@pytest.mark.asyncio
async def test_guard_false_without_effective_message() -> None:
    update = SimpleNamespace(effective_user=SimpleNamespace(id=100), effective_message=None)
    context = SimpleNamespace(application=SimpleNamespace(bot_data={"settings": _settings(100)}))

    assert await guard(update, context) is False


@pytest.mark.asyncio
async def test_guard_false_for_other_user() -> None:
    update = SimpleNamespace(effective_user=SimpleNamespace(id=999), effective_message=SimpleNamespace())
    context = SimpleNamespace(application=SimpleNamespace(bot_data={"settings": _settings(100)}))

    assert await guard(update, context) is False


@pytest.mark.asyncio
async def test_guard_true_for_allowed_user() -> None:
    update = SimpleNamespace(effective_user=SimpleNamespace(id=100), effective_message=SimpleNamespace())
    context = SimpleNamespace(application=SimpleNamespace(bot_data={"settings": _settings(100)}))

    assert await guard(update, context) is True


@pytest.mark.asyncio
async def test_ensure_user_settings_forwards_defaults() -> None:
    settings_repo = AsyncMock()
    context = SimpleNamespace(
        application=SimpleNamespace(bot_data={"settings": _settings(100), "settings_repository": settings_repo})
    )

    await ensure_user_settings(context, 100)

    settings_repo.ensure.assert_awaited_once_with(100, default_timezone="UTC", default_checkin_hour=21)


def test_local_today_converts_timezone() -> None:
    now_utc = datetime(2026, 1, 1, 23, 0, tzinfo=UTC)
    assert local_today(now_utc, "Europe/Warsaw") == datetime(2026, 1, 2, tzinfo=UTC).date()
