from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from tonus_bot.persistence import Checkin
from tonus_bot.repositories import CheckinRepository
from tonus_bot.services import gadgetbridge

MIN_RATING = 1
MAX_RATING = 7
# Between local midnight and 04:00 it's ambiguous whether "today" means the day that just ended
# or the one that just started, so default to yesterday but let the handler offer a switch.
_AMBIGUOUS_HOUR_CUTOFF = 4


@dataclass(frozen=True)
class CheckinDateResolution:
    date: date
    is_ambiguous: bool
    alternate_date: date | None


class CheckinService:
    def __init__(self, checkin_repository: CheckinRepository) -> None:
        self._checkin_repository = checkin_repository

    def resolve_checkin_date(self, now_utc: datetime, timezone: str) -> CheckinDateResolution:
        local_now = now_utc.astimezone(ZoneInfo(timezone))
        if local_now.hour < _AMBIGUOUS_HOUR_CUTOFF:
            yesterday = local_now.date() - timedelta(days=1)
            return CheckinDateResolution(date=yesterday, is_ambiguous=True, alternate_date=local_now.date())
        return CheckinDateResolution(date=local_now.date(), is_ambiguous=False, alternate_date=None)

    def validate_rating(self, value: int) -> int:
        if not MIN_RATING <= value <= MAX_RATING:
            msg = f"Rating must be between {MIN_RATING} and {MAX_RATING}, got {value}"
            raise ValueError(msg)
        return value

    async def save_checkin(
        self, *, user_id: int, checkin_date: date, mood: int, productivity: int, note: str | None
    ) -> Checkin:
        self.validate_rating(mood)
        self.validate_rating(productivity)
        return await self._checkin_repository.save(
            user_id=user_id, checkin_date=checkin_date, mood=mood, productivity=productivity, note=note
        )

    async def get_checkin(self, user_id: int, checkin_date: date) -> Checkin | None:
        return await self._checkin_repository.get(user_id, checkin_date)

    async def get_recent(self, user_id: int, *, days: int, today: date) -> list[Checkin]:
        start_date = today - timedelta(days=days - 1)
        return await self._checkin_repository.get_range(user_id, start_date, today)

    async def enrich_with_gadgetbridge(
        self, user_id: int, checkin_date: date, *, db_path: str | None, timezone: str
    ) -> Checkin | None:
        sleep_hours, steps = await gadgetbridge.read_sleep_and_steps(db_path, checkin_date, timezone)
        if sleep_hours is None and steps is None:
            return None
        return await self._checkin_repository.update_enrichment(user_id, checkin_date, sleep_hours, steps)
