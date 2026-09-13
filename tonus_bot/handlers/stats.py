from __future__ import annotations

from datetime import UTC, datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from tonus_bot import strings
from tonus_bot.config import Settings
from tonus_bot.handlers.common import ensure_user_settings, guard, local_today
from tonus_bot.repositories import SettingsRepository
from tonus_bot.services import AnalysisService, CheckinService, trends

STATS_DAYS = 7


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return

    user_id = update.effective_user.id
    checkin_service: CheckinService = context.application.bot_data["checkin_service"]
    user_settings = await ensure_user_settings(context, user_id)
    lang = user_settings.language
    today = local_today(datetime.now(UTC), user_settings.timezone)

    current = await checkin_service.get_recent(user_id, days=STATS_DAYS, today=today)
    if not current:
        await update.effective_message.reply_text(strings.t("STATS_EMPTY", lang))
        return

    previous = await checkin_service.get_recent(user_id, days=STATS_DAYS, today=today - timedelta(days=STATS_DAYS))
    mood_trend = trends.trend_arrow(
        trends.average([c.mood for c in current]), trends.average([c.mood for c in previous])
    )
    productivity_trend = trends.trend_arrow(
        trends.average([c.productivity for c in current]), trends.average([c.productivity for c in previous])
    )

    lines = [strings.t("STATS_HEADER", lang, days=STATS_DAYS)]
    lines.extend(strings.t("STATS_ROW", lang, date=c.date, mood=c.mood, productivity=c.productivity) for c in current)
    lines.append("")
    lines.append(strings.t("STATS_TREND", lang, mood_trend=mood_trend, productivity_trend=productivity_trend))
    await update.effective_message.reply_text("\n".join(lines))


async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await guard(update, context):
        return

    user_id = update.effective_user.id
    checkin_service: CheckinService = context.application.bot_data["checkin_service"]
    user_settings = await ensure_user_settings(context, user_id)
    lang = user_settings.language
    today = local_today(datetime.now(UTC), user_settings.timezone)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    checkins = await checkin_service.get_recent(user_id, days=(today - week_start).days + 1, today=today)
    if not checkins:
        await update.effective_message.reply_text(strings.t("WEEK_EMPTY", lang))
        return

    avg_mood = trends.average([c.mood for c in checkins]) or 0.0
    avg_productivity = trends.average([c.productivity for c in checkins]) or 0.0

    await update.effective_message.reply_text(
        "\n".join(
            [
                strings.t("WEEK_HEADER", lang, start=week_start, end=week_end),
                strings.t("WEEK_AVERAGES", lang, avg_mood=avg_mood, avg_productivity=avg_productivity),
            ]
        )
    )


async def weekly_analysis_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    analysis_service: AnalysisService = context.application.bot_data["analysis_service"]
    settings_repo: SettingsRepository = context.application.bot_data["settings_repository"]

    user_settings = await settings_repo.ensure(
        settings.allowed_user_id,
        default_timezone=settings.default_timezone,
        default_checkin_hour=settings.checkin_reminder_hour,
    )
    today = local_today(datetime.now(UTC), user_settings.timezone)
    week_start = today - timedelta(days=today.weekday())

    try:
        insight = await analysis_service.generate_weekly_insight(
            settings.allowed_user_id, week_start, language=user_settings.language
        )
    except ValueError:
        return

    await context.bot.send_message(
        chat_id=settings.allowed_user_id,
        text=f"{strings.t('WEEKLY_INSIGHT_HEADER', user_settings.language)}\n{insight.insight_text}",
    )
