from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.persistence.fakes import FakeSession, FakeSessionFactory
from tonus_bot.persistence.settings_store import SettingsStore


class SettingsDb(SettingsStore):
    def __init__(self, session: FakeSession):
        self._session_factory = FakeSessionFactory(session)


def _fake_settings_record(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "user_id": 1,
        "checkin_hour": 21,
        "timezone": "Europe/Warsaw",
        "reminders_enabled": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_get_settings_sync_none() -> None:
    session = FakeSession(scalar_results=[None])
    db = SettingsDb(session)
    assert db._get_settings_sync(1) is None


def test_get_settings_sync_some(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _fake_settings_record()
    session = FakeSession(scalar_results=[record])
    db = SettingsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.settings_store.to_user_settings", lambda r: r)

    assert db._get_settings_sync(1) == record


def test_ensure_settings_sync_creates_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(scalar_results=[None])
    db = SettingsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.settings_store.to_user_settings", lambda r: r)

    out = db._ensure_settings_sync(1, "Europe/Warsaw", 21)

    assert out.timezone == "Europe/Warsaw"
    assert out.checkin_hour == 21
    assert session.added
    assert session.committed == 1


def test_ensure_settings_sync_returns_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    record = _fake_settings_record(timezone="UTC")
    session = FakeSession(scalar_results=[record])
    db = SettingsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.settings_store.to_user_settings", lambda r: r)

    out = db._ensure_settings_sync(1, "Europe/Warsaw", 21)

    assert out.timezone == "UTC"
    assert session.added == []
    assert session.committed == 0


@pytest.mark.parametrize(
    ("method", "field", "value"),
    [
        ("_set_checkin_hour_sync", "checkin_hour", 8),
        ("_set_timezone_sync", "timezone", "UTC"),
        ("_set_reminders_enabled_sync", "reminders_enabled", False),
    ],
)
def test_setters_create_record_when_missing(
    monkeypatch: pytest.MonkeyPatch, method: str, field: str, value: object
) -> None:
    session = FakeSession(scalar_results=[None])
    db = SettingsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.settings_store.to_user_settings", lambda r: r)

    result = getattr(db, method)(1, value)

    assert getattr(result, field) == value
    assert session.added
    assert session.committed == 1


@pytest.mark.parametrize(
    ("method", "field", "value"),
    [
        ("_set_checkin_hour_sync", "checkin_hour", 8),
        ("_set_timezone_sync", "timezone", "UTC"),
        ("_set_reminders_enabled_sync", "reminders_enabled", False),
    ],
)
def test_setters_update_existing_record(
    monkeypatch: pytest.MonkeyPatch, method: str, field: str, value: object
) -> None:
    record = _fake_settings_record()
    session = FakeSession(scalar_results=[record])
    db = SettingsDb(session)
    monkeypatch.setattr("tonus_bot.persistence.settings_store.to_user_settings", lambda r: r)

    result = getattr(db, method)(1, value)

    assert getattr(result, field) == value
    assert session.added == []
    assert session.committed == 1
