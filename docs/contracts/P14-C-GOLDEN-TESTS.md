# P14-C Golden Tests — Coverage Matrix (Frozen)

> Standard answers for the future P14-C production implementation.
> Workflow: Design Contract → Acceptance Harness (PASS) → **Golden Tests (this doc + fixtures)** → Independent Acceptance → Implementation.
> Status: implementation complete — awaiting independent acceptance.

Facts: 64 golden fixtures, covering all 61 canonical Contract IDs in the frozen
Acceptance Matrix (PIT-GOOD/PIT-BAD additionally exercise P14-A PIT authority;
G-TS-005 extends TS-001 with malformed/future-timestamp cases).
Expected values are hand-written literals inside each fixture JSON — never derived
from an implementation. Validation engine: `tests/contracts/p14c/golden/core.py`
(338 mechanical checks, deterministic report byte-identical across reruns).

## Interpretation notes (no contract modification)

- **Intentional absence declaration**: the contract requires EXPECTED_ABSENCE to be
  *declared by contract* (P14C-MISS-004) but its §8.2 structure has no field for it.
  Golden fixtures declare it positively as `intentional_absence_pairs` inside the
  expected-contract entry — an a-priori, payload-independent pair declaration.
  The banned boolean/control styles (`expected_absence=True`, `expected_empty`,
  `broken_source`, `force_source_error`, `fixture_mode`) never appear
  (mechanically enforced by the anti-cheat scan). Not a CONTRACT_BLOCKER:
  the semantics are unambiguous and implementable without touching the contract.
- **RECON-001 vs RECON-006** (mandate §26): they are distinct — RECON-001 is the
  tolerance *classification* rule (difference ≤ tolerance → CONSISTENT), RECON-006 is an
  *output-schema* prohibition (no resolved_value/winner field). G-RECON-001 demonstrates
  CONSISTENT classification; G-RECON-006 demonstrates the forbidden-field schema on the
  same conflict input. CONTRACT_BLOCKER: NO.
- **Relative difference formula** (frozen here): difference = max(values) − min(values);
  relative_difference = difference / min(|values|).
- **Source health priority** (contract §17, transcribed in the validator):
  ERROR > EMPTY > STALE > DEGRADED > UNRESOLVED > OK.

## Coverage matrix

