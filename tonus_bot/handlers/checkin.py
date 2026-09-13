from __future__ import annotations

from datetime import UTC, date, datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from tonus_bot import strings
from tonus_bot.config import Settings
from tonus_bot.handlers.common import ensure_user_settings, guard, local_today
from tonus_bot.repositories import SettingsRepository
from tonus_bot.services import CheckinService, reminder_service

CONFIRM_DATE, MOOD, PRODUCTIVITY, NOTE = range(4)

_DATE_CALLBACK_TODAY = "checkin:date:today"
_DATE_CALLBACK_YESTERDAY = "checkin:date:yesterday"
_MOOD_PREFIX = "checkin:mood:"
_PRODUCTIVITY_PREFIX = "checkin:prod:"


def _rating_keyboard(prefix: str) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(str(n), callback_data=f"{prefix}{n}") for n in range(1, 8)]
    return InlineKeyboardMarkup([buttons])


async def cmd_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await guard(update, context):
        return ConversationHandler.END

    checkin_service: CheckinService = context.application.bot_data["checkin_service"]
    user_settings = await ensure_user_settings(context, update.effective_user.id)
    lang = user_settings.language
    resolution = checkin_service.resolve_checkin_date(datetime.now(UTC), user_settings.timezone)

    if resolution.is_ambiguous:
        context.user_data["checkin_date"] = resolution.date
        context.user_data["checkin_alternate_date"] = resolution.alternate_date
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        strings.t("CHECKIN_DATE_BUTTON_YESTERDAY", lang, date=resolution.date),
                        callback_data=_DATE_CALLBACK_YESTERDAY,
                    ),
                    InlineKeyboardButton(
                        strings.t("CHECKIN_DATE_BUTTON_TODAY", lang), callback_data=_DATE_CALLBACK_TODAY
                    ),
                ]
            ]
        )
        await update.effective_message.reply_text(
            strings.t("CHECKIN_DATE_CONFIRM", lang, yesterday=resolution.date, today=resolution.alternate_date),
            reply_markup=keyboard,
        )
        return CONFIRM_DATE

    context.user_data["checkin_date"] = resolution.date
    await update.effective_message.reply_text(
        strings.t("CHECKIN_ASK_MOOD", lang, date=resolution.date), reply_markup=_rating_keyboard(_MOOD_PREFIX)
    )
    return MOOD


async def on_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        return ConversationHandler.END
    await query.answer()

    if query.data == _DATE_CALLBACK_TODAY:
        context.user_data["checkin_date"] = context.user_data["checkin_alternate_date"]
    checkin_date: date = context.user_data["checkin_date"]

    user_settings = await ensure_user_settings(context, update.effective_user.id)
    await query.edit_message_text(
        strings.t("CHECKIN_ASK_MOOD", user_settings.language, date=checkin_date),
        reply_markup=_rating_keyboard(_MOOD_PREFIX),
    )
    return MOOD


async def on_mood_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        return ConversationHandler.END
    await query.answer()

    checkin_service: CheckinService = context.application.bot_data["checkin_service"]
    mood = checkin_service.validate_rating(int(query.data.removeprefix(_MOOD_PREFIX)))
    context.user_data["checkin_mood"] = mood

    user_settings = await ensure_user_settings(context, update.effective_user.id)
    await query.edit_message_text(
        strings.t("CHECKIN_ASK_PRODUCTIVITY", user_settings.language),
        reply_markup=_rating_keyboard(_PRODUCTIVITY_PREFIX),
    )
    return PRODUCTIVITY


async def on_productivity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None:
        return ConversationHandler.END
    await query.answer()

    checkin_service: CheckinService = context.application.bot_data["checkin_service"]
    productivity = checkin_service.validate_rating(int(query.data.removeprefix(_PRODUCTIVITY_PREFIX)))
    context.user_data["checkin_productivity"] = productivity

    user_settings = await ensure_user_settings(context, update.effective_user.id)
    # edit_message_text always sends reply_markup (defaulting to None), which already clears
    # the keyboard here — no separate edit_message_reply_markup call needed or safe to make.
    await query.edit_message_text(strings.t("CHECKIN_ASK_NOTE", user_settings.language))
    return NOTE


async def on_note_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _finish_checkin(update, context, note=update.effective_message.text)


async def cmd_skip_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _finish_checkin(update, context, note=None)


async def cmd_cancel_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_settings = await ensure_user_settings(context, update.effective_user.id)
    context.user_data.clear()
    await update.effective_message.reply_text(strings.t("CHECKIN_CANCELLED", user_settings.language))
    return ConversationHandler.END


async def _finish_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE, *, note: str | None) -> int:
    settings: Settings = context.application.bot_data["settings"]
    checkin_service: CheckinService = context.application.bot_data["checkin_service"]
    user_id = update.effective_user.id
    checkin_date: date = context.user_data["checkin_date"]
    mood: int = context.user_data["checkin_mood"]
    productivity: int = context.user_data["checkin_productivity"]

    checkin = await checkin_service.save_checkin(
        user_id=user_id, checkin_date=checkin_date, mood=mood, productivity=productivity, note=note
    )

    user_settings = await ensure_user_settings(context, user_id)
    enriched = await checkin_service.enrich_with_gadgetbridge(
        user_id, checkin_date, db_path=settings.gadgetbridge_db_path, timezone=user_settings.timezone
    )
    checkin = enriched or checkin

    lang = user_settings.language
    text = strings.t("CHECKIN_SAVED", lang, date=checkin_date, mood=mood, productivity=productivity)
    if checkin.sleep_hours is not None or checkin.steps is not None:
        text += strings.t("CHECKIN_ENRICHED", lang, sleep_hours=checkin.sleep_hours or 0.0, steps=checkin.steps or 0)

    await update.effective_message.reply_text(text)
    context.user_data.clear()
    return ConversationHandler.END


async def reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    checkin_service: CheckinService = context.application.bot_data["checkin_service"]
    settings_repo: SettingsRepository = context.application.bot_data["settings_repository"]

    user_settings = await settings_repo.ensure(
        settings.allowed_user_id,
        default_timezone=settings.default_timezone,
        default_checkin_hour=settings.checkin_reminder_hour,
    )
    if not user_settings.reminders_enabled:
        return

    now_utc = datetime.now(UTC)
    today = local_today(now_utc, user_settings.timezone)
    has_checkin = await checkin_service.get_checkin(settings.allowed_user_id, today) is not None

    if reminder_service.should_remind(
        now_utc, user_settings.timezone, user_settings.checkin_hour, has_checkin_today=has_checkin
    ):
        await context.bot.send_message(
            chat_id=settings.allowed_user_id, text=strings.t("REMINDER_TEXT", user_settings.language)
        )
