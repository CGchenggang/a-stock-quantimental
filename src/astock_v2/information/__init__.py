"""P14-A unified information contract: raw -> provenance -> normalized ->
PIT -> freshness -> dedup -> conflict -> research information records.

P13-R decides; P13-S explains; the information layer only answers "what
could a researcher know at a given decision time?" — via available_time,
never event_time.
"""
from .conflict import CONFLICT, annotate_conflict_status, detect_conflicts
from .dedup import dedup_key, deduplicate
from .freshness import (
    FRESH,
    MISSING_POLICY,
    STALE,
    UNKNOWN,
    FreshnessPolicy,
    freshness_status,
    freshness_summary,
)
from .models import (
    SCHEMA_VERSION,
    QUALITY_INVALID,
    QUALITY_OK,
    QUALITY_STATUSES,
    QUALITY_UNRESOLVED,
    REQUIRED_FIELDS,
    RawInformationRecord,
    ResearchInformationRecord,
    SCHEMA_VERSION,
    parse_boundary,
)
from .normalization import normalize
from .pit import (
    admissible_records,
    is_admissible,
    visible_revisions,
)
from .provenance import (
    has_valid_provenance,
    provenance_issues,
    provenance_summary,
    to_research_record,
)
from .registry import (
    FRESHNESS_POLICIES,
    SOURCE_REGISTRY,
    SourceCategory,
    SourceSpec,
    is_registered,
    spec_for,
)
from astock_v2.research_boundary import RESEARCH_END, VIRGIN_START, assert_research_zone
from .research_boundary_guard import select_asof

__all__ = [
    "CONFLICT", "FRESH", "MISSING_POLICY", "STALE", "UNKNOWN",
    "QUALITY_INVALID", "QUALITY_OK", "QUALITY_STATUSES", "QUALITY_UNRESOLVED",
    "REQUIRED_FIELDS", "SCHEMA_VERSION",
    "FreshnessPolicy", "RawInformationRecord", "ResearchInformationRecord",
"SourceCategory", "SourceSpec",
    "RESEARCH_END", "VIRGIN_START",
    "admissible_records", "annotate_conflict_status", "assert_research_zone",
    "dedup_key", "deduplicate", "detect_conflicts",
    "freshness_status", "freshness_summary", "has_valid_provenance",
    "is_admissible", "is_registered", "normalize", "parse_boundary",
    "provenance_issues", "provenance_summary", "select_asof",
    "spec_for", "to_research_record", "visible_revisions",
]
