"""User-facing strings for English and Russian, selected by UserSettings.language."""

from __future__ import annotations

DEFAULT_LANGUAGE = "en"
LANGUAGES = ("en", "ru")

_EN: dict[str, str] = {
    # /checkin — date confirmation (only shown during the 00:00-04:00 local ambiguity window)
    "CHECKIN_DATE_CONFIRM": "It's early morning. Log {yesterday} or today ({today})?",
    "CHECKIN_DATE_BUTTON_YESTERDAY": "Yesterday ({date})",
    "CHECKIN_DATE_BUTTON_TODAY": "Today",
    # /checkin — mood/productivity/note steps
    "CHECKIN_ASK_MOOD": "How was your mood on {date}? Rate 1 to 7.",
    "CHECKIN_ASK_PRODUCTIVITY": "How was your productivity? Rate 1 to 7.",
    "CHECKIN_ASK_NOTE": "Want to add a note? Type it, or send /skip.",
    "CHECKIN_SAVED": "Logged for {date}: mood {mood}/7, productivity {productivity}/7.",
    "CHECKIN_ENRICHED": " Sleep: {sleep_hours:.1f}h, steps: {steps}.",
    "CHECKIN_CANCELLED": "Okay, cancelled.",
    # /stats, /week
    "STATS_HEADER": "Last {days} days:",
    "STATS_ROW": "{date}: mood {mood}/7, productivity {productivity}/7",
    "STATS_EMPTY": "No check-ins yet.",
    "STATS_TREND": "Mood trend: {mood_trend} Productivity trend: {productivity_trend}",
    "WEEK_HEADER": "This week ({start} — {end}):",
    "WEEK_AVERAGES": "Average mood: {avg_mood:.1f}, average productivity: {avg_productivity:.1f}",
    "WEEK_EMPTY": "No check-ins yet this week.",
    # /settings
    "SETTINGS_CURRENT": (
        "Current settings:\nReminder hour: {hour}:00\nTimezone: {timezone}\nReminders: {reminders}\n"
        "Language: {language}"
    ),
    "SETTINGS_REMINDERS_ON": "on",
    "SETTINGS_REMINDERS_OFF": "off",
    "SETTINGS_USAGE": (
        "Usage: /settings hour <0-23> | /settings timezone <IANA> | /settings reminders on|off | "
        "/settings language en|ru"
    ),
    "SETTINGS_HOUR_UPDATED": "Reminder hour updated: {hour}:00",
    "SETTINGS_HOUR_INVALID": "Hour must be a number between 0 and 23.",
    "SETTINGS_TIMEZONE_UPDATED": "Timezone updated: {timezone}",
    "SETTINGS_TIMEZONE_INVALID": "Couldn't recognize timezone: {timezone}",
    "SETTINGS_REMINDERS_UPDATED": "Reminders are now {state}.",
    "SETTINGS_REMINDERS_USAGE": "Send /settings reminders on or /settings reminders off.",
    "SETTINGS_LANGUAGE_UPDATED": "Language updated: {language}",
    "SETTINGS_LANGUAGE_INVALID": "Language must be 'en' or 'ru'.",
    # Reminder job
    "REMINDER_TEXT": "Don't forget to check in today: /checkin",
    # Weekly analysis job
    "WEEKLY_INSIGHT_HEADER": "This week's summary:",
    "WEEKLY_INSIGHT_EMPTY": "Not enough data to analyze this week.",
}

_RU: dict[str, str] = {
    "CHECKIN_DATE_CONFIRM": "Сейчас раннее утро. Записать за {yesterday} или за сегодня ({today})?",
    "CHECKIN_DATE_BUTTON_YESTERDAY": "Вчера ({date})",
    "CHECKIN_DATE_BUTTON_TODAY": "Сегодня",
    "CHECKIN_ASK_MOOD": "Как настроение {date}? Оцените от 1 до 7.",
    "CHECKIN_ASK_PRODUCTIVITY": "Как продуктивность? Оцените от 1 до 7.",
    "CHECKIN_ASK_NOTE": "Хотите добавить заметку? Напишите её или отправьте /skip.",
    "CHECKIN_SAVED": "Записано за {date}: настроение {mood}/7, продуктивность {productivity}/7.",
    "CHECKIN_ENRICHED": " Сон: {sleep_hours:.1f} ч, шаги: {steps}.",
    "CHECKIN_CANCELLED": "Хорошо, отменено.",
    "STATS_HEADER": "Последние {days} дн.:",
    "STATS_ROW": "{date}: настроение {mood}/7, продуктивность {productivity}/7",
    "STATS_EMPTY": "Пока нет записей.",
    "STATS_TREND": "Тренд настроения: {mood_trend} Тренд продуктивности: {productivity_trend}",
    "WEEK_HEADER": "Эта неделя ({start} — {end}):",
    "WEEK_AVERAGES": "Среднее настроение: {avg_mood:.1f}, средняя продуктивность: {avg_productivity:.1f}",
    "WEEK_EMPTY": "На этой неделе пока нет записей.",
    "SETTINGS_CURRENT": (
        "Текущие настройки:\nЧас напоминания: {hour}:00\nЧасовой пояс: {timezone}\nНапоминания: {reminders}\n"
        "Язык: {language}"
    ),
    "SETTINGS_REMINDERS_ON": "вкл",
    "SETTINGS_REMINDERS_OFF": "выкл",
    "SETTINGS_USAGE": (
        "Использование: /settings hour <0-23> | /settings timezone <IANA> | /settings reminders on|off | "
        "/settings language en|ru"
    ),
    "SETTINGS_HOUR_UPDATED": "Час напоминания обновлён: {hour}:00",
    "SETTINGS_HOUR_INVALID": "Час должен быть числом от 0 до 23.",
    "SETTINGS_TIMEZONE_UPDATED": "Часовой пояс обновлён: {timezone}",
    "SETTINGS_TIMEZONE_INVALID": "Не удалось распознать часовой пояс: {timezone}",
    "SETTINGS_REMINDERS_UPDATED": "Напоминания теперь {state}.",
    "SETTINGS_REMINDERS_USAGE": "Отправьте /settings reminders on или /settings reminders off.",
    "SETTINGS_LANGUAGE_UPDATED": "Язык обновлён: {language}",
    "SETTINGS_LANGUAGE_INVALID": "Язык должен быть 'en' или 'ru'.",
    "REMINDER_TEXT": "Не забудьте отметиться сегодня: /checkin",
    "WEEKLY_INSIGHT_HEADER": "Итоги недели:",
    "WEEKLY_INSIGHT_EMPTY": "Недостаточно данных для анализа этой недели.",
}

_BY_LANGUAGE: dict[str, dict[str, str]] = {"en": _EN, "ru": _RU}


def t(key: str, lang: str, **kwargs: object) -> str:
    template = _BY_LANGUAGE.get(lang, _EN)[key]
    return template.format(**kwargs) if kwargs else template
