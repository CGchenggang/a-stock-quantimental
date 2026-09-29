from astock_v2.provider_research import build_research_packet_from_provider
from astock_v2.data.legacy_market_provider_impl import LegacyMarketProvider
from astock_v2.data.providers import PitStatus, ProviderResult, normalize_time, pit_status
from astock_v2.data_quality import summarize_pit


def test_provider_research_builds_evidence_packet_and_health():
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {
            "ok": True,
            "quotes": {"000001": {"price": 10.2}},
            "source": "sina_spot",
            "fetched_at": "2026-09-26T16:00:00+00:00",
            "available_time": "2026-09-26T16:00:00+00:00",
        },
        index_fetcher=lambda symbol: {
            "ok": True, "symbol": symbol, "latest_date": "2026-09-26",
            "latest_close": 4000.0, "pct": 1.0, "ma20": 3950.0,
            "above_ma20": True, "source": "legacy_index",
            "fetched_at": "2026-09-26T16:00:00+00:00",
        },
        sector_fetcher=lambda: {
            "ok": True, "sectors": [{"name": "A", "pct": 1.0}, {"name": "B", "pct": -1.0}],
            "source": "legacy_sector", "ts": "2026-09-26T16:00:00+00:00",
        },
        daily_fetcher=lambda symbol, days: {
            "ok": True, "code": symbol, "latest_date": "2026-09-26",
            "latest": {"close": 10.0}, "source": "legacy_daily",
            "fetched_at": "2026-09-26T16:00:00+00:00",
            "available_time": "2026-09-26T16:00:00+00:00",
        },
    )
    packet = build_research_packet_from_provider(
        provider, symbol="000001", decision_time="2026-09-27T08:00:00+08:00",
        daily_start="2026-09-20", daily_end="2026-09-26",
    )
    assert packet.decision_time == "2026-09-27T00:00:00+00:00"
    assert packet.market["quotes"]["000001"]["price"] == 10.2
    assert packet.stock["daily"]["latest"]["close"] == 10.0
    assert packet.model == {}
    assert packet.data_quality["provider_results"] == 4
    assert packet.data_quality["fallback_ratio"] == 0.0
    assert packet.data_quality["availability_complete"] is True
    assert packet.data_quality["pit_admissible"] is True
    assert packet.data_quality["pit_admissible_ratio"] == 1.0
    assert packet.data_quality["future_data_count"] == 0


def test_provider_research_attaches_conservative_market_regime_context():
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {
            "ok": True,
            "quotes": {"000001": {"price": 10.2, "pct": 2.0}, "000002": {"price": 8.0, "pct": -1.0}},
            "source": "sina_spot", "fetched_at": "2026-09-26T16:00:00+00:00",
            "available_time": "2026-09-26T16:00:00+00:00",
        },
        daily_fetcher=lambda symbol, days: {
            "ok": True, "code": symbol, "latest_date": "2026-09-26",
            "latest": {"close": 10.0}, "source": "legacy_daily",
            "fetched_at": "2026-09-26T16:00:00+00:00",
            "available_time": "2026-09-26T16:00:00+00:00",
        },
        index_fetcher=lambda symbol: {
            "ok": True, "symbol": symbol, "latest_date": "2026-09-26",
            "latest_close": 4000.0, "pct": 1.2, "ma20": 3950.0,
            "above_ma20": True, "source": "legacy_index",
            "fetched_at": "2026-09-26T16:00:00+00:00",
        },
        sector_fetcher=lambda: {
            "ok": True, "sectors": [{"name": "A", "pct": 2.0}, {"name": "B", "pct": -1.0}],
            "source": "legacy_sector", "ts": "2026-09-26T16:00:00+00:00",
        },
        turnover_fetcher=lambda: {
            "turnover_z": None, "pit_ready": False, "amount": 100.0,
            "ts": "2026-09-26T16:00:00+00:00",
        },
    )
    packet = build_research_packet_from_provider(
        provider, symbol="000001", decision_time="2026-09-27T08:00:00+08:00",
        daily_start="2026-09-20", daily_end="2026-09-26",
    )
    assert packet.market["regime"]["regime"] == "UNKNOWN"
    assert packet.market["regime"]["confidence"] == 0.0
    assert "turnover_z" in packet.market["regime_missing_fields"]
    assert packet.market["regime_proxy_fields"]
    assert packet.market["regime_data_quality"]["provider_results"] == 4
    assert packet.market["regime_data_quality"]["pit_admissible"] is True


