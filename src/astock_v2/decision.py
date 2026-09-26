from .types import DecisionPacket
from .risk.engine import RiskEngine

def build_decision(packet: DecisionPacket, risk: RiskEngine):
    rr = risk.evaluate(packet.data_quality, packet.expected_volatility,
                        packet.expected_drawdown, liquidity_ok=True)
    packet.risk_flags.extend(rr.flags)
    if not rr.allowed:
        packet.decision_class = "NO_ACTION"
    elif packet.data_quality >= 0.90 and packet.p_up.get(5, 0.5) >= 0.60:
        packet.decision_class = "PAPER_TEST"
    else:
        packet.decision_class = "RESEARCH"
    return packet
