# P14-C Acceptance Matrix — Revised

> Design Contract invariant ↔ Acceptance Matrix row ↔ Future Golden Test
> 三者可追踪。每个 Contract ID 编号在本文件和 DESIGN-CONTRACT.md 中一致。
>
> 状态：DRAFT — awaiting independent contract review
>
> Bidirectional closure mechanically verified (scripts/audit_p14c_contract.py):
> contract_unique_ids = 61, matrix_unique_ids = 61,
> orphan_contract_invariants = 0, orphan_matrix_rows = 0,
> duplicate_contract_ids = 0, duplicate_matrix_ids = 0, undefined_matrix_ids = 0

## Missingness

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-MISS-001 | 六类互斥，任何 observation 只能属于一类 | six_class_mutual_exclusion/ | 每条 observation 只有一个分类 | ✅ | ✅ |
| P14C-MISS-002 | SOURCE_EMPTY ≠ EXPECTED_ABSENCE | source_empty_vs_expected_absence/ | 两者分类不混淆 | ✅ | ✅ |
| P14C-MISS-003 | PARSE_FAILURE ≠ SOURCE_ERROR | parse_vs_source_error/ | 两者分类不混淆 | ✅ | ✅ |
| P14C-MISS-004 | EXPECTED_ABSENCE 不能由"实际没数据"自动推导 | auto_derive_rejection/ | 缺数据但不满足 expected_absence 条件 → UNEXPECTED_MISSING | ✅ | ✅ |
| P14C-MISS-005 | UNEXPECTED_MISSING：expected 要求存在但 actual 为空 | unexpected_missing/ | missingness = UNEXPECTED_MISSING | ✅ | ✅ |
| P14C-MISS-006 | UNRESOLVED_AVAILABILITY 当 available_time 为 None | unresolved_availability/ | quality_status = UNRESOLVED | ✅ | ✅ |

## Expected Contract

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-EXP-001 | Expected set 在 audit 运行前定义 | independent_contract/ | 删除 payload 后 expected set 不变 | ✅ | ✅ |
| P14C-EXP-002 | ingestion 失败不改变 EXPECTED_CONTRACT | ingestion_failure/ | EXPECTED_CONTRACT 不变 | ✅ | ✅ |
| P14C-EXP-003 | 每个 source 最多出现一次 | duplicate_source/ | 仅计一次 | ✅ | ✅ |
| P14C-EXP-004 | expected_pairs = entities × dates | cartesian_product/ | pair 集合正确 | ✅ | ✅ |

## Completeness

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-COMP-001 | coverage_ratio 由 required/actual pair 集合差计算（不得手工填写） | complete/ 与 partial/ | coverage = 1.0（完整）；有缺失时 < 1.0 | ✅ | ✅ |
| P14C-COMP-002 | missing 数据不得被 forward-fill / 默认值填充 / 静默删除 | partial/ | missing 字段保留为 None/空 | ✅ | ✅ |
| P14C-COMP-003 | expected set 独立于 actual ingestion 结果 | independent_contract/ | ingestion 失败后 expected set 不变 | ✅ | ✅ |
| P14C-COMP-004 | entity / date / pair 三种粒度 missing 集合分别报告 | granularity/ | 三粒度 missing 集合齐全 | ✅ | ✅ |
| P14C-COMP-005 | EXPECTED_ABSENCE pair 不计入 denominator | expected_absence_pair/ | denominator 排除 expected_absence pair | ✅ | ✅ |

## Freshness

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-FRESH-001 | freshness 判断委托 P14-A freshness_status | freshness_fresh/ | status = fresh | ✅ | ✅ |
| P14C-FRESH-002 | STALE 从 policy 计算 | freshness_stale/ | status = stale | ✅ | ✅ |
| P14C-FRESH-003 | policy_id 缺失 → UNKNOWN | freshness_unknown/ | status = unknown | ✅ | ✅ |
| P14C-FRESH-004 | FRESH/STALE/UNRESOLVED 三种证据在 audit 中产生 | macro_stale_variant/ | 至少一种 stale evidence | ✅ | ✅ |

## Revision

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-REV-001 | revision gap 检测 | revision_gap/ | revision_gap issue | ✅ | ✅ |
| P14C-REV-002 | duplicate revision 检测 | revision_dup/ | same_revision issue | ✅ | ✅ |
| P14C-REV-003 | payload mutation 检测 | revision_mutation/ | RAW_MUTATION_DETECTED | ✅ | ✅ |
| P14C-REV-004 | available_time regression 检测 | revision_regression/ | regression issue | ✅ | ✅ |
| P14C-REV-005 | revision anomaly 不破坏 PIT | revision_pit/ | PIT 判断不受影响 | ✅ | ✅ |

## Reconciliation

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-RECON-001 | CONSISTENT 当 ≤ tolerance | recon_consistent/ | status = CONSISTENT | ✅ | ✅ |
| P14C-RECON-002 | CONFLICT 当 > tolerance | recon_conflict/ | status = CONFLICT | ✅ | ✅ |
| P14C-RECON-003 | 双 source value 保留 | recon_conflict/ | value A ≠ value B 均保留 | ✅ | ✅ |
| P14C-RECON-004 | provenance 保留（event_time/available_time/ingested_at） | recon_conflict/ | 每条含三个 timestamp 字段 | ✅ | ✅ |
| P14C-RECON-005 | policy_id/policy_version 记录 | recon_conflict/ | 字段存在 | ✅ | ✅ |
| P14C-RECON-006 | 不得自动选择 winner | recon_conflict/ | 无 resolved_value 字段 | ✅ | ✅ |

