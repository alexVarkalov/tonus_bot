from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def should_remind(now_utc: datetime, timezone: str, checkin_hour: int, *, has_checkin_today: bool) -> bool:
    if has_checkin_today:
        return False
    local_hour = now_utc.astimezone(ZoneInfo(timezone)).hour
    return local_hour == checkin_hour
