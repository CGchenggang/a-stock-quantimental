from astock_v2.data.legacy_market_provider_impl import LegacyMarketProvider
from astock_v2.data.legacy_market_inputs import LegacyMarketInputs


def _provider():
    return LegacyMarketProvider(
        realtime_fetcher=lambda: {
            "ok": True,
            "quotes": {
                "000001": {"price": 10.2, "pct": 2.0},
                "000002": {"price": 8.0, "pct": -1.0},
                "000003": {"price": 5.0, "pct": 0.0},
            },
            "source": "sina_spot",
            "fetched_at": "2026-09-27T04:00:00+00:00",
        },
        daily_fetcher=lambda symbol, days: {},
        sector_fetcher=lambda: {
            "ok": True,
            "sectors": [
                {"name": "A", "pct": 2.0},
                {"name": "B", "pct": -1.0},
            ],
            "source": "legacy_sector",
            "ts": "2026-09-27T04:00:00+00:00",
        },
        index_fetcher=lambda symbol: {
            "ok": True,
            "symbol": symbol,
            "latest_date": "2026-09-26",
            "latest_close": 4000.0,
            "pct": 1.2,
            "ma20": 3950.0,
            "above_ma20": True,
            "source": "legacy_index",
            "fetched_at": "2026-09-27T04:00:00+00:00",
        },
    )


def test_market_provider_supports_explicit_market_wide_quote():
    result = _provider().quote([])
    assert result.data["requested_symbols"] == ["__ALL__"]
    assert set(result.data["quotes"]) == {"000001", "000002", "000003"}


def test_legacy_market_inputs_labels_breadth_as_proxy():
    result = LegacyMarketInputs(_provider()).snapshot()
    breadth = result["breadth"]
    assert breadth["breadth"] == (2 - 1) / 3
    assert breadth["proxy"] is True
    assert breadth["limit_up"] == 0
    assert breadth["limit_down"] == 0


def test_provider_bridges_index_and_sector():
    provider = _provider()
    index = provider.index_daily("sh000300")
    sector = provider.sector_board()
    assert index.source_type == "legacy_index_provider"
    assert index.data["above_ma20"] is True
    assert sector.source_type == "legacy_sector_provider"
    assert len(sector.data["sectors"]) == 2


def test_regime_inputs_keep_missing_p3_fields_explicit():
    result = LegacyMarketInputs(_provider()).regime_inputs()
    assert result["inputs"]["breadth"] == (2 - 1) / 3
    assert result["inputs"]["turnover_z"] is None
    assert result["inputs"]["volatility_z"] is None
    assert result["inputs"]["liquidity"] is None
    assert set(result["missing_fields"]) == {"turnover_z", "volatility_z", "liquidity"}
    assert "index" in result["provenance"]
    assert "sector" in result["provenance"]
