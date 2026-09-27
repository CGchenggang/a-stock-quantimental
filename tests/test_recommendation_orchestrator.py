from astock_v2.agent.orchestrator import ResearchOrchestrator, ResearchPacket

def test_research_packet_can_create_ledger_record():
    packet=ResearchPacket(
        "000001","2026-01-01T09:30:00+00:00",{},{"supporting_evidence":["trend"],"contradictory_evidence":[]},
        {},[],{"calibration_status":"CALIBRATED","p_up":{5:.72},"confidence":.8,"provenance":["model:m1"]},{},{"score":.95,"pit_admissible":True})
    record=ResearchOrchestrator().recommendation_record(packet,record_id="r1",model_version="m1")
    assert record.symbol=="000001"
    assert record.probability==.72
    assert record.action=="HOLD"
    assert record.provenance==("model:m1",)
