from astock_v2.data.legacy_market_provider import (
    legacy_daily_result,
    legacy_intraday_result,
    legacy_quote_result,
)


def test_quote_adapter_preserves_v1_payload_without_recalculation():
    payload = {
        "ok": True,
        "code": "000001",
        "raw_code": "sz000001",
        "name": "平安银行",
        "price": 10.21,
        "pct": 1.23,
        "change": 0.12,
        "prev_close": 10.09,
        "open": 10.10,
        "high": 10.30,
        "low": 10.05,
        "volume": 123456,
        "amount": 987654321.0,
        "turnover": 2.34,
        "volume_ratio": 1.56,
        "source": "sina_spot",
        "fetched_at": "2026-09-27T09:31:00+08:00",
    }

    result = legacy_quote_result(
        payload, available_time="2026-09-27T09:31:01+08:00"
    )

    assert result.data is payload
    assert result.data["code"] == "000001"
    assert result.data["price"] == 10.21
    assert result.data["pct"] == 1.23
    assert result.data["turnover"] == 2.34
    assert result.source == "sina_spot"
    assert result.fallback is False


def test_daily_adapter_preserves_v1_computed_fields():
    payload = {
        "ok": True,
        "code": "000001",
        "latest_date": "2026-09-26",
        "latest": {
            "open": 10.10,
            "close": 10.21,
            "high": 10.30,
            "low": 10.05,
            "pct": 1.23,
            "volume": 123456,
            "amount": 987654321.0,
            "turnover": None,
        },
        "prev_close": 10.09,
        "ma5": 10.02,
        "ma10": 9.88,
        "ma20": 9.71,
        "ma60": 9.55,
        "vol_ma20": 100000.0,
        "lr": 1.234,
        "recent_high20": 10.30,
        "recent_low20": 9.10,
        "closes_tail": [9.8, 9.9, 10.0, 10.1, 10.21],
        "closes60": [9.0, 9.1],
        "highs60": [10.0, 10.2],
        "lows60": [8.9, 9.0],
        "kline_count": 60,
        "trend_analysis": {"is_trend": True},
        "source": "legacy_daily",
        "fetched_at": "2026-09-27T01:00:00+00:00",
    }

    result = legacy_daily_result(
        payload, available_time="2026-09-27T02:00:00+00:00"
    )

    assert result.data is payload
    assert result.data["ma5"] == 10.02
    assert result.data["ma20"] == 9.71
    assert result.data["lr"] == 1.234
    assert result.data["trend_analysis"] == {"is_trend": True}
    assert result.available_time == "2026-09-27T02:00:00+00:00"


def test_daily_fallback_semantics_survive_adapter():
    payload = {
        "ok": True,
        "code": "000001",
        "latest_date": "2026-09-26",
        "latest": {"close": 10.0},
        "source": "daily_close_fallback",
        "fallback": True,
        "fetched_at": "2026-09-27T01:00:00+00:00",
        "_note": "上一交易日收盘价兜底",
    }

    result = legacy_daily_result(
        payload, available_time="2026-09-27T02:00:00+00:00"
    )

    assert result.fallback is True
    assert result.source == "daily_close_fallback"
    assert result.warnings == ["上一交易日收盘价兜底"]


def test_intraday_adapter_preserves_scale_and_ohlcv_rows():
    payload = {
        "ok": True,
        "code": "000001",
        "scale": 5,
        "klines": [
            {
                "time": "2026-09-26T14:55:00+08:00",
                "open": 10.0,
                "high": 10.2,
                "low": 9.9,
                "close": 10.1,
                "volume": 1000,
            },
            {
                "time": "2026-09-26T15:00:00+08:00",
                "open": 10.1,
                "high": 10.3,
                "low": 10.0,
                "close": 10.2,
                "volume": 1200,
            },
        ],
        "count": 2,
        "source": "legacy_sina_minute",
        "fetched_at": "2026-09-26T15:01:00+08:00",
    }

    result = legacy_intraday_result(
        payload, available_time="2026-09-26T15:02:00+08:00"
    )

    assert result.data is payload
    assert result.data["scale"] == 5
    assert result.data["count"] == 2
    assert result.data["klines"] == payload["klines"]
    assert result.available_time == "2026-09-26T15:02:00+08:00"