def test_provider_research_rejects_future_available_time():
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {
            "ok": True, "quotes": {"000001": {"price": 10.2}},
            "source": "sina_spot", "fetched_at": "2026-09-27T02:00:00+00:00",
            "available_time": "2026-09-27T02:00:00+00:00",
        },
        daily_fetcher=lambda symbol, days: {
            "ok": True, "code": symbol, "latest_date": "2026-09-26",
            "latest": {"close": 10.0}, "source": "legacy_daily",
            "fetched_at": "2026-09-26T16:00:00+00:00",
            "available_time": "2026-09-26T16:00:00+00:00",
        },
        index_fetcher=lambda symbol: {
            "ok": True, "symbol": symbol, "latest_date": "2026-09-26",
            "latest_close": 4000.0, "pct": 1.2, "ma20": 3950.0,
            "above_ma20": True, "source": "legacy_index",
            "fetched_at": "2026-09-27T02:00:00+00:00",
        },
        sector_fetcher=lambda: {
            "ok": True, "sectors": [{"name": "A", "pct": 2.0}, {"name": "B", "pct": -1.0}],
            "source": "legacy_sector", "ts": "2026-09-27T02:00:00+00:00",
        },
    )
    packet = build_research_packet_from_provider(
        provider, symbol="000001", decision_time="2026-09-27T08:00:00+08:00",
        daily_start="2026-09-20", daily_end="2026-09-26",
    )
    assert packet.market["quotes"] == {}
    assert packet.stock["daily"]["latest"]["close"] == 10.0
    assert packet.market["regime_inputs"]["index_trend"] is None
    assert packet.market["regime_inputs"]["sector_dispersion"] is None
    assert packet.market["regime_inputs"]["breadth"] is None
    assert packet.market["regime"]["regime"] == "UNKNOWN"
    assert packet.data_quality["future_data_count"] == 3
    assert packet.data_quality["pit_admissible_ratio"] == 0.25
    assert packet.data_quality["pit_admissible"] is False


def test_provider_research_allows_exact_decision_time_boundary():
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {
            "ok": True, "quotes": {"000001": {"price": 10.2}},
            "source": "sina_spot", "fetched_at": "2026-09-27T08:00:00+00:00",
            "available_time": "2026-09-27T00:00:00+00:00",
        },
        daily_fetcher=lambda symbol, days: {
            "ok": True, "code": symbol, "latest_date": "2026-09-26",
            "latest": {"close": 10.0}, "source": "legacy_daily",
            "fetched_at": "2026-09-27T08:00:00+00:00",
            "available_time": "2026-09-27T00:00:00+00:00",
        },
        index_fetcher=lambda symbol: {
            "ok": True, "symbol": symbol, "latest_date": "2026-09-26",
            "latest_close": 4000.0, "pct": 1.2, "ma20": 3950.0,
            "above_ma20": True, "source": "legacy_index",
            "fetched_at": "2026-09-27T00:00:00+00:00",
        },
        sector_fetcher=lambda: {
            "ok": True, "sectors": [{"name": "A", "pct": 2.0}, {"name": "B", "pct": -1.0}],
            "source": "legacy_sector", "ts": "2026-09-27T00:00:00+00:00",
        },
    )
    packet = build_research_packet_from_provider(
        provider, symbol="000001", decision_time="2026-09-27T08:00:00+08:00",
        daily_start="2026-09-20", daily_end="2026-09-26",
    )
    assert packet.data_quality["pit_admissible_ratio"] == 1.0
    assert packet.data_quality["future_data_count"] == 0
    assert packet.data_quality["pit_admissible"] is True


