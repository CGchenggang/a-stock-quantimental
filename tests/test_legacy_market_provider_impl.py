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
