"""Source category registry and per-source policies.

Every source in the information layer must be registered here before its
records can be normalized into research records. The registry defines, per
source: its category, the freshness policy it follows, its revision policy
and its provenance requirements. Unregistered sources are rejected by
normalization (``unregistered_source``) — no unknown-origin data reaches
the research layer.

Only a small set of representative fixture sources is defined in P14-A;
real adapters come later and must register here first.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .freshness import FreshnessPolicy


class SourceCategory(str, Enum):
    A_SHARE_MARKET = "A_SHARE_MARKET"
    COMPANY = "COMPANY"
    MACRO = "MACRO"
    OVERSEAS_MARKET = "OVERSEAS_MARKET"
    INDUSTRY = "INDUSTRY"
    MARKET_STATE = "MARKET_STATE"
    PUBLIC_EVENT = "PUBLIC_EVENT"


SECOND = 1.0
MINUTE = 60.0 * SECOND
HOUR = 60.0 * MINUTE
DAY = 24.0 * HOUR

FRESHNESS_POLICIES: dict[str, FreshnessPolicy] = {
    "market_daily": FreshnessPolicy(
        "market_daily", 16 * HOUR, "daily market data, available after the close"),
    "announcement_72h": FreshnessPolicy(
        "announcement_72h", 72 * HOUR, "company announcements"),
    "macro_release_35d": FreshnessPolicy(
        "macro_release_35d", 35 * DAY, "monthly macro releases"),
    "overseas_daily": FreshnessPolicy(
        "overseas_daily", 20 * HOUR, "overseas daily market data"),
    "industry_quarterly": FreshnessPolicy(
        "industry_quarterly", 100 * DAY, "industry classification / quarterly data"),
    "event_7d": FreshnessPolicy(
        "event_7d", 7 * DAY, "public events"),
}


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    source_category: SourceCategory
    freshness_policy_id: str
    revision_policy: str = "monotone_append_only"
    provenance_required: tuple[str, ...] = ("source", "source_id", "ingested_at")
    quality_policy: str = "reject_unresolved"


SOURCE_REGISTRY: dict[str, SourceSpec] = {
    spec.source_id: spec
    for spec in (
        SourceSpec("cn_index_daily", SourceCategory.A_SHARE_MARKET, "market_daily"),
        SourceSpec("cn_stock_quote", SourceCategory.A_SHARE_MARKET, "market_daily"),
        SourceSpec("company_announcement", SourceCategory.COMPANY, "announcement_72h"),
        SourceSpec("macro_pmi_cn", SourceCategory.MACRO, "macro_release_35d"),
        SourceSpec("macro_cpi_cn", SourceCategory.MACRO, "macro_release_35d"),
        SourceSpec("us_index_daily", SourceCategory.OVERSEAS_MARKET, "overseas_daily"),
        SourceSpec("industry_classification", SourceCategory.INDUSTRY, "industry_quarterly"),
        SourceSpec("market_state_feed", SourceCategory.MARKET_STATE, "market_daily"),
        SourceSpec("public_event_feed", SourceCategory.PUBLIC_EVENT, "event_7d"),
    )
}


def is_registered(source_id: str) -> bool:
    return source_id in SOURCE_REGISTRY


def spec_for(source_id: str) -> SourceSpec | None:
    return SOURCE_REGISTRY.get(source_id)
