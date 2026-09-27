import pytest

from astock_v2.data.legacy_provider import provider_result_from_legacy_payload
from astock_v2.data.pit_adapter import daily_latest_to_datapoint, minute_klines_to_datapoints


def test_v1_realtime_fallback_semantics_are_preserved():
    payload={
        "source":"prev_close_fallback",
        "fetched_at":"2026-09-26T10:00:00+00:00",
        "price":10.0,
        "_note":"previous close",
    }
    result=provider_result_from_legacy_payload(payload)
    assert result.fallback is True
    assert result.source=="prev_close_fallback"
    assert result.source_type=="legacy_adapter"


def test_v1_daily_and_v2_pit_share_event_identity():
    payload={
        "code":"000001",
        "latest_date":"2026-09-25",
        "latest":{"close":10.1,"volume":1000},
    }
    point=daily_latest_to_datapoint(
        payload,
        available_time="2026-09-26T08:00:00+08:00",
    )
    assert point.symbol==payload["code"]
    assert point.event_time=="2026-09-25T00:00:00+00:00"
    assert point.value==payload["latest"]


def test_v1_minute_shape_maps_without_loss_of_ohlcv_fields():
    payload={
        "code":"000001",
        "scale":5,
        "klines":[{
            "time":"2026-09-25T14:55:00+08:00",
            "open":10.0,"high":10.2,"low":9.9,"close":10.1,"volume":1000,
        }],
    }
    points=minute_klines_to_datapoints(
        payload,
        fetched_at="2026-09-25T15:01:00+08:00",
    )
    value=points[0].value
    assert value["scale"]==5
    assert {k:value[k] for k in ("open","high","low","close","volume")}=={
        "open":10.0,"high":10.2,"low":9.9,"close":10.1,"volume":1000,
    }


def test_v1_missing_timestamp_cannot_enter_v2_provider_contract():
    with pytest.raises(ValueError, match="fetched_at"):
        provider_result_from_legacy_payload({
            "source":"sina_spot",
            "price":10.0,
        })
