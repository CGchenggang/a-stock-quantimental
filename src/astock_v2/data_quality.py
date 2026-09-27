"""Point-in-time data-quality helpers shared by provider-backed pipelines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .data.providers import PitStatus, ProviderResult, pit_status


@dataclass(frozen=True)
class DataQualitySummary:
    """Structured PIT quality summary for a set of provider results."""

    total: int
    admissible: int
    status_counts: dict[str, int]
    admissible_ratio: float
    pit_admissible: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "provider_results": self.total,
            "pit_admissible_ratio": self.admissible_ratio,
            "pit_status_counts": dict(self.status_counts),
            "pit_admissible": self.pit_admissible,
        }


def summarize_pit(results: Iterable[ProviderResult], decision_time: str) -> DataQualitySummary:
    """Summarize provider PIT status without changing or fabricating source data."""
    items = list(results)
    statuses = [pit_status(result, decision_time) for result in items]
    counts = {status.value: statuses.count(status) for status in PitStatus}
    admissible = counts[PitStatus.ADMISSIBLE.value]
    total = len(items)
    return DataQualitySummary(
        total=total,
        admissible=admissible,
        status_counts=counts,
        admissible_ratio=admissible / total if total else 0.0,
        pit_admissible=bool(total) and admissible == total,
    )
