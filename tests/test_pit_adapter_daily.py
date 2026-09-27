import pytest

from astock_v2.data.pit_adapter import daily_latest_to_datapoint


def test_daily_latest_requires_explicit_availability_time():
    point = daily_latest_to_datapoint(
        {
            "code": "000001",
            "latest_date": "2026-09-25",
            "latest": {"close": 10.1, "volume": 1000},
        },
        available_time="2026-09-26T08:00:00+08:00",
    )
    assert point.event_time == "2026-09-25T00:00:00+00:00"
    assert point.available_time == "2026-09-26T08:00:00+08:00"
    assert point.value["close"] == 10.1


def test_daily_latest_rejects_unavailable_future_data():
    with pytest.raises(ValueError, match="available_time"):
        daily_latest_to_datapoint(
            {
                "code": "000001",
                "latest_date": "2026-09-26",
                "latest": {"close": 10.1},
            },
            available_time="2026-09-25T16:00:00+08:00",
        )
