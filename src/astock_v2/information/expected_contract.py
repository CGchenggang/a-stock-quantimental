"""P14-C §8/§9/§16.4: Expected Contract — the frozen a-priori completeness
universe (production implementation).

Contract §8.2 structure::

    EXPECTED_CONTRACT[source_id] = {
        "expected_entities": [str, ...],
        "expected_dates": [str, ...],
        "expected_absence_pairs": [[entity_id, date], ...],   # optional
    }

Frozen §8.3 semantics enforced here:

- ``expected_absence_pairs`` is the SOLE authoritative EXPECTED_ABSENCE
  declaration channel. Boolean switches (a bare ``expected_absence`` key)
  and the fixture-control fields (``expected_empty`` / ``broken_source`` /
  ``force_source_error`` / ``fixture_mode``) are structurally invalid and
  rejected fail-fast — production code never interprets them.
- every declared pair must lie in E x D (X ⊆ P); an out-of-scope
  declaration is a contract structure error.
- required pairs R = P - X; completeness counts only R (§9.2):
  expected_count = |R|, actual_count = |A_pair ∩ R|,
  coverage = actual/expected (1.0 when |R| == 0).
- declaration provenance is Type C (§16.4): source_id, expected_contract_id,
  entity_date_pair_scope, declaration_reference. Observation-only fields
  (observed_at / adapter_version / ingestion_id / available_time /
  ingested_at / raw_payload_hash) never exist on a declaration.

Deterministic: all outputs use explicitly sorted canonical ordering; no
runtime timestamp, UUID, or environment value enters any result.
"""
from __future__ import annotations

CANONICAL_ABSENCE_FIELD = "expected_absence_pairs"
CONTRACT_CONTROL_FIELDS = (
    "expected_empty",
    "broken_source",
    "force_source_error",
    "fixture_mode",
)
BANNED_ABSENCE_CONTROL_KEY = "expected_absence"

CONTRACT_VERSION = "p14c-expected-contract-1"

# Source-level missingness classes (Contract §7.1). A source with no missing
# observation has class NONE: EXPECTED_ABSENCE is a declaration about pairs,
# never a label for "everything is fine".
CLASS_NONE = "NONE"
CLASS_EXPECTED_ABSENCE = "EXPECTED_ABSENCE"
CLASS_UNEXPECTED_MISSING = "UNEXPECTED_MISSING"


