from astock_v2.provider_research import build_research_packet_from_provider
from astock_v2.data.legacy_market_provider_impl import LegacyMarketProvider


def test_provider_research_builds_evidence_packet_and_health():
    provider = LegacyMarketProvider(
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
    )
    packet = build_research_packet_from_provider(
        provider,
        symbol="000001",
        decision_time="2026-09-27T08:00:00+08:00",
        daily_start="2026-09-20",
        daily_end="2026-09-26",
    )
    assert packet.decision_time == "2026-09-27T00:00:00+00:00"
    assert packet.market["quotes"]["000001"]["price"] == 10.2
    assert packet.stock["daily"]["latest"]["close"] == 10.0
    assert packet.model == {}
    assert packet.data_quality["provider_results"] == 2
    assert packet.data_quality["fallback_ratio"] == 0.0
