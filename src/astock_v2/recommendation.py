"""Auditable recommendation ledger primitives."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class RecommendationRecord:
    record_id: str
    symbol: str
    decision_time: str
    action: str
    probability: float | None
    confidence: float | None
    rationale: str
    model_version: str
    data_quality: Mapping[str, object]
    provenance: tuple[str,...] = ()
    review_status: str = "OPEN"

    def __post_init__(self):
        if self.action not in {"BUY","HOLD","SELL","NO_ACTION"}: raise ValueError("invalid action")
        for name in ("probability","confidence"):
            value=getattr(self,name)
            if value is not None and not 0 <= value <= 1: raise ValueError(f"{name} must be in [0,1]")
        if not self.record_id or not self.symbol or not self.decision_time: raise ValueError("identity fields are required")

    def as_dict(self):
        return {"record_id":self.record_id,"symbol":self.symbol,"decision_time":self.decision_time,
                "action":self.action,"probability":self.probability,"confidence":self.confidence,
                "rationale":self.rationale,"model_version":self.model_version,
                "data_quality":dict(self.data_quality),"provenance":list(self.provenance),
                "review_status":self.review_status}

@dataclass(frozen=True)
class LedgerReview:
    record_id: str
    review_time: str
    realized_return: float | None
    outcome: str
    notes: str = ""

def close_review(record: RecommendationRecord, review: LedgerReview) -> RecommendationRecord:
    if review.record_id != record.record_id: raise ValueError("review record_id mismatch")
    if review.outcome not in {"CORRECT","INCORRECT","UNRESOLVED"}: raise ValueError("invalid outcome")
    return RecommendationRecord(record.record_id,record.symbol,record.decision_time,record.action,
        record.probability,record.confidence,record.rationale,record.model_version,record.data_quality,
        record.provenance,review.outcome)
