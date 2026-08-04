from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from tests.persistence.fakes import FakeInsert, FakeSession, FakeSessionFactory
from tonus_bot.persistence.checkin_store import CheckinStore


class CheckinsDb(CheckinStore):
    def __init__(self, session: FakeSession):
        self._session_factory = FakeSessionFactory(session)


def _fake_checkin_record(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "id": 1,
        "user_id": 1,
        "date": date(2026, 1, 1),
        "mood": 5,
        "productivity": 4,
        "note": None,
        "tags": None,
        "sleep_hours": None,
        "steps": None,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _select_stub(*_a: object, **_k: object) -> SimpleNamespace:
    return SimpleNamespace(where=lambda *_a2, **_k2: object())


def test_get_checkin_sync_none() -> None:
    session = FakeSession(scalar_results=[None])
    db = CheckinsDb(session)
    assert db._get_checkin_sync(1, date(2026, 1, 1)) is None


def test_get_checkin_sync_some(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _fake_checkin_record()
    session = FakeSession(scalar_results=[record])
    db = CheckinsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.to_checkin", lambda r: r)

    assert db._get_checkin_sync(1, date(2026, 1, 1)) == record


def test_upsert_checkin_sync_raises_if_read_back_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(scalar_results=[None])
    db = CheckinsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.pg_insert", lambda _model: FakeInsert())
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.select", _select_stub)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.utc_now", lambda: datetime(2026, 1, 1, tzinfo=UTC))

    with pytest.raises(RuntimeError, match="failed to read checkin after upsert"):
        db._upsert_checkin_sync(1, date(2026, 1, 1), 5, 4, None, None)


def test_upsert_checkin_sync_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _fake_checkin_record()
    session = FakeSession(scalar_results=[record])
    db = CheckinsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.pg_insert", lambda _model: FakeInsert())
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.select", _select_stub)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.utc_now", lambda: datetime(2026, 1, 1, tzinfo=UTC))
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.to_checkin", lambda r: r)

    out = db._upsert_checkin_sync(1, date(2026, 1, 1), 5, 4, "note", ["tag"])

    assert out == record
    assert session.executed
    assert session.committed == 1


def test_get_checkins_range_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    r1 = _fake_checkin_record(id=1, date=date(2026, 1, 1))
    r2 = _fake_checkin_record(id=2, date=date(2026, 1, 2))
    session = FakeSession(scalars_results=[[r1, r2]])
    db = CheckinsDb(session)
    monkeypatch.setattr(
        "tonus_bot.persistence.checkin_store.select",
        lambda *_a, **_k: SimpleNamespace(
            where=lambda *_a2, **_k2: SimpleNamespace(order_by=lambda *_a3, **_k3: object())
        ),
    )
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.to_checkin", lambda r: r)

    result = db._get_checkins_range_sync(1, date(2026, 1, 1), date(2026, 1, 2))

    assert result == [r1, r2]


def test_update_enrichment_sync_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(scalar_results=[None])
    db = CheckinsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.select", _select_stub)

    assert db._update_enrichment_sync(1, date(2026, 1, 1), 7.5, 5000) is None
    assert session.committed == 0


def test_update_enrichment_sync_updates_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _fake_checkin_record()
    session = FakeSession(scalar_results=[record])
    db = CheckinsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.select", _select_stub)
    monkeypatch.setattr("tonus_bot.persistence.checkin_store.to_checkin", lambda r: r)

    out = db._update_enrichment_sync(1, date(2026, 1, 1), 7.5, 5000)

    assert out.sleep_hours == 7.5
    assert out.steps == 5000
    assert session.committed == 1