| Golden ID | Contract ID | Scenario | Fixture | Expected Result | Evidence |
| --------- | ----------- | -------- | ------- | --------------- | -------- |
| P14C-GOLD-001 | P14C-EVID-001 | every ingestion attempt has one durable audit event | tests/contracts/p14c/fixtures/G-001_evid.json | audit_outcome_sequence, canonical_record_count, observation_audit_outcomes | audit_file_lines=5; canonical_file_lines=2; restart_recovery=True |
| P14C-GOLD-002 | P14C-EVID-002 | audit file fully recovers after process restart | tests/contracts/p14c/fixtures/G-002_evid.json | audit_outcome_sequence_after_restart, canonical_record_count_after_restart, observation_audit_outcomes | restart_recovery=True |
| P14C-GOLD-003 | P14C-EVID-003 | failure evidence is durable, never memory-only | tests/contracts/p14c/fixtures/G-003_evid.json | audit_outcome_sequence_after_restart, canonical_record_count_after_restart, observation_audit_outcomes | restart_recovery=True |
| P14C-GOLD-004 | P14C-EVID-004 | SOURCE_EMPTY observation produces no canonical record, hash or ingestion_id | tests/contracts/p14c/fixtures/G-004_evid.json | canonical_record_count, empty_event_has_ingestion_id, empty_event_has_raw_payload_hash, observation_audit_outc | audit_file_lines=1; canonical_file_lines=0 |
| P14C-GOLD-005 | P14C-EVID-005 | SOURCE_ERROR and parse REJECTED outcomes are distinguishable | tests/contracts/p14c/fixtures/G-005_evid.json | observation_audit_outcomes, outcomes_distinct |  |
| P14C-GOLD-006 | P14C-MISS-001 | six missingness classes are mutually exclusive | tests/contracts/p14c/fixtures/G-006_miss.json | classes_all_distinct, classifications, each_case_exactly_one_class |  |
| P14C-GOLD-007 | P14C-MISS-002 | SOURCE_EMPTY is not EXPECTED_ABSENCE | tests/contracts/p14c/fixtures/G-007_miss.json | classifications, source_empty_not_reinterpreted |  |
| P14C-GOLD-008 | P14C-MISS-003 | PARSE_FAILURE is not SOURCE_ERROR | tests/contracts/p14c/fixtures/G-008_miss.json | classifications, parse_not_downgraded_to_source_error |  |
| P14C-GOLD-009 | P14C-MISS-004 | EXPECTED_ABSENCE cannot be auto-derived from missing data | tests/contracts/p14c/fixtures/G-009_miss.json | auto_derivation_forbidden, missingness, undeclared_missing_pair |  |
| P14C-GOLD-010 | P14C-MISS-005 | UNEXPECTED_MISSING when expected non-empty but actual empty | tests/contracts/p14c/fixtures/G-010_miss.json | missing_dates, missing_entities, missingness |  |
| P14C-GOLD-011 | P14C-MISS-006 | UNRESOLVED_AVAILABILITY when available_time is null | tests/contracts/p14c/fixtures/G-011_miss.json | availability_status, missingness, quality_status |  |
| P14C-GOLD-012 | P14C-EXP-001 | expected set is defined a priori, independent of payload | tests/contracts/p14c/fixtures/G-012_exp.json | entities_in_expected_but_not_in_actual, expected_dates_frozen, expected_entities_frozen, expected_set_defined_ |  |
| P14C-GOLD-013 | P14C-EXP-002 | ingestion failure does not change EXPECTED_CONTRACT | tests/contracts/p14c/fixtures/G-013_exp.json | expected_contract_unchanged, expected_dates_after_failure, expected_entities_after_failure |  |
| P14C-GOLD-014 | P14C-EXP-003 | each source appears at most once in EXPECTED_CONTRACT | tests/contracts/p14c/fixtures/G-014_exp.json | duplicate_source_keys_rejected, source_keys_count |  |
| P14C-GOLD-015 | P14C-EXP-004 | expected pairs are the cartesian product entities x dates | tests/contracts/p14c/fixtures/G-015_exp.json | expected_count, expected_pairs |  |
| P14C-GOLD-016 | P14C-COMP-001 | complete data yields coverage 1.0 (G-001) | tests/contracts/p14c/fixtures/G-016_comp.json | actual_count, coverage_ratio, expected_count, missing_dates, missing_entities, missing_pairs |  |
| P14C-GOLD-017 | P14C-COMP-002 | missing data is not forward-filled or defaulted | tests/contracts/p14c/fixtures/G-017_comp.json | actual_count, coverage_ratio, expected_count, forward_fill_forbidden, missing_pairs, missing_stays_missing |  |
| P14C-GOLD-018 | P14C-COMP-003 | denominator comes from expected set, not actual payload | tests/contracts/p14c/fixtures/G-018_comp.json | actual_count, coverage_ratio, denominator_source, expected_count, missing_entities |  |
| P14C-GOLD-019 | P14C-COMP-004 | entity / date / pair missing sets reported at all three granularities | tests/contracts/p14c/fixtures/G-019_comp.json | actual_count, coverage_ratio, expected_count, missing_dates, missing_entities, missing_pairs, three_granularit |  |
| P14C-GOLD-020 | P14C-COMP-005 | declared intentional absence excluded from denominator | tests/contracts/p14c/fixtures/G-020_comp.json | absence_in_denominator, absence_pairs_reported, actual_count, coverage_ratio, required_expected_count |  |
| P14C-GOLD-021 | P14C-TS-001 | event_time / available_time / ingested_at stay semantically separate | tests/contracts/p14c/fixtures/G-021_ts.json | fields_independently_checked, issues |  |
| P14C-GOLD-022 | P14C-TS-002 | event_time never substitutes for available_time | tests/contracts/p14c/fixtures/G-022_ts.json | admissibility_uses, event_time_used_for_admissibility, pit_admissible |  |
| P14C-GOLD-023 | P14C-TS-003 | ingested_at never substitutes for available_time | tests/contracts/p14c/fixtures/G-023_ts.json | admissibility_uses, ingested_at_used_for_admissibility, pit_admissible |  |
| P14C-GOLD-024 | P14C-TS-004 | unprovable available/event ordering reports UNKNOWN, not a guess | tests/contracts/p14c/fixtures/G-024_ts.json | issues, violation_forbidden |  |
| P14C-GOLD-025 | P14C-TS-001 | malformed and future timestamps are VIOLATIONs | tests/contracts/p14c/fixtures/G-025_ts.json | issues |  |
| P14C-GOLD-026 | P14C-REV-001 | revision gap is reported as ANOMALY without changing quality status | tests/contracts/p14c/fixtures/G-026_rev.json | canonical_record_count, gap_is_anomaly, quality_status_affected, revision_gaps |  |
| P14C-GOLD-027 | P14C-REV-002 | duplicate revision: same key same payload replays as DUPLICATE | tests/contracts/p14c/fixtures/G-027_rev.json | canonical_record_count, duplicate_is_same_revision_same_payload |  |
| P14C-GOLD-028 | P14C-REV-003 | same revision with different payload is RAW_MUTATION_DETECTED | tests/contracts/p14c/fixtures/G-028_rev.json | canonical_record_count, mutation_is_anomaly, original_payload_preserved |  |
| P14C-GOLD-029 | P14C-REV-004 | available_time regression reported as ANOMALY, record retained | tests/contracts/p14c/fixtures/G-029_rev.json | available_time_regressions, canonical_record_count, record_deleted, regression_is_anomaly |  |
| P14C-GOLD-030 | P14C-REV-005 | revision anomaly never breaks PIT visibility (P14-A authority) | tests/contracts/p14c/fixtures/G-030_rev.json | later_revision_invisible_before_availability, pit_authority, visible_revision_at_decision |  |
| P14C-GOLD-031 | P14C-DUP-001 | no source winner is auto-selected on conflict | tests/contracts/p14c/fixtures/G-031_dup.json | conflict_detected, conflict_stands_unresolved, forbidden_output_fields |  |
| P14C-GOLD-032 | P14C-DUP-002 | conflicting values are never averaged | tests/contracts/p14c/fixtures/G-032_dup.json | averaging_forbidden, forbidden_output_fields, preserved_values |  |
| P14C-GOLD-033 | P14C-DUP-003 | no silent resolution of conflicts | tests/contracts/p14c/fixtures/G-033_dup.json | forbidden_output_fields, silent_resolution_forbidden, status |  |
| P14C-GOLD-034 | P14C-DUP-004 | every source's value is preserved | tests/contracts/p14c/fixtures/G-034_dup.json | no_value_dropped, preserved_sources, preserved_values |  |
| P14C-GOLD-035 | P14C-FRESH-001 | fresh via P14-A market_daily policy | tests/contracts/p14c/fixtures/G-035_fresh.json | freshness, policy_id, policy_source |  |
| P14C-GOLD-036 | P14C-FRESH-002 | stale via P14-A policy, not a hardcoded count | tests/contracts/p14c/fixtures/G-036_fresh.json | computed_from_policy_max_age, freshness, policy_id |  |
| P14C-GOLD-037 | P14C-FRESH-003 | freshness policy is frozen infrastructure, not an alpha threshold | tests/contracts/p14c/fixtures/G-037_fresh.json | alpha_threshold_forbidden, freshness, policy_id, policy_registry |  |
| P14C-GOLD-038 | P14C-FRESH-004 | FRESH / STALE / UNRESOLVED evidence all produced | tests/contracts/p14c/fixtures/G-038_fresh.json | all_three_evidence_kinds_present, freshness |  |
| P14C-GOLD-039 | P14C-RECON-001 | difference within tolerance classifies CONSISTENT | tests/contracts/p14c/fixtures/G-039_recon.json | classification_source, difference, relative_difference, status |  |
| P14C-GOLD-040 | P14C-RECON-002 | difference beyond tolerance classifies CONFLICT | tests/contracts/p14c/fixtures/G-040_recon.json | classification_source, difference, relative_difference, status |  |
| P14C-GOLD-041 | P14C-RECON-003 | conflicting values preserved verbatim | tests/contracts/p14c/fixtures/G-041_recon.json | entry_fields_required, preserved_values, status |  |
| P14C-GOLD-042 | P14C-RECON-004 | provenance fields preserved per contributing source | tests/contracts/p14c/fixtures/G-042_recon.json | every_source_keeps_its_own_timestamps, provenance_fields_required, status |  |
| P14C-GOLD-043 | P14C-RECON-005 | tolerance policy is versioned | tests/contracts/p14c/fixtures/G-043_recon.json | group_fields_required, policy_id, policy_version, status |  |
| P14C-GOLD-044 | P14C-RECON-006 | reconciliation output carries no resolved_value / winner field | tests/contracts/p14c/fixtures/G-044_recon.json | conflict_stands_unresolved, forbidden_output_fields, status |  |
| P14C-GOLD-045 | P14C-PROV-A-001 | record provenance (Type A) contains raw_payload_hash and ingestion_id | tests/contracts/p14c/fixtures/G-045_prov.json | applies_to, record_provenance_fields_required |  |
| P14C-GOLD-046 | P14C-PROV-B-001 | observation provenance (Type B) carries no raw_payload_hash | tests/contracts/p14c/fixtures/G-046_prov.json | applies_to, observation_provenance_fields_required, raw_payload_hash_required |  |
| P14C-GOLD-047 | P14C-SH-001 | OK when no anomaly conditions hold | tests/contracts/p14c/fixtures/G-047_sh.json | deterministic_from_metrics, health |  |
| P14C-GOLD-048 | P14C-SH-002 | DEGRADED computed from rejected/mutation evidence, not hardcoded counts | tests/contracts/p14c/fixtures/G-048_sh.json | evidence_used, hardcoded_counts_forbidden, health |  |
| P14C-GOLD-049 | P14C-SH-003 | STALE when freshness aggregation is majority stale | tests/contracts/p14c/fixtures/G-049_sh.json | evidence_used, hardcoded_counts_forbidden, health |  |
| P14C-GOLD-050 | P14C-SH-004 | EMPTY when attempted>0, accepted=0, errors=0 | tests/contracts/p14c/fixtures/G-050_sh.json | distinct_from, health |  |
| P14C-GOLD-051 | P14C-SH-005 | ERROR when errors>0 and accepted=0 | tests/contracts/p14c/fixtures/G-051_sh.json | distinct_from, health |  |
| P14C-GOLD-052 | P14C-SH-006 | UNRESOLVED when attempted=0 | tests/contracts/p14c/fixtures/G-052_sh.json | health |  |
| P14C-GOLD-053 | P14C-DET-001 | identical inputs produce byte-identical artifacts on rerun | tests/contracts/p14c/fixtures/G-053_det.json | byte_identical_rerun, observation_audit_outcomes |  |
| P14C-GOLD-054 | P14C-DET-002 | deterministic outputs contain no runtime timestamp / random UUID / machine path | tests/contracts/p14c/fixtures/G-054_det.json | forbidden_patterns, golden_report_is_deterministic |  |
| P14C-GOLD-055 | P14C-DET-003 | manifest carries no dynamic timestamp | tests/contracts/p14c/fixtures/G-055_det.json | manifest_forbidden_keys, manifest_keys |  |
| P14C-GOLD-056 | P14C-RR-001 | process restart loses no durable audit evidence | tests/contracts/p14c/fixtures/G-056_rr.json | audit_outcome_sequence_after_restart, canonical_record_count_after_restart, restart_recovery |  |
| P14C-GOLD-057 | P14C-RR-002 | replay creates no new canonical record | tests/contracts/p14c/fixtures/G-057_rr.json | canonical_record_count |  |
| P14C-GOLD-058 | P14C-RR-003 | replay attempt audited as DUPLICATE | tests/contracts/p14c/fixtures/G-058_rr.json | audit_outcome_sequence, replay_outcome_is_duplicate |  |
| P14C-GOLD-059 | P14C-BND-001 | RESEARCH_END frozen at 2026-09-22 | tests/contracts/p14c/fixtures/G-059_bnd.json | RESEARCH_END, authority |  |
| P14C-GOLD-060 | P14C-BND-002 | VIRGIN_START frozen at 2026-09-23; fixture dates stay in research zone | tests/contracts/p14c/fixtures/G-060_bnd.json | VIRGIN_START, all_fixture_dates_below_virgin_start, authority |  |
| P14C-GOLD-061 | P14C-BND-003 | assert_research_zone raises on virgin decision dates | tests/contracts/p14c/fixtures/G-061_bnd.json | assert_research_zone_raises |  |
| P14C-GOLD-062 | P14C-BND-004 | production FACTOR_REGISTRY unchanged during P14-C | tests/contracts/p14c/fixtures/G-062_bnd.json | factor_count, factor_registry_sha256 |  |
| P14C-GOLD-063 | P14C-REV-005 | PIT-GOOD: available_time <= decision_time is admissible (P14-A authority) | tests/contracts/p14c/fixtures/G-063_pit.json | admissibility, boundary_is_inclusive, pit_authority |  |
| P14C-GOLD-064 | P14C-REV-005 | PIT-BAD: available_time > decision_time is inadmissible | tests/contracts/p14c/fixtures/G-064_pit.json | admissibility, pit_authority |  |

## Anti-cheat guarantees (mandate §31)

- Check A/E: the golden layer never imports the P14-C production implementation
  (quality / reconciliation / source_health / adapters / audit script) — enforced by
  an import-statement scan over the golden layer sources.
- Check B: expected entity/date sets are declared a priori; fixtures where actual ≠
  expected (G-EXP-001, G-COMP-003) prove the expected set is not payload-derived.
- Check C: banned fixture-control tokens never appear in any fixture file (scan).
- Check D: the contract/matrix bytes are hash-pinned; any silent contract edit fails
  the golden layer instead of re-blessing the answers.

