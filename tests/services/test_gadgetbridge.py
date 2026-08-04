from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from tonus_bot.services.gadgetbridge import read_sleep_and_steps


@pytest.mark.asyncio
async def test_read_sleep_and_steps_returns_none_without_path() -> None:
    assert await read_sleep_and_steps(None, date(2026, 1, 1), "UTC") == (None, None)


@pytest.mark.asyncio
async def test_read_sleep_and_steps_returns_none_for_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    assert await read_sleep_and_steps(str(missing), date(2026, 1, 1), "UTC") == (None, None)


@pytest.mark.asyncio
async def test_read_sleep_and_steps_returns_none_without_matching_table(tmp_path: Path) -> None:
    db_path = tmp_path / "gadgetbridge.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE UNRELATED_TABLE (X INTEGER)")
    conn.commit()
    conn.close()

    assert await read_sleep_and_steps(str(db_path), date(2026, 1, 1), "UTC") == (None, None)


@pytest.mark.asyncio
async def test_read_sleep_and_steps_reads_matching_samples(tmp_path: Path) -> None:
    db_path = tmp_path / "gadgetbridge.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE MI_BAND_ACTIVITY_SAMPLE (TIMESTAMP INTEGER, RAW_KIND INTEGER, STEPS INTEGER)")
    day_start = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
    conn.executemany(
        "INSERT INTO MI_BAND_ACTIVITY_SAMPLE VALUES (?, ?, ?)",
        [
            (day_start + 60, 2, 0),  # one minute of light sleep
            (day_start + 120, 2, 0),  # another minute of light sleep
            (day_start + 3600, 1, 100),  # one hour in, activity with steps
        ],
    )
    conn.commit()
    conn.close()

    sleep_hours, steps = await read_sleep_and_steps(str(db_path), date(2026, 1, 1), "UTC")

    assert steps == 100
    assert sleep_hours == pytest.approx(2 / 60)
