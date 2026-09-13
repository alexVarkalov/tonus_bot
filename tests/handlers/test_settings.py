from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.helpers import make_user_settings
from tonus_bot.config import Settings
from tonus_bot.handlers.settings import cmd_settings


def _settings() -> Settings:
    return Settings(
        bot_token="token",
        database_url="postgresql+psycopg://u:p@localhost:5432/tonus",
        anthropic_api_key="key",
        allowed_user_id=100,
        gadgetbridge_db_path=None,
        default_timezone="UTC",
        checkin_reminder_hour=21,
    )


def _bot_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {"settings": _settings(), "settings_repository": AsyncMock()}
    data.update(overrides)
    return data


def _context(args: list[str], bot_data: dict[str, object] | None = None) -> SimpleNamespace:
    return SimpleNamespace(application=SimpleNamespace(bot_data=bot_data or _bot_data()), args=args)


def _update(user_id: int = 100) -> SimpleNamespace:
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id), effective_message=SimpleNamespace(reply_text=AsyncMock())
    )


@pytest.mark.asyncio
async def test_cmd_settings_blocks_other_user() -> None:
    context = _context([])
    update = _update(user_id=999)

    await cmd_settings(update, context)

    update.effective_message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_cmd_settings_shows_current_without_args() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(
        checkin_hour=21, timezone="Europe/Warsaw", reminders_enabled=True, language="en"
    )
    context = _context([], bot_data)
    update = _update()

    await cmd_settings(update, context)

    text = update.effective_message.reply_text.await_args.args[0]
    assert "21:00" in text
    assert "Europe/Warsaw" in text
    assert "on" in text
    assert "en" in text


@pytest.mark.asyncio
async def test_cmd_settings_hour_updates_valid_value() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["hour", "8"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_checkin_hour.assert_awaited_once_with(100, 8)


@pytest.mark.asyncio
async def test_cmd_settings_hour_rejects_out_of_range() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["hour", "24"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_checkin_hour.assert_not_awaited()
    text = update.effective_message.reply_text.await_args.args[0]
    assert "0 and 23" in text


@pytest.mark.asyncio
async def test_cmd_settings_timezone_updates_valid_value() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["timezone", "Europe/Warsaw"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_timezone.assert_awaited_once_with(100, "Europe/Warsaw")


@pytest.mark.asyncio
async def test_cmd_settings_timezone_rejects_invalid_value() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["timezone", "Mars/Colony"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_timezone.assert_not_awaited()


@pytest.mark.asyncio
async def test_cmd_settings_reminders_toggles_on_and_off() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["reminders", "off"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_reminders_enabled.assert_awaited_once_with(100, False)


@pytest.mark.asyncio
async def test_cmd_settings_reminders_rejects_invalid_value() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["reminders", "maybe"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_reminders_enabled.assert_not_awaited()


@pytest.mark.asyncio
async def test_cmd_settings_language_updates_valid_value() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["language", "ru"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_language.assert_awaited_once_with(100, "ru")
    text = update.effective_message.reply_text.await_args.args[0]
    assert "ru" in text


@pytest.mark.asyncio
async def test_cmd_settings_language_rejects_invalid_value() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["language", "fr"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    bot_data["settings_repository"].set_language.assert_not_awaited()


@pytest.mark.asyncio
async def test_cmd_settings_unknown_subcommand_shows_usage() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(["bogus"], bot_data)
    update = _update()

    await cmd_settings(update, context)

    text = update.effective_message.reply_text.await_args.args[0]
    assert "Usage" in text
