from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class ResearchPacket:
    symbol: str
    decision_time: str
    market: dict[str,Any]
    stock: dict[str,Any]
    factors: dict[str,Any]
    events: list[dict[str,Any]]
    model: dict[str,Any]
    risk: dict[str,Any]
    data_quality: dict[str,Any]

class ResearchOrchestrator:
    """Build evidence packets without changing quantitative outputs."""

    ORDER=("data-health","market-snapshot","stock-research","event-research","decision-review")

    def build(self, **kwargs)->ResearchPacket:
        return ResearchPacket(**kwargs)

    def build_from_provider(self, provider, **kwargs) -> ResearchPacket:
        from ..provider_research import build_research_packet_from_provider
        return build_research_packet_from_provider(provider, **kwargs)

    def as_json(self, packet: ResearchPacket)->dict[str,Any]:
        return asdict(packet)

    def recommendation_record(self, packet: ResearchPacket, *, record_id: str, model_version: str):
        from ..recommendation import RecommendationRecord
        state=self.research_state(packet)
        action={"PAPER_TEST":"HOLD","RESEARCH":"NO_ACTION","NO_ACTION":"NO_ACTION"}.get(state["decision_class"],"NO_ACTION")
        p5=packet.model.get("p_up",{}).get(5)
        confidence=packet.model.get("confidence")
        rationale="; ".join(state["supporting_evidence"] + state["contradictory_evidence"]) or "quantitative evidence packet"
        return RecommendationRecord(record_id,packet.symbol,packet.decision_time,action,p5,confidence,rationale,model_version,packet.data_quality,tuple(packet.model.get("provenance",())))

    def research_state(self, packet: ResearchPacket)->dict[str,Any]:
        quality=float(packet.data_quality.get("score",0.0))
        # R4-D integration point (R4D-014): when the packet carries the
        # authorized probability block and it is CALIBRATED, the frozen
        # policy threshold (threshold_platt_p50) decides PAPER_TEST;
        # legacy packets keep the previous scaffold behavior unchanged.
        r4d=packet.model.get("r4d") or {}
        if r4d.get("probability_status")=="CALIBRATED":
            calibrated=True
            p5=float(r4d["probability"])
            threshold=float(r4d.get("probability_threshold",0.5))
        else:
            calibrated=packet.model.get("calibration_status")=="CALIBRATED"
            p5=packet.model.get("p_up",{}).get(5,0.5)
            threshold=0.60
        if quality<0.75: decision="NO_ACTION"
        elif calibrated and p5>=threshold: decision="PAPER_TEST"
        else: decision="RESEARCH"
        return {"symbol":packet.symbol,"decision_time":packet.decision_time,
                "decision_class":decision,"model_output":packet.model.copy(),
                "supporting_evidence":packet.stock.get("supporting_evidence",[]),
                "contradictory_evidence":packet.stock.get("contradictory_evidence",[]),
                "missing_evidence":packet.stock.get("missing_evidence",[]),
                "risk_flags":packet.risk.get("flags",[])}
