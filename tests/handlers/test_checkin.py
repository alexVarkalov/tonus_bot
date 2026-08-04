from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from telegram.ext import ConversationHandler

from tests.helpers import make_checkin, make_user_settings
from tonus_bot.config import Settings
from tonus_bot.handlers import checkin as checkin_module
from tonus_bot.handlers.checkin import (
    CONFIRM_DATE,
    MOOD,
    NOTE,
    PRODUCTIVITY,
    cmd_cancel_checkin,
    cmd_checkin,
    cmd_skip_note,
    on_date_callback,
    on_mood_callback,
    on_note_text,
    on_productivity_callback,
    reminder_job,
)
from tonus_bot.services.checkin_service import CheckinDateResolution, CheckinService


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
    # spec=CheckinService so AsyncMock correctly makes resolve_checkin_date/validate_rating
    # (sync methods) plain Mocks instead of coroutine-returning AsyncMocks.
    data: dict[str, object] = {
        "settings": _settings(),
        "checkin_service": AsyncMock(spec=CheckinService),
        "settings_repository": AsyncMock(),
    }
    data.update(overrides)
    return data


def _context(bot_data: dict[str, object] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        application=SimpleNamespace(bot_data=bot_data or _bot_data()),
        user_data={},
        bot=AsyncMock(),
    )


def _update(user_id: int = 100, text: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        effective_message=SimpleNamespace(reply_text=AsyncMock(), text=text),
        callback_query=None,
    )


def _query(data: str) -> SimpleNamespace:
    return SimpleNamespace(
        data=data, answer=AsyncMock(), edit_message_text=AsyncMock(), edit_message_reply_markup=AsyncMock()
    )


@pytest.mark.asyncio
async def test_cmd_checkin_blocks_other_user() -> None:
    context = _context()
    update = _update(user_id=999)

    result = await cmd_checkin(update, context)

    assert result == ConversationHandler.END
    update.effective_message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_cmd_checkin_ambiguous_asks_confirmation() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    bot_data["checkin_service"].resolve_checkin_date.return_value = CheckinDateResolution(
        date=date(2026, 1, 1), is_ambiguous=True, alternate_date=date(2026, 1, 2)
    )
    context = _context(bot_data)
    update = _update()

    result = await cmd_checkin(update, context)

    assert result == CONFIRM_DATE
    assert context.user_data["checkin_date"] == date(2026, 1, 1)
    assert context.user_data["checkin_alternate_date"] == date(2026, 1, 2)
    update.effective_message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_checkin_not_ambiguous_asks_mood() -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    bot_data["checkin_service"].resolve_checkin_date.return_value = CheckinDateResolution(
        date=date(2026, 1, 2), is_ambiguous=False, alternate_date=None
    )
    context = _context(bot_data)
    update = _update()

    result = await cmd_checkin(update, context)

    assert result == MOOD
    assert context.user_data["checkin_date"] == date(2026, 1, 2)
    update.effective_message.reply_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_date_callback_switches_to_today() -> None:
    context = _context()
    context.user_data.update({"checkin_date": date(2026, 1, 1), "checkin_alternate_date": date(2026, 1, 2)})
    query = _query(checkin_module._DATE_CALLBACK_TODAY)
    update = SimpleNamespace(callback_query=query)

    result = await on_date_callback(update, context)

    assert result == MOOD
    assert context.user_data["checkin_date"] == date(2026, 1, 2)
    query.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_date_callback_keeps_yesterday() -> None:
    context = _context()
    context.user_data.update({"checkin_date": date(2026, 1, 1), "checkin_alternate_date": date(2026, 1, 2)})
    query = _query(checkin_module._DATE_CALLBACK_YESTERDAY)
    update = SimpleNamespace(callback_query=query)

    result = await on_date_callback(update, context)

    assert result == MOOD
    assert context.user_data["checkin_date"] == date(2026, 1, 1)


@pytest.mark.asyncio
async def test_on_mood_callback_stores_rating_and_advances() -> None:
    bot_data = _bot_data()
    bot_data["checkin_service"].validate_rating.side_effect = lambda v: v
    context = _context(bot_data)
    query = _query("checkin:mood:5")
    update = SimpleNamespace(callback_query=query)

    result = await on_mood_callback(update, context)

    assert result == PRODUCTIVITY
    assert context.user_data["checkin_mood"] == 5
    query.edit_message_text.assert_awaited_once()
    assert "reply_markup" in query.edit_message_text.await_args.kwargs