def test_provider_pit_status_distinguishes_boundary_conditions():
    decision = "2026-09-27T08:00:00+00:00"
    base = dict(data={}, source="test", source_type="test", fetched_at=decision)
    assert pit_status(ProviderResult(**base, available_time="2026-09-27T07:59:59+00:00"), decision) is PitStatus.ADMISSIBLE
    assert pit_status(ProviderResult(**base, available_time=decision), decision) is PitStatus.ADMISSIBLE
    assert pit_status(ProviderResult(**base, available_time="2026-09-27T08:00:01+00:00"), decision) is PitStatus.FUTURE
    assert pit_status(ProviderResult(**base), decision) is PitStatus.MISSING_TIME
    assert pit_status(ProviderResult(**base, fallback=True), decision) is PitStatus.FALLBACK
    assert pit_status(ProviderResult(**base, available_time="not-a-time"), decision) is PitStatus.INVALID_TIME
    assert pit_status(ProviderResult(**base, available_time=decision), "not-a-time") is PitStatus.INVALID_TIME


def test_provider_research_health_reports_structured_pit_status_counts():
    provider = LegacyMarketProvider(
        realtime_fetcher=lambda: {
            "ok": True, "quotes": {"000001": {"price": 10.2}},
            "source": "sina_spot", "fetched_at": "2026-09-27T10:00:00+00:00",
            "available_time": "2026-09-27T10:00:00+00:00",
        },
        daily_fetcher=lambda symbol, days: {
            "ok": True, "code": symbol, "latest_date": "2026-09-26",
            "latest": {"close": 10.0}, "source": "legacy_daily",
            "fetched_at": "2026-09-27T04:00:00+00:00",
            "available_time": "2026-09-27T04:00:00+00:00",
        },
        index_fetcher=lambda symbol: {
            "ok": True, "symbol": symbol, "latest_date": "2026-09-26",
            "latest_close": 4000.0, "pct": 1.2, "ma20": 3950.0,
            "above_ma20": True, "source": "legacy_index",
            "fetched_at": "2026-09-27T10:00:00+00:00",
        },
        sector_fetcher=lambda: {
            "ok": True, "sectors": [{"name": "A", "pct": 2.0}],
            "source": "legacy_sector", "ts": "2026-09-27T10:00:00+00:00",
        },
    )
    packet = build_research_packet_from_provider(
        provider, symbol="000001", decision_time="2026-09-27T08:00:00+00:00",
        daily_start="2026-09-20", daily_end="2026-09-26",
    )
    counts = packet.data_quality["pit_status_counts"]
    assert counts["FUTURE"] == 3
    assert counts["ADMISSIBLE"] == 1
    assert counts["MISSING_TIME"] == 0
    assert counts["FALLBACK"] == 0
    assert counts["INVALID_TIME"] == 0


def test_shared_pit_data_quality_summary_is_reason_specific():
    decision = "2026-09-27T08:00:00+00:00"
    base = dict(data={}, source="test", source_type="test", fetched_at=decision)
    summary = summarize_pit([
        ProviderResult(**base, available_time=decision),
        ProviderResult(**base, available_time="2026-09-27T09:00:00+00:00"),
        ProviderResult(**base),
        ProviderResult(**base, fallback=True),
        ProviderResult(**base, available_time="bad-time"),
    ], decision)
    assert summary.total == 5
    assert summary.admissible == 1
    assert summary.admissible_ratio == 0.2
    assert summary.pit_admissible is False
    assert summary.status_counts == {
        "ADMISSIBLE": 1,
        "FUTURE": 1,
        "MISSING_TIME": 1,
        "FALLBACK": 1,
        "INVALID_TIME": 1,
    }


def test_normalize_time_is_offset_exact_and_repeat_stable():
    # lru_cache memoises this pure string->string mapping (the cache key is
    # the full input, so a hit is always equivalent to a fresh parse);
    # repeated calls and cache hits must return the canonical UTC form.
    first = normalize_time("2026-09-27T08:00:00+08:00")
    assert first == "2026-09-27T00:00:00+00:00"
    assert normalize_time("2026-09-27T08:00:00+08:00") is first
    # The Z and naive forms name a different instant (08:00 UTC, not
    # 16:00+08:00) and must stay offset-exact, not collapse into `first`.
    utc_form = normalize_time("2026-09-27T08:00:00Z")
    assert utc_form == "2026-09-27T08:00:00+00:00"
    assert normalize_time("2026-09-27T08:00:00") == utc_form
    assert normalize_time("2026-09-27T08:00:00+00:00") == utc_form
