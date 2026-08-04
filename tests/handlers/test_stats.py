from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.helpers import make_checkin, make_user_settings, make_weekly_insight
from tonus_bot.config import Settings
from tonus_bot.handlers import stats as stats_module
from tonus_bot.handlers.stats import cmd_stats, cmd_week, weekly_analysis_job


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
    data: dict[str, object] = {
        "settings": _settings(),
        "checkin_service": AsyncMock(),
        "settings_repository": AsyncMock(),
        "analysis_service": AsyncMock(),
    }
    data.update(overrides)
    return data


def _context(bot_data: dict[str, object] | None = None) -> SimpleNamespace:
    return SimpleNamespace(application=SimpleNamespace(bot_data=bot_data or _bot_data()), bot=AsyncMock())


def _update(user_id: int = 100) -> SimpleNamespace:
    return SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id), effective_message=SimpleNamespace(reply_text=AsyncMock())
    )


class _FixedDatetime(datetime):
    _now: datetime

    @classmethod
    def now(cls, tz: object | None = None) -> datetime:
        return cls._now


def _freeze(monkeypatch: pytest.MonkeyPatch, when: datetime) -> None:
    _FixedDatetime._now = when
    monkeypatch.setattr(stats_module, "datetime", _FixedDatetime)


@pytest.mark.asyncio
async def test_cmd_stats_blocks_other_user() -> None:
    context = _context()
    update = _update(user_id=999)

    await cmd_stats(update, context)

    update.effective_message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_cmd_stats_reports_empty_when_no_checkins(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    bot_data["checkin_service"].get_recent.return_value = []
    context = _context(bot_data)
    update = _update()
    _freeze(monkeypatch, datetime(2026, 1, 8, 12, 0, tzinfo=UTC))

    await cmd_stats(update, context)

    text = update.effective_message.reply_text.await_args.args[0]
    assert "No check-ins" in text


@pytest.mark.asyncio
async def test_cmd_stats_reports_rows_and_trend(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    current = [make_checkin(date=date(2026, 1, 8), mood=6, productivity=6)]
    previous = [make_checkin(date=date(2026, 1, 1), mood=4, productivity=4)]
    bot_data["checkin_service"].get_recent.side_effect = [current, previous]
    context = _context(bot_data)
    update = _update()
    _freeze(monkeypatch, datetime(2026, 1, 8, 12, 0, tzinfo=UTC))

    await cmd_stats(update, context)

    text = update.effective_message.reply_text.await_args.args[0]
    assert "2026-01-08" in text
    assert "↑" in text


@pytest.mark.asyncio
async def test_cmd_week_reports_empty_when_no_checkins(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    bot_data["checkin_service"].get_recent.return_value = []
    context = _context(bot_data)
    update = _update()
    _freeze(monkeypatch, datetime(2026, 1, 8, 12, 0, tzinfo=UTC))

    await cmd_week(update, context)

    text = update.effective_message.reply_text.await_args.args[0]
    assert "No check-ins" in text


@pytest.mark.asyncio
async def test_cmd_week_reports_averages(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    bot_data["checkin_service"].get_recent.return_value = [
        make_checkin(mood=6, productivity=4),
        make_checkin(mood=4, productivity=6),
    ]
    context = _context(bot_data)
    update = _update()
    _freeze(monkeypatch, datetime(2026, 1, 8, 12, 0, tzinfo=UTC))  # Thursday

    await cmd_week(update, context)

    text = update.effective_message.reply_text.await_args.args[0]
    assert "5.0" in text


@pytest.mark.asyncio
async def test_weekly_analysis_job_sends_insight(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    bot_data["analysis_service"].generate_weekly_insight.return_value = make_weekly_insight(insight_text="insight!")
    context = _context(bot_data)
    _freeze(monkeypatch, datetime(2026, 1, 8, 20, 0, tzinfo=UTC))

    await weekly_analysis_job(context)

    context.bot.send_message.assert_awaited_once()
    assert "insight!" in context.bot.send_message.await_args.kwargs["text"]


@pytest.mark.asyncio
async def test_weekly_analysis_job_skips_send_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    bot_data = _bot_data()
    bot_data["settings_repository"].ensure.return_value = make_user_settings(timezone="UTC")
    bot_data["analysis_service"].generate_weekly_insight.side_effect = ValueError("no data")
    context = _context(bot_data)
    _freeze(monkeypatch, datetime(2026, 1, 8, 20, 0, tzinfo=UTC))

    await weekly_analysis_job(context)

    context.bot.send_message.assert_not_awaited()
