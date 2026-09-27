from astock_v2.data.legacy_provider import provider_result_from_legacy_payload


def test_legacy_provider_preserves_fallback_and_provenance():
    result = provider_result_from_legacy_payload({
        "source": "prev_close_fallback",
        "fetched_at": "2026-09-26T10:00:00+00:00",
        "_note": "used previous close",
        "price": 10.0,
    })
    assert result.source == "prev_close_fallback"
    assert result.source_type == "legacy_adapter"
    assert result.fallback is True
    assert result.available_time == "2026-09-26T10:00:00+00:00"
    assert result.warnings == ["used previous close"]


def test_legacy_provider_requires_timestamp():
    try:
        provider_result_from_legacy_payload({"source": "sina_spot"})
    except ValueError as exc:
        assert "fetched_at" in str(exc)
    else:
        raise AssertionError("missing timestamp must be rejected")
