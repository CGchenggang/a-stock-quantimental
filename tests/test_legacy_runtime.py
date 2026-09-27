from astock_v2.data.legacy_runtime import build_legacy_market_provider


def test_runtime_factory_wires_injected_legacy_functions():
    provider = build_legacy_market_provider(
        realtime_fetcher=lambda: {
            "ok": True,
            "quotes": {"000001": {"price": 10.2}},
            "source": "sina_spot",
            "fetched_at": "2026-09-27T04:00:00+00:00",
        },
        daily_fetcher=lambda symbol, days: {
            "ok": True,
            "code": symbol,
            "latest_date": "2026-09-26",
            "latest": {"close": 10.0},
            "source": "legacy_daily",
            "fetched_at": "2026-09-27T04:00:00+00:00",
        },
        intraday_fetcher=lambda symbol, scale, datalen: {
            "ok": True,
            "code": symbol,
            "scale": scale,
            "klines": [],
        },
    )
    assert provider.name == "legacy_v1"
    assert provider.quote(["000001"]).data["quotes"]["000001"]["price"] == 10.2
    assert provider.daily("000001", "2026-09-26", "2026-09-26").data["latest"]["close"] == 10.0
    assert provider.intraday("000001", 5, 20).data["scale"] == 5
