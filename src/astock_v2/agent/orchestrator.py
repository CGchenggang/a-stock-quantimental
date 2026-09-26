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

    def as_json(self, packet: ResearchPacket)->dict[str,Any]:
        return asdict(packet)

    def research_state(self, packet: ResearchPacket)->dict[str,Any]:
        quality=float(packet.data_quality.get("score",0.0))
        calibrated=packet.model.get("calibration_status")=="CALIBRATED"
        p5=packet.model.get("p_up",{}).get(5,0.5)
        if quality<0.75: decision="NO_ACTION"
        elif calibrated and p5>=0.60: decision="PAPER_TEST"
        else: decision="RESEARCH"
        return {"symbol":packet.symbol,"decision_time":packet.decision_time,
                "decision_class":decision,"model_output":packet.model.copy(),
                "supporting_evidence":packet.stock.get("supporting_evidence",[]),
                "contradictory_evidence":packet.stock.get("contradictory_evidence",[]),
                "missing_evidence":packet.stock.get("missing_evidence",[]),
                "risk_flags":packet.risk.get("flags",[])}
