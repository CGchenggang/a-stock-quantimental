from astock_v2.data.pit_adapter import daily_latest_cached_to_datapoint

def test_cached_daily_uses_persisted_cache_time():
    point=daily_latest_cached_to_datapoint({
        "saved_at_unix":1790419200.0,
        "data":{
            "code":"000001",
            "latest_date":"2026-09-25",
            "latest":{"close":10.1},
        },
    })
    assert point.available_time=="2026-09-26T00:00:00+00:00"
    assert point.event_time=="2026-09-25T00:00:00+00:00"

def test_cached_daily_requires_persisted_timestamp():
    try:
        daily_latest_cached_to_datapoint({"data":{
            "code":"000001","latest_date":"2026-09-25","latest":{"close":10.1}
        }})
    except ValueError as exc:
        assert "saved_at_unix" in str(exc)
    else:
        raise AssertionError("missing cache timestamp must be rejected")
