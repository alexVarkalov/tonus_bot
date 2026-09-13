from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.helpers import make_checkin, make_weekly_insight
from tonus_bot.services.analysis_service import AnalysisService


def _settings() -> SimpleNamespace:
    return SimpleNamespace(anthropic_api_key="key")


def _text_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


@pytest.mark.asyncio
async def test_generate_weekly_insight_raises_without_checkins() -> None:
    checkin_repo = AsyncMock()
    checkin_repo.get_range.return_value = []
    insight_repo = AsyncMock()
    client = AsyncMock()
    service = AnalysisService(_settings(), client, checkin_repo, insight_repo)

    with pytest.raises(ValueError, match="No check-ins"):
        await service.generate_weekly_insight(1, date(2026, 1, 5))

    client.messages.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_weekly_insight_saves_and_returns_insight() -> None:
    checkin_repo = AsyncMock()
    checkin_repo.get_range.return_value = [make_checkin()]
    insight_repo = AsyncMock()
    insight_repo.save.return_value = make_weekly_insight(insight_text="pattern found")
    client = AsyncMock()
    client.messages.create.return_value = _text_response("pattern found")
    service = AnalysisService(_settings(), client, checkin_repo, insight_repo)

    result = await service.generate_weekly_insight(1, date(2026, 1, 5))

    assert result.insight_text == "pattern found"
    insight_repo.save.assert_awaited_once()
    _, kwargs = insight_repo.save.await_args
    assert kwargs["user_id"] == 1
    assert kwargs["week_start"] == date(2026, 1, 5)
    assert kwargs["insight_text"] == "pattern found"


@pytest.mark.asyncio
async def test_generate_weekly_insight_raises_on_empty_response() -> None:
    checkin_repo = AsyncMock()
    checkin_repo.get_range.return_value = [make_checkin()]
    insight_repo = AsyncMock()
    client = AsyncMock()
    client.messages.create.return_value = _text_response("")
    service = AnalysisService(_settings(), client, checkin_repo, insight_repo)

    with pytest.raises(ValueError, match="empty response"):
        await service.generate_weekly_insight(1, date(2026, 1, 5))


@pytest.mark.asyncio
async def test_generate_weekly_insight_passes_language_to_system_prompt() -> None:
    checkin_repo = AsyncMock()
    checkin_repo.get_range.return_value = [make_checkin()]
    insight_repo = AsyncMock()
    insight_repo.save.return_value = make_weekly_insight(insight_text="pattern found")
    client = AsyncMock()
    client.messages.create.return_value = _text_response("pattern found")
    service = AnalysisService(_settings(), client, checkin_repo, insight_repo)

    await service.generate_weekly_insight(1, date(2026, 1, 5), language="ru")

    _, kwargs = client.messages.create.await_args
    assert "Russian" in kwargs["system"]


@pytest.mark.asyncio
async def test_generate_weekly_insight_wraps_api_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeAPIError(Exception):
        pass

    monkeypatch.setattr("tonus_bot.services.analysis_service.anthropic.APIError", FakeAPIError)

    checkin_repo = AsyncMock()
    checkin_repo.get_range.return_value = [make_checkin()]
    insight_repo = AsyncMock()
    client = AsyncMock()
    client.messages.create.side_effect = FakeAPIError("boom")
    service = AnalysisService(_settings(), client, checkin_repo, insight_repo)

    with pytest.raises(ValueError, match="Anthropic API error"):
        await service.generate_weekly_insight(1, date(2026, 1, 5))
