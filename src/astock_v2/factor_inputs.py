"""Point-in-time gate for provider-backed factor inputs.

This module is intentionally calculation-agnostic: it only admits provider
results that are usable at a factor decision time and reports rejected inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .data_quality import DataQualitySummary, summarize_pit
from .data.providers import PitStatus, ProviderResult, pit_status


@dataclass(frozen=True)
class FactorInputGateResult:
    """Admitted and rejected provider inputs for a factor calculation."""

    admitted: tuple[ProviderResult, ...]
    rejected: tuple[ProviderResult, ...]
    rejection_statuses: tuple[PitStatus, ...]
    quality: DataQualitySummary

    @property
    def ready(self) -> bool:
        """Return True only when every supplied provider result is admissible."""
        return self.quality.pit_admissible

    def as_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "admitted_count": len(self.admitted),
            "rejected_count": len(self.rejected),
            "rejection_statuses": [status.value for status in self.rejection_statuses],
            "data_quality": self.quality.as_dict(),
        }


def gate_factor_inputs(
    results: Iterable[ProviderResult],
    decision_time: str,
) -> FactorInputGateResult:
    """Separate PIT-admissible factor inputs from unusable observations.

    Rejected observations are retained for diagnostics but are never silently
    substituted, repaired, or converted into factor values.
    """
    items = tuple(results)
    statuses = tuple(pit_status(result, decision_time) for result in items)
    admitted = tuple(
        result for result, status in zip(items, statuses) if status is PitStatus.ADMISSIBLE
    )
    rejected = tuple(
        result for result, status in zip(items, statuses) if status is not PitStatus.ADMISSIBLE
    )
    rejected_statuses = tuple(
        status for status in statuses if status is not PitStatus.ADMISSIBLE
    )
    return FactorInputGateResult(
        admitted=admitted,
        rejected=rejected,
        rejection_statuses=rejected_statuses,
        quality=summarize_pit(items, decision_time),
    )
