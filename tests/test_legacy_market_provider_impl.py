from astock_v2.data.legacy_market_provider_impl import LegacyMarketProvider


def test_legacy_market_provider_wraps_v1_quote_without_recomputing():
    payload = {
        "ok": True,
        "quotes": {"000001": {"code": "000001", "price": 10.2}},
        "source": "sina_spot",
        "fetched_at": "2026-09-27T04:00:00+00:00",
    }
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: payload,
        daily_fetcher=lambda symbol, days: {},
    )
    result = provider.quote(["000001"])
    assert result.data is payload
    assert result.source == "sina_spot"
    assert result.source_type == "legacy_quote_provider"
    assert result.available_time is not None


def test_legacy_market_provider_wraps_v1_daily_and_uses_requested_window():
    calls = []

    def fetch(symbol, days):
        calls.append((symbol, days))
        return {
            "ok": True,
            "code": symbol,
            "latest_date": "2026-09-26",
            "latest": {"close": 10.0},
            "source": "legacy_daily",
            "fetched_at": "2026-09-27T04:00:00+00:00",
        }

    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {},
        daily_fetcher=fetch,
    )
    result = provider.daily("000001", "2026-09-20", "2026-09-26")
    assert calls == [("000001", 7)]
    assert result.data["latest"]["close"] == 10.0
    assert result.source_type == "legacy_daily_provider"


def test_quote_provider_scopes_full_market_snapshot_to_requested_symbols():
    payload = {
        "ok": True,
        "quotes": {
            "000001": {"code": "000001", "price": 10.2},
            "600000": {"code": "600000", "price": 8.1},
            "sz000001": {"code": "000001", "price": 10.2},
        },
        "source": "sina_spot",
        "fetched_at": "2026-09-27T04:00:00+00:00",
    }
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: payload,
        daily_fetcher=lambda symbol, days: {},
    )
    result = provider.quote(["sh600000"])
    assert result.data["requested_symbols"] == ["600000"]
    assert set(result.data["quotes"]) == {"600000"}
    assert result.data["quotes"]["600000"]["price"] == 8.1
    assert result.data["legacy_payload"] is payload


def test_daily_provider_rejects_v1_payload_beyond_requested_end_date():
    payload = {
        "ok": True,
        "code": "000001",
        "latest_date": "2026-09-27",
        "latest": {"close": 10.2},
        "source": "legacy_daily",
        "fetched_at": "2026-09-27T04:00:00+00:00",
    }
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {},
        daily_fetcher=lambda symbol, days: payload,
    )
    try:
        provider.daily("000001", "2026-09-20", "2026-09-26")
    except ValueError as exc:
        assert "beyond requested end date" in str(exc)
    else:
        raise AssertionError("future data must not cross the requested historical boundary")


def test_intraday_provider_preserves_scale_and_datalen():
    payload = {
        "ok": True,
        "code": "000001",
        "scale": 5,
        "klines": [
            {"time": "2026-09-27T09:35:00+08:00", "open": 10.0, "high": 10.1, "low": 9.9, "close": 10.05, "volume": 1000}
        ],
        "count": 1,
        "source": "legacy_sina_minute",
        "fetched_at": "2026-09-27T01:36:00+00:00",
    }
    calls = []
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {},
        daily_fetcher=lambda symbol, days: {},
        intraday_fetcher=lambda symbol, scale, datalen: (
            calls.append((symbol, scale, datalen)) or payload
        ),
    )
    result = provider.intraday("000001", scale=5, datalen=20)
    assert calls == [("000001", 5, 20)]
    assert result.data is payload
    assert result.source_type == "legacy_intraday_provider"
    assert result.data["scale"] == 5


def test_intraday_provider_rejects_invalid_scale_and_datalen():
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {},
        daily_fetcher=lambda symbol, days: {},
        intraday_fetcher=lambda symbol, scale, datalen: {},
    )
    for scale in [0, 2, 10, 120]:
        try:
            provider.intraday("000001", scale=scale)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid scale must be rejected")
    try:
        provider.intraday("000001", datalen=0)
    except ValueError:
        pass
    else:
        raise AssertionError("non-positive datalen must be rejected")


def test_daily_provider_does_not_fabricate_availability_from_fetch_time():
    provider=LegacyMarketProvider(
        realtime_fetcher=lambda: {},
        daily_fetcher=lambda symbol, days: {"latest_date":"2026-09-26","fetched_at":"2026-09-27T04:00:00+00:00"},
    )
    result=provider.daily("000001","2026-09-20","2026-09-26")
    assert result.available_time == ""
