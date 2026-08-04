from __future__ import annotations

from datetime import UTC, datetime

from tonus_bot.services.reminder_service import should_remind


def test_should_remind_false_when_already_checked_in() -> None:
    now = datetime(2026, 1, 1, 21, 0, tzinfo=UTC)
    assert should_remind(now, "UTC", 21, has_checkin_today=True) is False


def test_should_remind_true_at_checkin_hour() -> None:
    now = datetime(2026, 1, 1, 21, 30, tzinfo=UTC)
    assert should_remind(now, "UTC", 21, has_checkin_today=False) is True


def test_should_remind_false_outside_checkin_hour() -> None:
    now = datetime(2026, 1, 1, 20, 30, tzinfo=UTC)
    assert should_remind(now, "UTC", 21, has_checkin_today=False) is False


def test_should_remind_respects_timezone() -> None:
    # 21:30 UTC == 22:30 Europe/Warsaw in January (UTC+1, no DST)
    now = datetime(2026, 1, 1, 21, 30, tzinfo=UTC)
    assert should_remind(now, "Europe/Warsaw", 22, has_checkin_today=False) is True