## Source Health

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-SH-001 | health 由 deterministic 规则从 observable metrics 计算 | sh_ok/ | health = OK（六态 deterministic 判定） | ✅ | ✅ |
| P14C-SH-002 | 不得硬编码 stale 计数 | sh_degraded/ | health = DEGRADED（由 rejected/mutations 证据计算） | ✅ | ✅ |
| P14C-SH-003 | 不得引入 ML health score | sh_stale/ | health = STALE（由 freshness 占比计算） | ✅ | ✅ |
| P14C-SH-004 | EMPTY 当 attempted>0, accepted=0 | sh_empty/ | health = EMPTY | ✅ | ✅ |
| P14C-SH-005 | ERROR 当 errors>0 且 accepted=0 | sh_error/ | health = ERROR | ✅ | ✅ |
| P14C-SH-006 | UNRESOLVED 当 attempted=0 | sh_unresolved/ | health = UNRESOLVED | ✅ | ✅ |

## Determinism

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-DET-001 | 双次运行 byte-identical | N/A（replay fixture） | SHA256(artifacts) 相同 | ✅ | ✅ |
| P14C-DET-002 | 禁止 runtime timestamp / random UUID / machine path 进入输出 | N/A | 所有 JSON 字段 deterministic | ✅ | ✅ |
| P14C-DET-003 | manifest 不含动态 timestamp | N/A | manifest 中无 generated_at | ✅ | ✅ |

## Boundary

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-BND-001 | RESEARCH_END = 2026-09-22 | N/A | 常量不变 | ✅ | ✅ |
| P14C-BND-002 | VIRGIN_START = 2026-09-23 | N/A | 常量不变 | ✅ | ✅ |
| P14C-BND-003 | P13-Q/P13-R guard 活跃 | N/A | assert_research_zone raise | ✅ | ✅ |
| P14C-BND-004 | production factor registry 不变 | N/A | FACTOR_REGISTRY 未变 | ✅ | ✅ |

## Evidence

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-EVID-001 | 每次 attempt 有 durable event | N/A | audit file 含全部 attempt | ✅ | ✅ |
| P14C-EVID-002 | audit 重启后完整恢复 | N/A | 重新加载 outcomes 一致 | ✅ | ✅ |
| P14C-EVID-003 | SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY 的 evidence 不得仅存在于进程内存 | failure_evidence/ | evidence 位于 durable audit JSONL | ✅ | ✅ |
| P14C-EVID-004 | SOURCE_EMPTY observation 不产生 canonical record/hash/id | source_empty_evidence/ | 不进入 raw_records.jsonl | ✅ | ✅ |
| P14C-EVID-005 | SOURCE_ERROR 与 REJECTED outcome 可区分 | source_error_vs_rejected/ | outcome 字段不同 | ✅ | ✅ |

## Provenance

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-PROV-A-001 | Record provenance 含 raw_payload_hash | record_provenance/ | raw_payload_hash 字段存在 | ✅ | ✅ |
| P14C-PROV-B-001 | Observation provenance 不含 raw_payload_hash | observation_provenance/ | raw_payload_hash 字段不存在 | ✅ | ✅ |

## Restart / Replay

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-RR-001 | process restart 后 durable audit 完整恢复 | N/A | 重新加载后一致 | ✅ | ✅ |
| P14C-RR-002 | 重复 replay 不产生新 canonical record | N/A | records 数不变 | ✅ | ✅ |
| P14C-RR-003 | replay audit event 标记为 DUPLICATE | N/A | outcome = DUPLICATE | ✅ | ✅ |

## Timestamp Quality

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-TS-001 | event_time/available_time/ingested_at 语义分离 | N/A | 三个字段独立检查 | ✅ | ✅ |
| P14C-TS-002 | event_time 不替代 available_time | N/A | 无替代路径 | ✅ | ✅ |
| P14C-TS-003 | ingested_at 不替代 available_time | N/A | 无替代路径 | ✅ | ✅ |
| P14C-TS-004 | source contract 无法证明顺序时报告 UNKNOWN | N/A | status = UNKNOWN（非 VIOLATION） | ✅ | ✅ |


## Duplicate / Mutation

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-DUP-001 | 不得自动选择 source winner | dup_no_winner/ | 无 resolved_value 字段 | ✅ | ✅ |
| P14C-DUP-002 | 不得自动平均 | dup_no_average/ | 无 averaged_value 字段 | ✅ | ✅ |
| P14C-DUP-003 | 不得静默 resolution | dup_no_silent_resolution/ | 无 resolved_status 字段 | ✅ | ✅ |
| P14C-DUP-004 | 不同 source 的 value 都必须保留 | dup_all_values_preserved/ | 全部 value 字段存在 | ✅ | ✅ |
