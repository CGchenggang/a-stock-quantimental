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
from .raw_store import RawStore, to_information_record
from .registry import (
    FRESHNESS_POLICIES,
    SOURCE_REGISTRY,
    SourceCategory,
    SourceSpec,
    is_registered,
    spec_for,
)
from astock_v2.research_boundary import RESEARCH_END, VIRGIN_START, assert_research_zone
from .quality import (
    PIT_ADMISSIBLE, PIT_REJECTED,
    AVAILABLE_TIME_MISSING, AVAILABLE_TIME_AFTER_DECISION,
    QUALITY_ADMISSIBLE, QUALITY_WITH_WARNING, QUALITY_REJECTED,
    QUALITY_UNRESOLVED,
    MISSINGNESS_VOCABULARY,
    classify_missingness, freshness_quality, pit_quality,
    record_quality_decision, revision_integrity_issues, timestamp_issues,
)
from .reconciliation import (
    DEFAULT_POLICY, ReconciliationPolicy, reconcile, reconcile_pair,
)
from .expected_contract import (
    ExpectedContract, build_expected_contracts,
)
from .evidence import (
    BUNDLE_SCHEMA_VERSION,
    create_bundle,
    freeze_bundle,
    validate_bundle,
)
from .evidence_store import EvidenceStore
from .research_query import (
    EXCLUSION_NOT_YET_AVAILABLE, EXCLUSION_OUTSIDE_AS_OF,
    EXCLUSION_UNRESOLVED_AVAILABILITY, PROVENANCE_FIELDS,
    ResearchQuery, run_query,
)
from .source_health import source_health
from .research_boundary_guard import select_asof

__all__ = [
    "CONFLICT", "FRESH", "MISSING_POLICY", "STALE", "UNKNOWN",
    "QUALITY_INVALID", "QUALITY_OK", "QUALITY_STATUSES", "QUALITY_UNRESOLVED",
    "REQUIRED_FIELDS", "SCHEMA_VERSION",
    "FreshnessPolicy", "RawInformationRecord", "ResearchInformationRecord",
"SourceCategory", "SourceSpec",
    "RESEARCH_END", "VIRGIN_START",
    "admissible_records", "annotate_conflict_status", "assert_research_zone",
    "RawStore", "dedup_key", "deduplicate", "detect_conflicts",
    "to_information_record",
    "freshness_status", "freshness_summary", "has_valid_provenance",
    "is_admissible", "is_registered", "normalize", "parse_boundary",
    "ExpectedContract", "build_expected_contracts",
    "ResearchQuery", "run_query", "PROVENANCE_FIELDS",
    "create_bundle", "freeze_bundle", "validate_bundle", "EvidenceStore",
    "BUNDLE_SCHEMA_VERSION",
    "EXCLUSION_NOT_YET_AVAILABLE", "EXCLUSION_OUTSIDE_AS_OF",
    "EXCLUSION_UNRESOLVED_AVAILABILITY",
    "provenance_issues", "provenance_summary", "select_asof",
    "spec_for", "to_research_record", "visible_revisions",
]
