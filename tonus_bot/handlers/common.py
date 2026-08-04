from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from tonus_bot.config import Settings
from tonus_bot.persistence import UserSettings
from tonus_bot.repositories import SettingsRepository


def is_allowed(update: Update, settings: Settings) -> bool:
    user = update.effective_user
    return user is not None and user.id == settings.allowed_user_id


async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Silently ignore updates from anyone but the single allowed user."""
    if update.effective_user is None or update.effective_message is None:
        return False
    settings: Settings = context.application.bot_data["settings"]
    return is_allowed(update, settings)


async def ensure_user_settings(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> UserSettings:
    settings: Settings = context.application.bot_data["settings"]
    settings_repo: SettingsRepository = context.application.bot_data["settings_repository"]
    return await settings_repo.ensure(
        user_id,
        default_timezone=settings.default_timezone,
        default_checkin_hour=settings.checkin_reminder_hour,
    )


def local_today(now_utc: datetime, timezone: str) -> date:
    return now_utc.astimezone(ZoneInfo(timezone)).date()
