from astock_v2.data.freshness import classify_legacy_payload, freshness_age_seconds


def test_fallback_is_never_realtime_admissible():
    result = classify_legacy_payload(
        {
            "source": "prev_close_fallback",
            "fetched_at": "2026-09-26T10:00:00+00:00",
            "fallback": True,
        },
        now="2026-09-26T10:00:10+00:00",
    )
    assert result["status"] == "FALLBACK"
    assert result["is_realtime_admissible"] is False


def test_ttl_classification():
    result = classify_legacy_payload(
        {
            "source": "sina_spot",
            "fetched_at": "2026-09-26T09:00:00+00:00",
        },
        now="2026-09-26T09:06:00+00:00",
        realtime_ttl_seconds=300,
    )
    assert result["status"] == "STALE"
    assert result["is_realtime_admissible"] is False


def test_fresh_payload():
    result = classify_legacy_payload(
        {
            "source": "sina_spot",
            "fetched_at": "2026-09-26T09:00:00+00:00",
        },
        now="2026-09-26T09:03:00+00:00",
        realtime_ttl_seconds=300,
    )
    assert result["status"] == "FRESH"
    assert result["is_realtime_admissible"] is True
    assert freshness_age_seconds(
        "2026-09-26T09:00:00+00:00",
        "2026-09-26T09:03:00+00:00",
    ) == 180.0
