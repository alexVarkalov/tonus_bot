from __future__ import annotations

from tonus_bot.services import trends


def test_average_of_empty_sequence_is_none() -> None:
    assert trends.average([]) is None


def test_average_computes_mean() -> None:
    assert trends.average([1, 2, 3]) == 2


def test_trend_arrow_unknown_without_data() -> None:
    assert trends.trend_arrow(None, 3.0) == trends.TREND_UNKNOWN
    assert trends.trend_arrow(3.0, None) == trends.TREND_UNKNOWN


def test_trend_arrow_up_above_threshold() -> None:
    assert trends.trend_arrow(5.0, 4.0) == trends.TREND_UP


def test_trend_arrow_down_below_threshold() -> None:
    assert trends.trend_arrow(4.0, 5.0) == trends.TREND_DOWN


def test_trend_arrow_flat_within_threshold() -> None:
    assert trends.trend_arrow(4.1, 4.0) == trends.TREND_FLAT
