import pytest

from astock_v2.data.legacy_market_provider import (
    legacy_daily_result,
    legacy_intraday_result,
    legacy_quote_result,
)


def test_legacy_quote_requires_explicit_availability():
    result = legacy_quote_result(
        {
            "source": "sina_spot",
            "fetched_at": "2026-09-27T09:31:00+08:00",
            "code": "000001",
            "price": 10.2,
        },
        available_time="2026-09-27T09:31:01+08:00",
    )
    assert result.source_type == "legacy_quote_provider"
    assert result.available_time == "2026-09-27T09:31:01+08:00"


def test_legacy_daily_preserves_fallback_marker():
    result = legacy_daily_result(
        {
            "source": "daily_close_fallback",
            "fetched_at": "2026-09-27T00:00:00+00:00",
            "fallback": True,
            "latest_date": "2026-09-26",
            "latest": {"close": 10.0},
        },
        available_time="2026-09-27T01:00:00+00:00",
    )
    assert result.fallback is True
    assert result.data["latest_date"] == "2026-09-26"


def test_legacy_intraday_requires_scale_and_klines():
    payload = {
        "source": "intraday_fallback",
        "fetched_at": "2026-09-27T06:00:00+00:00",
        "scale": 5,
        "klines": [{"time": "2026-09-27T05:55:00+00:00", "close": 10.0}],
    }
    result = legacy_intraday_result(
        payload, available_time="2026-09-27T06:01:00+00:00"
    )
    assert result.data["scale"] == 5


def test_legacy_intraday_rejects_unknown_granularity():
    with pytest.raises(ValueError, match="scale"):
        legacy_intraday_result(
            {
                "source": "intraday_fallback",
                "fetched_at": "2026-09-27T06:00:00+00:00",
                "klines": [],
            },
            available_time="2026-09-27T06:01:00+00:00",
        )
