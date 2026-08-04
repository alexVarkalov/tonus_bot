"""Flat English user strings. Single user, single language — no i18n layer."""

# /checkin — date confirmation (only shown during the 00:00-04:00 local ambiguity window)
CHECKIN_DATE_CONFIRM = "It's early morning. Log {yesterday} or today ({today})?"
CHECKIN_DATE_BUTTON_YESTERDAY = "Yesterday ({date})"
CHECKIN_DATE_BUTTON_TODAY = "Today"

# /checkin — mood/productivity/note steps
CHECKIN_ASK_MOOD = "How was your mood on {date}? Rate 1 to 7."
CHECKIN_ASK_PRODUCTIVITY = "How was your productivity? Rate 1 to 7."
CHECKIN_ASK_NOTE = "Want to add a note? Type it, or send /skip."
CHECKIN_SAVED = "Logged for {date}: mood {mood}/7, productivity {productivity}/7."
CHECKIN_ENRICHED = " Sleep: {sleep_hours:.1f}h, steps: {steps}."
CHECKIN_CANCELLED = "Okay, cancelled."

# /stats, /week
STATS_HEADER = "Last {days} days:"
STATS_ROW = "{date}: mood {mood}/7, productivity {productivity}/7"
STATS_EMPTY = "No check-ins yet."
STATS_TREND = "Mood trend: {mood_trend} Productivity trend: {productivity_trend}"

WEEK_HEADER = "This week ({start} — {end}):"
WEEK_AVERAGES = "Average mood: {avg_mood:.1f}, average productivity: {avg_productivity:.1f}"
WEEK_EMPTY = "No check-ins yet this week."

# /settings
SETTINGS_CURRENT = "Current settings:\nReminder hour: {hour}:00\nTimezone: {timezone}\nReminders: {reminders}"
SETTINGS_REMINDERS_ON = "on"
SETTINGS_REMINDERS_OFF = "off"
SETTINGS_USAGE = "Usage: /settings hour <0-23> | /settings timezone <IANA> | /settings reminders on|off"
SETTINGS_HOUR_UPDATED = "Reminder hour updated: {hour}:00"
SETTINGS_HOUR_INVALID = "Hour must be a number between 0 and 23."
SETTINGS_TIMEZONE_UPDATED = "Timezone updated: {timezone}"
SETTINGS_TIMEZONE_INVALID = "Couldn't recognize timezone: {timezone}"
SETTINGS_REMINDERS_UPDATED = "Reminders are now {state}."
SETTINGS_REMINDERS_USAGE = "Send /settings reminders on or /settings reminders off."

# Reminder job
REMINDER_TEXT = "Don't forget to check in today: /checkin"

# Weekly analysis job
WEEKLY_INSIGHT_HEADER = "This week's summary:"
WEEKLY_INSIGHT_EMPTY = "Not enough data to analyze this week."
