from __future__ import annotations

import asyncio

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from tonus_bot.persistence import Checkin, UserSettings, WeeklyInsight
from tonus_bot.persistence.checkin_store import CheckinStore
from tonus_bot.persistence.insight_store import InsightStore
from tonus_bot.persistence.models import Base
from tonus_bot.persistence.settings_store import SettingsStore

__all__ = ["Checkin", "Database", "UserSettings", "WeeklyInsight"]


class Database(CheckinStore, InsightStore, SettingsStore):
    """PostgreSQL persistence via SQLAlchemy ORM; public methods stay async."""

    def __init__(self, url: str) -> None:
        self._engine: Engine = create_engine(url, future=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False, class_=Session)

    async def init(self) -> None:
        await asyncio.to_thread(self._init_sync)

    def _init_sync(self) -> None:
        Base.metadata.create_all(self._engine)
        # Additive migration for deployments created before language support existed;
        # create_all() alone won't add columns to a table that already exists.
        with self._engine.begin() as conn:
            conn.execute(text("ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS language TEXT NOT NULL DEFAULT 'en'"))
