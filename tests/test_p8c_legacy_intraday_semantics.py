"""Explicit regression contract for the legacy intraday detector."""
from __future__ import annotations

from scripts.intraday_reversal_detector import detect


def test_intraday_detector_treats_northbound_as_proxy_only():
    result = detect(
        intraday={
            "northbound_chg": True,
            "vwap_break": True,
        }
    )
    assert result["item_scores"]["northbound_proxy"] == 1
    assert "northbound_proxy" not in result.get("confirmed_facts", [])


def test_intraday_detector_requires_explicit_minute_snapshot_contract():
    # The detector consumes an intraday snapshot, but it does not itself prove
    # that the snapshot is minute-granular. V2 must carry timestamp metadata.
    result = detect(intraday={"vwap_break": True})
    assert result["item_scores"]["vwap_breakout"] == 1
    # Every one of the eight v3.86 items without data is noted in ITEMS order,
    # including the prev_state-derived extreme_sentiment_yesterday.
    assert result["notes"] == [
        "extreme_sentiment_yesterday:数据缺失按0分",
        "low_open_volume_shrink:数据缺失按0分",
        "decline_narrowing:数据缺失按0分",
        "weights_stable:数据缺失按0分",
        "etf_volume_surge:数据缺失按0分",
        "northbound_proxy:数据缺失按0分",
        "bottom_divergence:数据缺失按0分",
    ]
