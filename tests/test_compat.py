import pytest

from astock_v2.compat import (
    LEGACY_SCRIPT_ROLES,
    call_legacy_realtime,
    legacy_regime_mapping,
)


def test_legacy_observation_preserves_fallback_and_source():
    obs = call_legacy_realtime(
        lambda symbol: {
            "price": 10.0,
            "source": "daily_close_fallback",
            "_note": "legacy fallback",
        },
        "000001",
    )
    assert obs.symbol == "000001"
    assert obs.fallback is True
    assert obs.source == "daily_close_fallback"
    assert obs.warning == "legacy fallback"


@pytest.mark.parametrize(
    ("weather", "expected"),
    [
        ("SUNNY", "TREND_UP"),
        ("CLOUDY", "RANGE"),
        ("RAIN", "TREND_DOWN"),
        ("STORM", "RISK_OFF"),
        ("unknown", "UNKNOWN"),
    ],
)
def test_legacy_regime_mapping(weather, expected):
    assert legacy_regime_mapping(weather) == expected


def test_legacy_inventory_contains_high_risk_single_index_regime():
    assert "scripts/market_regime_check.py" in LEGACY_SCRIPT_ROLES
