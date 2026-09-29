"""Virgin-holdout-aware selection for the P14 information layer.

The information layer answers "what could a researcher know at decision
time T?" — therefore any selection request with T inside the virgin zone
(>= VIRGIN_START) must fail fast exactly like the P13-Q/P13-R research
entry points. There is no separate, weaker path for this layer.
"""
from __future__ import annotations

from typing import Iterable, Sequence

from astock_v2.research_boundary import assert_research_zone

from .dedup import deduplicate
from .models import RawInformationRecord
from .pit import admissible_records


def select_asof(
    records: Sequence[RawInformationRecord], decision_time: str
) -> list[RawInformationRecord]:
    """Admissible, deduplicated records visible at decision_time.

    Shares the P13-U virgin-holdout guard: a decision_time at or after
    VIRGIN_START (2026-09-23) raises instead of silently consuming holdout
    data.
    """
    assert_research_zone([decision_time])
    return deduplicate(admissible_records(records, decision_time))
