from __future__ import annotations

import pytest

from tonus_bot.config import Settings


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "token")
    monkeypatch.setenv("ALLOWED_USER_ID", "42")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/tonus")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key")


def test_from_env_requires_bot_token(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    with pytest.raises(ValueError, match="BOT_TOKEN"):
        Settings.from_env()


def test_from_env_requires_allowed_user_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv("ALLOWED_USER_ID", raising=False)

    with pytest.raises(ValueError, match="ALLOWED_USER_ID"):
        Settings.from_env()


def test_from_env_requires_allowed_user_id_to_be_int(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("ALLOWED_USER_ID", "not-a-number")

    with pytest.raises(ValueError, match="ALLOWED_USER_ID must be an integer"):
        Settings.from_env()


def test_from_env_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings.from_env()


def test_from_env_requires_anthropic_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        Settings.from_env()


def test_from_env_applies_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv("GADGETBRIDGE_DB_PATH", raising=False)
    monkeypatch.delenv("DEFAULT_TIMEZONE", raising=False)
    monkeypatch.delenv("CHECKIN_REMINDER_HOUR", raising=False)

    settings = Settings.from_env()

    assert settings.allowed_user_id == 42
    assert settings.gadgetbridge_db_path is None
    assert settings.default_timezone == "Europe/Warsaw"
    assert settings.checkin_reminder_hour == 21


def test_from_env_clamps_checkin_reminder_hour(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("CHECKIN_REMINDER_HOUR", "99")

    settings = Settings.from_env()

    assert settings.checkin_reminder_hour == 23


def test_from_env_reads_gadgetbridge_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("GADGETBRIDGE_DB_PATH", "/data/gadgetbridge.db")

    settings = Settings.from_env()

    assert settings.gadgetbridge_db_path == "/data/gadgetbridge.db"