class ExpectedContract:
    """Validated, frozen view of one source's EXPECTED_CONTRACT entry."""

    def __init__(self, source_id: str, entry: dict):
        if not isinstance(entry, dict):
            raise ValueError(f"expected contract entry for {source_id!r} must be a mapping")
        for field in CONTRACT_CONTROL_FIELDS:
            if field in entry:
                raise ValueError(
                    f"expected contract for {source_id!r} contains forbidden "
                    f"fixture-control field {field!r} (Contract §8.3 rule 1)")
        if BANNED_ABSENCE_CONTROL_KEY in entry:
            raise ValueError(
                f"expected contract for {source_id!r} uses the banned boolean "
                f"control key {BANNED_ABSENCE_CONTROL_KEY!r}; the sole "
                f"authoritative declaration channel is "
                f"{CANONICAL_ABSENCE_FIELD!r} (Contract §8.3 rule 1)")
        self.source_id = source_id
        self.entities = sorted(str(e) for e in entry.get("expected_entities", []))
        self.dates = sorted(str(d) for d in entry.get("expected_dates", []))
        declared = entry.get(CANONICAL_ABSENCE_FIELD, [])
        self.absence_pairs = sorted((str(e), str(d)) for e, d in declared)
        self.pairs = {(e, d) for e in self.entities for d in self.dates}
        # §8.3 rule 3: X ⊆ P, out-of-scope declaration fails fast.
        out_of_scope = sorted(set(self.absence_pairs) - self.pairs)
        if out_of_scope:
            raise ValueError(
                f"expected contract for {source_id!r} declares absence pairs "
                f"outside E x D: {out_of_scope}")
        self.required_pairs = self.pairs - set(self.absence_pairs)

    # -------------------------------------------------- §9.2 completeness

    def completeness(self, actual_pairs) -> dict:
        """§9.2 arithmetic on R; every list canonically sorted (JSON-friendly
        lists, not tuples).

        Satisfaction is measured ONLY by ``A_pair ∩ R`` — an actual pair
        outside P can never satisfy a required entity/date — and
        ``missing_entities`` / ``missing_dates`` are derived from the
        REQUIRED universe (entities/dates participating in R, satisfied by
        A_pair ∩ R), so declared absences never enter any ``missing_*``
        set (Contract §9.2 note; P14-C-COMP-BLOCKER-001 repair).
        """
        actual = {(str(e), str(d)) for e, d in actual_pairs}
        required = self.required_pairs
        satisfied = actual & required
        missing_entities = sorted(
            {e for e, _ in required} - {e for e, _ in satisfied})
        missing_dates = sorted(
            {d for _, d in required} - {d for _, d in satisfied})
        missing_pairs = sorted(required - satisfied)
        expected_count = len(required)
        actual_count = len(satisfied)
        coverage = (actual_count / expected_count) if expected_count else 1.0
        return {
            "expected_entities": self.entities,
            "actual_entities": sorted({e for e, _ in actual}),
            "missing_entities": missing_entities,
            "expected_dates": self.dates,
            "actual_dates": sorted({d for _, d in actual}),
            "missing_dates": missing_dates,
            "expected_pairs": [list(p) for p in sorted(self.pairs)],
            "required_expected_pairs": [list(p) for p in sorted(required)],
            "expected_absence_pairs": [list(p) for p in sorted(self.absence_pairs)],
            "missing_pairs": [list(p) for p in missing_pairs],
            "expected_count": expected_count,
            "actual_count": actual_count,
            "coverage_ratio": round(coverage, 4),
        }

    # --------------------------------------------- §7.1 pair classification

    def classify_pairs(self, actual_pairs) -> dict[tuple[str, str], str]:
        """Pair-level classification over E x D (frozen semantics):
        observed -> OBSERVED; declared absence -> EXPECTED_ABSENCE;
        required but absent -> UNEXPECTED_MISSING."""
        actual = {(str(e), str(d)) for e, d in actual_pairs}
        out: dict[tuple[str, str], str] = {}
        for pair in sorted(self.pairs):
            if pair in actual:
                out[pair] = "OBSERVED"
            elif pair in self.absence_pairs:
                out[pair] = CLASS_EXPECTED_ABSENCE
            else:
                out[pair] = CLASS_UNEXPECTED_MISSING
        return out

    def source_missingness_class(self, actual_pairs) -> str:
        """Source-level class over required observations (§7.1). The
        observation-evidence classes (SOURCE_EMPTY / SOURCE_ERROR /
        PARSE_FAILURE) take precedence and are applied by the audit runner;
        this method only decides the contract-derived remainder, driven by
        the PAIR-level required set (an entity/date granularity gap that
        consists solely of declared-absent pairs is EXPECTED_ABSENCE
        evidence, never UNEXPECTED_MISSING)."""
        comp = self.completeness(actual_pairs)
        if comp["missing_pairs"]:
            return CLASS_UNEXPECTED_MISSING
        actual = {(str(e), str(d)) for e, d in actual_pairs}
        unobserved_absence = sorted(set(self.absence_pairs) - actual)
        if unobserved_absence:
            return CLASS_EXPECTED_ABSENCE
        return CLASS_NONE

    # ------------------------------------------- §16.4 Type C provenance

    def declaration_provenance(self) -> list[dict]:
        """Type C Contract Declaration Provenance for every declared
        absence pair. Deliberately EXCLUDES observation-only fields."""
        return [
            {
                "source_id": self.source_id,
                "expected_contract_id": CONTRACT_VERSION,
                "entity_date_pair_scope": {"entity_id": e, "date": d},
                "declaration_reference": (
                    f"EXPECTED_CONTRACT[{self.source_id!r}]."
                    f"{CANONICAL_ABSENCE_FIELD}[{i}]"
                ),
            }
            for i, (e, d) in enumerate(sorted(self.absence_pairs))
        ]


def build_expected_contracts(contract: dict) -> dict[str, ExpectedContract]:
    """Parse a full EXPECTED_CONTRACT mapping; each source appears at most
    once by mapping semantics (§8 invariant EXP-003)."""
    return {source: ExpectedContract(source, entry)
            for source, entry in contract.items()}
