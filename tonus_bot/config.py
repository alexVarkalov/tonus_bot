from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    anthropic_api_key: str
    allowed_user_id: int
    gadgetbridge_db_path: str | None
    default_timezone: str
    checkin_reminder_hour: int

    @classmethod
    def from_env(cls) -> Settings:
        token = os.environ.get("BOT_TOKEN", "").strip()
        if not token:
            msg = "BOT_TOKEN is required"
            raise ValueError(msg)

        allowed_user_id_raw = os.environ.get("ALLOWED_USER_ID", "").strip()
        if not allowed_user_id_raw:
            msg = "ALLOWED_USER_ID is required"
            raise ValueError(msg)
        try:
            allowed_user_id = int(allowed_user_id_raw)
        except ValueError as exc:
            msg = "ALLOWED_USER_ID must be an integer"
            raise ValueError(msg) from exc

        database_url = os.environ.get("DATABASE_URL", "").strip()
        if not database_url:
            msg = "DATABASE_URL is required"
            raise ValueError(msg)

        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not anthropic_api_key:
            msg = "ANTHROPIC_API_KEY is required"
            raise ValueError(msg)

        return cls(
            bot_token=token,
            database_url=database_url,
            anthropic_api_key=anthropic_api_key,
            allowed_user_id=allowed_user_id,
            gadgetbridge_db_path=os.environ.get("GADGETBRIDGE_DB_PATH", "").strip() or None,
            default_timezone=os.environ.get("DEFAULT_TIMEZONE", "Europe/Warsaw").strip(),
            checkin_reminder_hour=max(0, min(23, int(os.environ.get("CHECKIN_REMINDER_HOUR", "21")))),
        )
