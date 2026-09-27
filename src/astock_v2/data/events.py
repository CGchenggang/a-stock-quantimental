"""Structured policy/event inputs; no subjective political scoring."""
from __future__ import annotations
from dataclasses import dataclass


ALLOWED_EVENT_TYPES = frozenset({
    "monetary_policy", "fiscal_policy", "industry_policy",
    "regulation", "trade_policy", "capital_market_rule",
    "geopolitical", "macro_release", "company_event", "other",
})


@dataclass(frozen=True)
class PolicyEvent:
    event_id: str
    event_time: str
    available_time: str | None
    source: str
    event_type: str
    title: str
    affected_assets: tuple[str, ...] = ()
    affected_sectors: tuple[str, ...] = ()
    evidence_level: str = "UNVERIFIED"

    def __post_init__(self) -> None:
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"unsupported event_type: {self.event_type}")
        if not self.event_id or not self.source or not self.title:
            raise ValueError("event_id, source and title are required")
        if self.event_type == "geopolitical" and self.evidence_level == "UNVERIFIED":
            raise ValueError("geopolitical events require an explicit evidence level")

    @property
    def quantitative_direction(self) -> None:
        """Intentionally unavailable: direction must be derived by a quant model."""
        return None
