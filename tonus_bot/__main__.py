from __future__ import annotations

import logging
import os
import sys
import warnings
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from anthropic import AsyncAnthropic
from telegram import Update
from telegram.ext import Application
from telegram.warnings import PTBUserWarning

from tonus_bot.config import Settings
from tonus_bot.db import Database
from tonus_bot.handlers import register_handlers, reminder_job, weekly_analysis_job
from tonus_bot.repositories import CheckinRepository, InsightRepository, SettingsRepository
from tonus_bot.services import AnalysisService, CheckinService

_WEEKLY_ANALYSIS_LOCAL_HOUR = 20  # Sunday evening, in Settings.default_timezone


def _load_dotenv_if_present() -> None:
    """Minimal .env loader to avoid an extra dependency; ignores parse errors."""
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        return


def _seconds_until_sunday_evening(timezone: str) -> float:
    now = datetime.now(ZoneInfo(timezone))
    days_until_sunday = (6 - now.weekday()) % 7
    candidate = (now + timedelta(days=days_until_sunday)).replace(
        hour=_WEEKLY_ANALYSIS_LOCAL_HOUR, minute=0, second=0, microsecond=0
    )
    if candidate <= now:
        candidate += timedelta(days=7)
    return (candidate - now).total_seconds()


async def _post_init(application: Application) -> None:
    db: Database = application.bot_data["db"]
    await db.init()

    application.bot_data["http_client"] = httpx.AsyncClient()
    application.job_queue.scheduler.configure(timezone="UTC")

    settings: Settings = application.bot_data["settings"]
    checkin_repo = CheckinRepository(db)
    insight_repo = InsightRepository(db)
    settings_repo = SettingsRepository(db)
    anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    application.bot_data["settings_repository"] = settings_repo
    application.bot_data["anthropic_client"] = anthropic_client
    application.bot_data["checkin_service"] = CheckinService(checkin_repo)
    application.bot_data["analysis_service"] = AnalysisService(settings, anthropic_client, checkin_repo, insight_repo)

    application.job_queue.run_repeating(reminder_job, interval=3600, first=10, name="checkin_reminder")
    application.job_queue.run_repeating(
        weekly_analysis_job,
        interval=604800,
        first=_seconds_until_sunday_evening(settings.default_timezone),
        name="weekly_analysis",
    )


async def _post_shutdown(application: Application) -> None:
    client: httpx.AsyncClient | None = application.bot_data.pop("http_client", None)
    if client is not None:
        await client.aclose()
    anthropic_client: AsyncAnthropic | None = application.bot_data.pop("anthropic_client", None)
    if anthropic_client is not None:
        await anthropic_client.close()


def main() -> None:
    _load_dotenv_if_present()
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # /checkin intentionally mixes CallbackQueryHandler with CommandHandler/MessageHandler
    # (the NOTE state), so per_message=True isn't an option — PTB warns regardless, even
    # though per_message=False is correct for a linear, one-keyboard-at-a-time conversation.
    warnings.filterwarnings("ignore", message=r"^If 'per_message=False'", category=PTBUserWarning)

    try:
        settings = Settings.from_env()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc

    application = (
        Application.builder().token(settings.bot_token).post_init(_post_init).post_shutdown(_post_shutdown).build()
    )

    application.bot_data["settings"] = settings
    application.bot_data["db"] = Database(settings.database_url)

    register_handlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
