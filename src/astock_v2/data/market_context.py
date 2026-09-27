"""Cross-market context contract.

Only structured, timestamped observations enter this layer.  AI agents may
describe these observations later, but must not mutate the quantitative values.
"""
from __future__ import annotations
from dataclasses import dataclass
from .catalog import HistoricalRecord


@dataclass(frozen=True)
class MarketContext:
    decision_time: str
    cn: tuple[HistoricalRecord, ...] = ()
    overseas: tuple[HistoricalRecord, ...] = ()
    macro: tuple[HistoricalRecord, ...] = ()
    policy_events: tuple[HistoricalRecord, ...] = ()

    def admissible_records(self) -> tuple[HistoricalRecord, ...]:
        records = self.cn + self.overseas + self.macro + self.policy_events
        return tuple(r for r in records if r.admissible_at(self.decision_time))

    def excluded_records(self) -> tuple[HistoricalRecord, ...]:
        records = self.cn + self.overseas + self.macro + self.policy_events
        return tuple(r for r in records if not r.admissible_at(self.decision_time))

    @property
    def pit_admissible(self) -> bool:
        records = self.cn + self.overseas + self.macro + self.policy_events
        return bool(records) and len(self.excluded_records()) == 0
