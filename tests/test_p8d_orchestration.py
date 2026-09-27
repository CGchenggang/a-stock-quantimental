from astock_v2.orchestration import collect_legacy_outputs, legacy_snapshot_to_v2


def test_legacy_snapshot_requires_explicit_availability_for_realtime_use():
    result = legacy_snapshot_to_v2(
        {"generated_at": "2026-09-27T08:30:00+08:00"},
        source="legacy_morning_collector",
    )
    assert result["generated_at"] == "2026-09-27T00:30:00+00:00"
    assert result["available_time"] is None
    assert result["freshness_status"] == "UNKNOWN"
    assert result["realtime_admissible"] is False


def test_legacy_snapshot_preserves_payload_and_quality():
    snapshot = {
        "generated_at": "2026-09-27T08:30:00+08:00",
        "data_quality": {"completeness": 0.8, "cautions": ["fallback"]},
        "stocks": [{"ticker": "000001"}],
    }
    result = legacy_snapshot_to_v2(
        snapshot,
        source="legacy_pre_market_pipeline",
        available_time="2026-09-27T08:31:00+08:00",
    )
    assert result["payload"] == snapshot
    assert result["data_quality"]["completeness"] == 0.8
    assert result["available_time"] == "2026-09-27T00:31:00+00:00"
    assert result["realtime_admissible"] is False


def test_legacy_collectors_share_one_v2_boundary():
    result = collect_legacy_outputs(
        morning={"generated_at": "2026-09-27T08:30:00+08:00"},
        pre_market={"generated_at": "2026-09-27T08:35:00+08:00"},
        available_time="2026-09-27T08:36:00+08:00",
    )
    assert set(result["outputs"]) == {"morning", "pre_market"}
    assert result["legacy_fallback"] is True
    assert result["outputs"]["morning"]["source"] == "legacy_morning_collector"
    assert result["outputs"]["pre_market"]["source"] == "legacy_pre_market_pipeline"
