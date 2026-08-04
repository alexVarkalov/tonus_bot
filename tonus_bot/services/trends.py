from __future__ import annotations

from collections.abc import Sequence

TREND_UP = "↑"
TREND_DOWN = "↓"
TREND_FLAT = "→"
TREND_UNKNOWN = "–"


def average(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def trend_arrow(current: float | None, previous: float | None, *, threshold: float = 0.3) -> str:
    if current is None or previous is None:
        return TREND_UNKNOWN
    delta = current - previous
    if delta > threshold:
        return TREND_UP
    if delta < -threshold:
        return TREND_DOWN
    return TREND_FLAT
