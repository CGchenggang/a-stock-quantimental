from astock_v2.orchestration import legacy_snapshot_to_research_packet


def test_legacy_snapshot_can_enter_research_context_without_model_invention():
    packet = legacy_snapshot_to_research_packet(
        {
            "generated_at": "2026-09-27T08:30:00+08:00",
            "data_quality": {"completeness": 0.8},
            "stocks": [{"ticker": "000001", "close": 10.1}],
        },
        decision_time="2026-09-27T08:30:00+08:00",
    )
    assert packet.symbol == "000001"
    assert packet.decision_time == "2026-09-27T00:30:00+00:00"
    assert packet.model == {}
    assert packet.factors == {}
    assert packet.risk["flags"] == ["LEGACY_COMPATIBILITY_INPUT"]
    assert packet.data_quality["realtime_admissible"] is False


def test_legacy_snapshot_does_not_create_fake_events():
    packet = legacy_snapshot_to_research_packet(
        {"stocks": [{"ticker": "000001"}], "data_quality": {"completeness": 1.0}},
        decision_time="2026-09-27T08:30:00+08:00",
    )
    assert packet.events == []