@pytest.mark.asyncio
async def test_on_productivity_callback_stores_rating_and_advances() -> None:
    bot_data = _bot_data()
    bot_data["checkin_service"].validate_rating.side_effect = lambda v: v
    context = _context(bot_data)
    query = _query("checkin:prod:4")
    update = SimpleNamespace(callback_query=query)

    result = await on_productivity_callback(update, context)

    assert result == NOTE
    assert context.user_data["checkin_productivity"] == 4
    query.edit_message_text.assert_awaited_once_with(checkin_module.strings.CHECKIN_ASK_NOTE)
    query.edit_message_reply_markup.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_note_text_saves_checkin_and_ends_conversation() -> None:
    bot_data = _bot_data()
    bot_data["checkin_service"].save_checkin.return_value = make_checkin(mood=5, productivity=4)
    bot_data["checkin_service"].enrich_with_gadgetbridge.return_value = None
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(bot_data)
    context.user_data.update({"checkin_date": date(2026, 1, 1), "checkin_mood": 5, "checkin_productivity": 4})
    update = _update(text="feeling okay")

    result = await on_note_text(update, context)

    assert result == ConversationHandler.END
    bot_data["checkin_service"].save_checkin.assert_awaited_once_with(
        user_id=100, checkin_date=date(2026, 1, 1), mood=5, productivity=4, note="feeling okay"
    )
    update.effective_message.reply_text.assert_awaited_once()
    assert context.user_data == {}


@pytest.mark.asyncio
async def test_cmd_skip_note_saves_without_note() -> None:
    bot_data = _bot_data()
    bot_data["checkin_service"].save_checkin.return_value = make_checkin(mood=5, productivity=4)
    bot_data["checkin_service"].enrich_with_gadgetbridge.return_value = None
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(bot_data)
    context.user_data.update({"checkin_date": date(2026, 1, 1), "checkin_mood": 5, "checkin_productivity": 4})
    update = _update()

    await cmd_skip_note(update, context)

    bot_data["checkin_service"].save_checkin.assert_awaited_once_with(
        user_id=100, checkin_date=date(2026, 1, 1), mood=5, productivity=4, note=None
    )


@pytest.mark.asyncio
async def test_finish_checkin_appends_enrichment_when_available() -> None:
    bot_data = _bot_data()
    bot_data["checkin_service"].save_checkin.return_value = make_checkin(mood=5, productivity=4)
    bot_data["checkin_service"].enrich_with_gadgetbridge.return_value = make_checkin(
        mood=5, productivity=4, sleep_hours=7.5, steps=5000
    )
    bot_data["settings_repository"].ensure.return_value = make_user_settings()
    context = _context(bot_data)
    context.user_data.update({"checkin_date": date(2026, 1, 1), "checkin_mood": 5, "checkin_productivity": 4})
    update = _update()

    await cmd_skip_note(update, context)

    text = update.effective_message.reply_text.await_args.args[0]
    assert "Sleep" in text
    assert "5000" in text


@pytest.mark.asyncio
async def test_cmd_cancel_checkin_clears_state_and_replies() -> None:
    context = _context()
    context.user_data["checkin_date"] = date(2026, 1, 1)
    update = _update()

    result = await cmd_cancel_checkin(update, context)

    assert result == ConversationHandler.END
    assert context.user_data == {}
    update.effective_message.reply_text.assert_awaited_once()


class _FixedDatetime(datetime):
    _now: datetime

    @classmethod
    def now(cls, tz: object | None = None) -> datetime:
        return cls._now


@pytest.mark.asyncio
async def test_reminder_job_skips_when_reminders_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(reminders_enabled=False)
    context = _context(bot_data)

    await reminder_job(context)

    context.bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_reminder_job_skips_when_already_checked_in(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(
        timezone="UTC", checkin_hour=21, reminders_enabled=True
    )
    bot_data["checkin_service"].get_checkin.return_value = make_checkin()
    context = _context(bot_data)
    _FixedDatetime._now = datetime(2026, 1, 1, 21, 30, tzinfo=UTC)
    monkeypatch.setattr(checkin_module, "datetime", _FixedDatetime)

    await reminder_job(context)

    context.bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_reminder_job_sends_when_due(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(
        timezone="UTC", checkin_hour=21, reminders_enabled=True
    )
    bot_data["checkin_service"].get_checkin.return_value = None
    context = _context(bot_data)
    _FixedDatetime._now = datetime(2026, 1, 1, 21, 30, tzinfo=UTC)
    monkeypatch.setattr(checkin_module, "datetime", _FixedDatetime)

    await reminder_job(context)

    context.bot.send_message.assert_awaited_once()
