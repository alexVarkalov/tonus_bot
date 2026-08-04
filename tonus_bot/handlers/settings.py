from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from telegram import Update
from telegram.ext import ContextTypes

from tonus_bot import strings
from tonus_bot.handlers.common import ensure_user_settings, guard
from tonus_bot.repositories import SettingsRepository


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return

    user_id = update.effective_user.id
    user_settings = await ensure_user_settings(context, user_id)

    if not context.args:
        reminders = strings.SETTINGS_REMINDERS_ON if user_settings.reminders_enabled else strings.SETTINGS_REMINDERS_OFF
        await update.effective_message.reply_text(
            strings.SETTINGS_CURRENT.format(
                hour=user_settings.checkin_hour, timezone=user_settings.timezone, reminders=reminders
            )
        )
        return

    settings_repo: SettingsRepository = context.application.bot_data["settings_repository"]
    subcommand = context.args[0].lower()

    if subcommand == "hour" and len(context.args) >= 2:
        await _set_hour(update, settings_repo, user_id, context.args[1])
        return
    if subcommand == "timezone" and len(context.args) >= 2:
        await _set_timezone(update, settings_repo, user_id, context.args[1])
        return
    if subcommand == "reminders" and len(context.args) >= 2:
        await _set_reminders(update, settings_repo, user_id, context.args[1])
        return

    await update.effective_message.reply_text(strings.SETTINGS_USAGE)


async def _set_hour(update: Update, settings_repo: SettingsRepository, user_id: int, raw_hour: str) -> None:
    try:
        hour = int(raw_hour)
        if not 0 <= hour <= 23:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text(strings.SETTINGS_HOUR_INVALID)
        return

    await settings_repo.set_checkin_hour(user_id, hour)
    await update.effective_message.reply_text(strings.SETTINGS_HOUR_UPDATED.format(hour=hour))


async def _set_timezone(update: Update, settings_repo: SettingsRepository, user_id: int, raw_timezone: str) -> None:
    timezone = raw_timezone.strip()
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        await update.effective_message.reply_text(strings.SETTINGS_TIMEZONE_INVALID.format(timezone=timezone))
        return

    await settings_repo.set_timezone(user_id, timezone)
    await update.effective_message.reply_text(strings.SETTINGS_TIMEZONE_UPDATED.format(timezone=timezone))


async def _set_reminders(update: Update, settings_repo: SettingsRepository, user_id: int, raw_value: str) -> None:
    value = raw_value.lower()
    if value not in {"on", "off"}:
        await update.effective_message.reply_text(strings.SETTINGS_REMINDERS_USAGE)
        return

    enabled = value == "on"
    await settings_repo.set_reminders_enabled(user_id, enabled)
    state = strings.SETTINGS_REMINDERS_ON if enabled else strings.SETTINGS_REMINDERS_OFF
    await update.effective_message.reply_text(strings.SETTINGS_REMINDERS_UPDATED.format(state=state))
