import pytest

from astock_v2.data.pit_adapter import minute_klines_to_datapoints


def test_minute_klines_preserve_event_and_available_time():
    points = minute_klines_to_datapoints(
        {
            "code": "000001",
            "scale": 5,
            "klines": [
                {
                    "time": "2026-09-25T14:55:00+08:00",
                    "open": 10.0,
                    "high": 10.2,
                    "low": 9.9,
                    "close": 10.1,
                    "volume": 1000,
                }
            ],
        },
        fetched_at="2026-09-25T15:01:00+08:00",
    )

    assert len(points) == 1
    point = points[0]
    assert point.symbol == "000001"
    assert point.event_time == "2026-09-25T14:55:00+08:00"
    assert point.available_time == "2026-09-25T15:01:00+08:00"
    assert point.source == "legacy_sina_minute"
    assert point.source_type == "legacy_adapter"
    assert point.value["scale"] == 5
    assert point.value["close"] == 10.1


def test_minute_klines_reject_future_event_relative_to_fetch():
    with pytest.raises(ValueError, match="available_time"):
        minute_klines_to_datapoints(
            {
                "code": "000001",
                "klines": [
                    {"time": "2026-09-25T15:05:00+08:00", "close": 10.1}
                ],
            },
            fetched_at="2026-09-25T15:01:00+08:00",
        )


def test_minute_klines_require_symbol_and_list():
    with pytest.raises(ValueError, match="code"):
        minute_klines_to_datapoints({}, fetched_at="2026-09-25T15:01:00+08:00")

    with pytest.raises(ValueError, match="klines"):
        minute_klines_to_datapoints(
            {"code": "000001"},
            fetched_at="2026-09-25T15:01:00+08:00",
        )
