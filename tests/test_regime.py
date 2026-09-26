import pytest

from astock_v2.regime import classify_regime


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (
            {
                "index_trend": 2.0,
                "breadth": 0.8,
                "turnover_z": 1.0,
                "volatility_z": 0.0,
                "sector_dispersion": 0.4,
                "limit_pressure": 0.2,
                "liquidity": 1.0,
            },
            "TREND_UP",
        ),
        (
            {
                "index_trend": -2.0,
                "breadth": -0.8,
                "turnover_z": 0.0,
                "volatility_z": 0.0,
                "sector_dispersion": 0.3,
                "limit_pressure": 0.0,
                "liquidity": 0.0,
            },
            "TREND_DOWN",
        ),
        (
            {
                "index_trend": 0.0,
                "breadth": 0.0,
                "turnover_z": 0.0,
                "volatility_z": 2.5,
                "sector_dispersion": 1.0,
                "limit_pressure": 0.0,
                "liquidity": 0.0,
            },
            "HIGH_VOL",
        ),
    ],
)
def test_multi_input_regime(values, expected):
    assert classify_regime(values)["regime"] == expected


def test_regime_unknown_when_most_inputs_missing():
    assert classify_regime({"index_trend": 1.0})["regime"] == "UNKNOWN"


def test_regime_confidence_reflects_missing_inputs():
    result = classify_regime(
        {"index_trend": 1.0, "breadth": 0.5, "volatility_z": 0.0}
    )
    assert result["confidence"] == pytest.approx(3 / 7)
