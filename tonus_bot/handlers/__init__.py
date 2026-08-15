from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ConversationHandler, MessageHandler, filters

from tonus_bot.handlers.checkin import (
    CONFIRM_DATE,
    MOOD,
    NOTE,
    PRODUCTIVITY,
    cmd_cancel_checkin,
    cmd_checkin,
    cmd_skip_note,
    on_date_callback,
    on_mood_callback,
    on_note_text,
    on_productivity_callback,
    reminder_job,
)
from tonus_bot.handlers.settings import cmd_settings
from tonus_bot.handlers.stats import cmd_stats, cmd_week, weekly_analysis_job

__all__ = ["register_handlers", "reminder_job", "weekly_analysis_job"]


def register_handlers(application: Application) -> None:
    checkin_conversation = ConversationHandler(
        entry_points=[CommandHandler("checkin", cmd_checkin)],
        states={
            CONFIRM_DATE: [CallbackQueryHandler(on_date_callback, pattern=r"^checkin:date:")],
            MOOD: [CallbackQueryHandler(on_mood_callback, pattern=r"^checkin:mood:")],
            PRODUCTIVITY: [CallbackQueryHandler(on_productivity_callback, pattern=r"^checkin:prod:")],
            NOTE: [
                CommandHandler("skip", cmd_skip_note),
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_note_text),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel_checkin),
            # Re-sending /checkin mid-flow restarts it instead of being silently dropped by
            # whichever state's handlers are currently active.
            CommandHandler("checkin", cmd_checkin),
        ],
        conversation_timeout=1800,
    )
    application.add_handler(checkin_conversation)
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("week", cmd_week))
    application.add_handler(CommandHandler("settings", cmd_settings))
