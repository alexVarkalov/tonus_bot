from __future__ import annotations

import json
from datetime import date, timedelta

import anthropic
from anthropic import AsyncAnthropic

from tonus_bot.config import Settings
from tonus_bot.persistence import WeeklyInsight
from tonus_bot.repositories import CheckinRepository, InsightRepository

MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = (
    "You analyze two weeks of a single person's daily mood/productivity check-ins. Mood and "
    "productivity are each rated on a 1-7 scale. Identify concrete patterns tied to specific "
    "numbers (e.g. correlations between sleep and mood, weekday vs weekend swings, streaks). "
    "Write 3-5 sentences in English. No generic advice."
)


class AnalysisService:
    def __init__(
        self,
        settings: Settings,
        anthropic_client: AsyncAnthropic,
        checkin_repository: CheckinRepository,
        insight_repository: InsightRepository,
    ) -> None:
        self._settings = settings
        self._client = anthropic_client
        self._checkin_repository = checkin_repository
        self._insight_repository = insight_repository

    async def generate_weekly_insight(self, user_id: int, week_start: date) -> WeeklyInsight:
        window_start = week_start - timedelta(days=7)
        window_end = week_start + timedelta(days=6)
        checkins = await self._checkin_repository.get_range(user_id, window_start, window_end)
        if not checkins:
            msg = "No check-ins in the analysis window"
            raise ValueError(msg)

        payload = [
            {
                "date": c.date.isoformat(),
                "mood": c.mood,
                "productivity": c.productivity,
                "sleep_hours": c.sleep_hours,
                "steps": c.steps,
                "note": c.note,
            }
            for c in checkins
        ]

        try:
            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=400,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            )
        except anthropic.APIError as exc:
            msg = f"Anthropic API error: {exc}"
            raise ValueError(msg) from exc

        insight_text = "".join(block.text for block in response.content if block.type == "text").strip()
        if not insight_text:
            msg = "Anthropic API returned an empty response"
            raise ValueError(msg)

        return await self._insight_repository.save(
            user_id=user_id,
            week_start=week_start,
            insight_text=insight_text,
            raw_stats={"checkins": payload},
        )
