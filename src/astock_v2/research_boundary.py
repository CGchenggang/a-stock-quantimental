"""Frozen research/virgin boundary — single source of truth.

research_end is the last decision date any research stage (P13-O through
P13-S) consumed; virgin_start is the first date reserved for a future
P13-T holdout. These values are frozen constants: they never follow the
latest data date and can only change through an auditable code change.

Every research entry point must fail fast on decision dates at or after
virgin_start via :func:`assert_research_zone`.
"""
from __future__ import annotations

RESEARCH_END = "2026-09-22"   # last OOS decision day consumed by P13-O..P13-S
VIRGIN_START = "2026-09-23"   # first day reserved for the P13-T holdout
MINIMUM_VIRGIN_TRADING_DAYS = 20   # one walk-forward test window
RECOMMENDED_VIRGIN_TRADING_DAYS = 60  # statistically meaningful window

CONTAMINATION_MESSAGE = "VIRGIN HOLDOUT DATA CANNOT BE CONSUMED BY RESEARCH PIPELINE"


def assert_research_zone(dates, virgin_start: str = VIRGIN_START) -> None:
    """Fail fast if any research input carries a virgin-zone decision date.

    Research pipelines (P13-O/P/Q/R analysis entry points and the P14
    information layer) call this on every decision_time they load. Virgin
    holdout rows may only be consumed by an explicit future P13-T
    evaluation, which must bypass this guard knowingly.
    """
    offending = sorted(str(d)[:10] for d in dates if str(d)[:10] >= virgin_start)
    if offending:
        shown = ", ".join(offending[:5]) + (" ..." if len(offending) > 5 else "")
        raise ValueError(
            f"{CONTAMINATION_MESSAGE}: decision dates >= {virgin_start} "
            f"received by a research pipeline: {shown}"
        )
