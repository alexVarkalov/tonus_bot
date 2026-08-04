from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from tests.helpers import make_checkin
from tonus_bot.services.checkin_service import CheckinService


def test_resolve_checkin_date_not_ambiguous_daytime() -> None:
    service = CheckinService(AsyncMock())

    resolution = service.resolve_checkin_date(datetime(2026, 1, 2, 12, 0, tzinfo=UTC), "UTC")

    assert resolution.date == date(2026, 1, 2)
    assert resolution.is_ambiguous is False
    assert resolution.alternate_date is None


def test_resolve_checkin_date_ambiguous_early_morning() -> None:
    service = CheckinService(AsyncMock())

    resolution = service.resolve_checkin_date(datetime(2026, 1, 2, 2, 0, tzinfo=UTC), "UTC")

    assert resolution.date == date(2026, 1, 1)
    assert resolution.is_ambiguous is True
    assert resolution.alternate_date == date(2026, 1, 2)


@pytest.mark.parametrize("value", [0, 8, -1])
def test_validate_rating_rejects_out_of_range(value: int) -> None:
    service = CheckinService(AsyncMock())
    with pytest.raises(ValueError, match="Rating must be between"):
        service.validate_rating(value)


@pytest.mark.parametrize("value", [1, 4, 7])
def test_validate_rating_accepts_in_range(value: int) -> None:
    service = CheckinService(AsyncMock())
    assert service.validate_rating(value) == value


@pytest.mark.asyncio
async def test_save_checkin_validates_before_saving() -> None:
    repo = AsyncMock()
    service = CheckinService(repo)

    with pytest.raises(ValueError, match="Rating must be between"):
        await service.save_checkin(user_id=1, checkin_date=date(2026, 1, 1), mood=9, productivity=4, note=None)

    repo.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_checkin_delegates_to_repo() -> None:
    repo = AsyncMock()
    repo.save.return_value = make_checkin()
    service = CheckinService(repo)

    result = await service.save_checkin(user_id=1, checkin_date=date(2026, 1, 1), mood=5, productivity=4, note="n")

    repo.save.assert_awaited_once_with(user_id=1, checkin_date=date(2026, 1, 1), mood=5, productivity=4, note="n")
    assert result == make_checkin()


@pytest.mark.asyncio
async def test_get_recent_computes_start_date() -> None:
    repo = AsyncMock()
    service = CheckinService(repo)

    await service.get_recent(1, days=7, today=date(2026, 1, 7))

    repo.get_range.assert_awaited_once_with(1, date(2026, 1, 1), date(2026, 1, 7))


@pytest.mark.asyncio
async def test_enrich_with_gadgetbridge_returns_none_without_data(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = AsyncMock()
    service = CheckinService(repo)
    monkeypatch.setattr(
        "tonus_bot.services.checkin_service.gadgetbridge.read_sleep_and_steps",
        AsyncMock(return_value=(None, None)),
    )

    result = await service.enrich_with_gadgetbridge(1, date(2026, 1, 1), db_path=None, timezone="UTC")

    assert result is None
    repo.update_enrichment.assert_not_awaited()


@pytest.mark.asyncio
async def test_enrich_with_gadgetbridge_updates_when_data_found(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = AsyncMock()
    repo.update_enrichment.return_value = make_checkin(sleep_hours=7.5, steps=5000)
    service = CheckinService(repo)
    monkeypatch.setattr(
        "tonus_bot.services.checkin_service.gadgetbridge.read_sleep_and_steps",
        AsyncMock(return_value=(7.5, 5000)),
    )

    result = await service.enrich_with_gadgetbridge(1, date(2026, 1, 1), db_path="/tmp/x.db", timezone="UTC")

    repo.update_enrichment.assert_awaited_once_with(1, date(2026, 1, 1), 7.5, 5000)
    assert result.sleep_hours == 7.5
