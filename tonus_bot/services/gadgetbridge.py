from __future__ import annotations

import asyncio
import sqlite3
from datetime import date, datetime
from zoneinfo import ZoneInfo

# Gadgetbridge stores activity samples in a per-device-coprocessor table (e.g.
# MI_BAND_ACTIVITY_SAMPLE, HUAWEI_ACTIVITY_SAMPLE...) whose name and RAW_KIND values depend on the
# paired device and installed app version. Before trusting this against a real export, inspect it
# with `sqlite3 <path> ".schema"` and adjust _CANDIDATE_TABLES / _SLEEP_KINDS to match — don't rely
# on the Gadgetbridge README, it lags behind.
_CANDIDATE_TABLES = ("MI_BAND_ACTIVITY_SAMPLE", "HUAWEI_ACTIVITY_SAMPLE", "BASE_ACTIVITY_SAMPLE")
_SLEEP_KINDS = (2, 4, 5, 6)


async def read_sleep_and_steps(
    db_path: str | None, checkin_date: date, timezone: str
) -> tuple[float | None, int | None]:
    """Best-effort read; returns (None, None) whenever the file, table, or day's data is missing."""
    if not db_path:
        return None, None
    return await asyncio.to_thread(_read_sleep_and_steps_sync, db_path, checkin_date, timezone)


def _read_sleep_and_steps_sync(db_path: str, checkin_date: date, timezone: str) -> tuple[float | None, int | None]:
    zone = ZoneInfo(timezone)
    day_start = int(datetime(checkin_date.year, checkin_date.month, checkin_date.day, tzinfo=zone).timestamp())
    day_end = day_start + 24 * 3600

    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            table = _find_activity_table(conn)
            if table is None:
                return None, None
            rows = conn.execute(
                f"SELECT RAW_KIND, STEPS FROM {table} WHERE TIMESTAMP >= ? AND TIMESTAMP < ?",
                (day_start, day_end),
            ).fetchall()
    except sqlite3.Error, OSError:
        return None, None

    if not rows:
        return None, None

    total_steps = sum(steps for _kind, steps in rows if steps and steps > 0)
    sleep_minutes = sum(1 for kind, _steps in rows if kind in _SLEEP_KINDS)
    sleep_hours = (sleep_minutes / 60) if sleep_minutes else None
    return sleep_hours, (total_steps or None)


def _find_activity_table(conn: sqlite3.Connection) -> str | None:
    existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for table in _CANDIDATE_TABLES:
        if table in existing:
            return table
    return None
