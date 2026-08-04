from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from tests.persistence.fakes import FakeSession, FakeSessionFactory
from tonus_bot.persistence.insight_store import InsightStore


class InsightsDb(InsightStore):
    def __init__(self, session: FakeSession):
        self._session_factory = FakeSessionFactory(session)


def _fake_insight_record(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "id": 1,
        "user_id": 1,
        "week_start": date(2026, 1, 5),
        "insight_text": "text",
        "raw_stats": None,
        "created_at": datetime(2026, 1, 5, tzinfo=UTC),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_save_insight_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    db = InsightsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.insight_store.utc_now", lambda: datetime(2026, 1, 5, tzinfo=UTC))
    monkeypatch.setattr("tonus_bot.persistence.insight_store.to_weekly_insight", lambda r: r)

    out = db._save_insight_sync(1, date(2026, 1, 5), "text", {"a": 1})

    assert out.insight_text == "text"
    assert session.added
    assert session.committed == 1


def test_get_latest_insight_sync_none() -> None:
    session = FakeSession(scalar_results=[None])
    db = InsightsDb(session)
    assert db._get_latest_insight_sync(1) is None


def test_get_latest_insight_sync_some(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _fake_insight_record()
    session = FakeSession(scalar_results=[record])
    db = InsightsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.insight_store.to_weekly_insight", lambda r: r)

    assert db._get_latest_insight_sync(1) == record


def test_get_insight_for_week_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _fake_insight_record()
    session = FakeSession(scalar_results=[record])
    db = InsightsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.insight_store.to_weekly_insight", lambda r: r)

    assert db._get_insight_for_week_sync(1, date(2026, 1, 5)) == record
