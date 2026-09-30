# P14-C Acceptance Matrix

> 每个 Contract invariant 对应至少一个 Golden Test。
> Golden Tests 将在 Contract 通过独立审查后的下一阶段编写。

## Missingness

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-MISS-001 | SOURCE_ERROR ≠ EXPECTED_ABSENCE | golden/source_error/ | missingness = SOURCE_ERROR | ✅ | ✅ |
| P14C-MISS-002 | PARSE_FAILURE ≠ SOURCE_ERROR | golden/parse_failure/ | missingness = PARSE_FAILURE | ✅ | ✅ |
| P14C-MISS-003 | SOURCE_EMPTY ≠ EXPECTED_ABSENCE | golden/source_empty/ | missingness = SOURCE_EMPTY | ✅ | ✅ |
| P14C-MISS-004 | EXPECTED_ABSENCE 仅由 contract 声明触发 | golden/expected_absence/ | missingness = EXPECTED_ABSENCE | ✅ | ✅ |
| P14C-MISS-005 | UNEXPECTED_MISSING 有 expected 但 actual 为空 | golden/unexpected_missing/ | missingness = UNEXPECTED_MISSING | ✅ | ✅ |
| P14C-MISS-006 | UNRESOLVED_AVAILABILITY 当 available_time 缺失 | golden/unresolved_availability/ | quality_status = UNRESOLVED | ✅ | ✅ |

## Expected Contract

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-EXP-001 | Expected set 独立于 actual payload | golden/independent_contract/ | 删除 payload 后 expected set 不变 | ✅ | ✅ |
| P14C-EXP-002 | Expected contract 冻结后 missing entity 可检测 | golden/missing_entity/ | missing_entities 非空 | ✅ | ✅ |
| P14C-EXP-003 | Expected contract 冻结后 missing date 可检测 | golden/missing_date/ | missing_dates 非空 | ✅ | ✅ |
| P14C-EXP-004 | Entity-date pair coverage 可计算 | golden/pair_coverage/ | coverage_ratio = actual/expected | ✅ | ✅ |

## Completeness

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-COMP-001 | coverage_ratio 由集合差计算 | golden/complete/ | coverage = 1.0 | ✅ | ✅ |
| P14C-COMP-002 | coverage_ratio < 1 当有缺失 | golden/partial/ | coverage < 1.0 | ✅ | ✅ |
| P14C-COMP-003 | missing 数据不被 forward-fill | golden/partial/ | missing 字段保留为 None/空 | ✅ | ✅ |
| P14C-COMP-004 | 9 维度 quality_report 结构完整 | golden/nine_dimensions/ | 每维度有 status/reasons/metrics/evidence | ✅ | ✅ |

## Freshness

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-FRESH-001 | freshness 判断委托 P14-A freshness_status | golden/freshness_fresh/ | status = fresh | ✅ | ✅ |
| P14C-FRESH-002 | STALE 从 policy 计算 | golden/freshness_stale/ | status = stale | ✅ | ✅ |
| P14C-FRESH-003 | freshness_policy_id 缺失 → UNKNOWN | golden/freshness_unknown/ | status = unknown | ✅ | ✅ |

## Revision

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-REV-001 | revision gap 检测 | golden/revision_gap/ | revision_gap issue | ✅ | ✅ |
| P14C-REV-002 | duplicate revision 检测 | golden/revision_dup/ | same_revision issue | ✅ | ✅ |
| P14C-REV-003 | available_time regression 检测 | golden/revision_regression/ | regression issue | ✅ | ✅ |

## Reconciliation

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-RECON-001 | CONSISTENT 当 |reconciliation| ≤ tolerance | golden/recon_consistent/ | status = CONSISTENT | ✅ | ✅ |
| P14C-RECON-002 | CONFLICT 当 \|difference\| > tolerance | golden/recon_conflict/ | status = CONFLICT | ✅ | ✅ |
| P14C-RECON-003 | 双 source value 保留 | golden/recon_conflict/ | sources[0].value ≠ sources[1].value | ✅ | ✅ |
| P14C-RECON-004 | provenance 保留 | golden/recon_conflict/ | 每条含 event_time/available_time/ingested_at | ✅ | ✅ |
| P14C-RECON-005 | policy_id/policy_version 记录 | golden/recon_conflict/ | 字段存在 | ✅ | ✅ |
| P14C-RECON-006 | 不得自动选择 winner | golden/recon_conflict/ | 无 resolved_value 字段 | ✅ | ✅ |

## Source Health

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-SH-001 | OK 当无异常 | golden/sh_ok/ | health = OK | ✅ | ✅ |
| P14C-SH-002 | DEGRADED 当有 rejected/mutations | golden/sh_degraded/ | health = DEGRADED | ✅ | ✅ |
| P14C-SH-003 | STALE 当 freshness 占多数 stale | golden/sh_stale/ | health = STALE | ✅ | ✅ |
| P14C-SH-004 | EMPTY 当 attempted>0, accepted=0 | golden/sh_empty/ | health = EMPTY | ✅ | ✅ |
| P14C-SH-005 | ERROR 当 errors>0 且 accepted=0 | golden/sh_error/ | health = ERROR | ✅ | ✅ |
| P14C-SH-006 | UNRESOLVED 当 attempted=0 | golden/sh_unresolved/ | health = UNRESOLVED | ✅ | ✅ |

## Determinism

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-DET-001 | 双次运行 byte-identical | N/A（replay fixture） | SHA256(artifacts) 相同 | ✅ | ✅ |
| P14C-DET-002 | manifest 无动态 timestamp | N/A | manifest 中无 generated_at | ✅ | ✅ |

## Boundary

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-BND-001 | RESEARCH_END = 2026-09-22 | N/A | 常量不变 | ✅ | ✅ |
| P14C-BND-002 | VIRGIN_START = 2026-09-23 | N/A | 常量不变 | ✅ | ✅ |
| P14C-BND-003 | P13-Q/P13-R guard 活跃 | N/A | assert_research_zone raise | ✅ | ✅ |
| P14C-BND-004 | production factor registry 不变 | N/A | FACTOR_REGISTRY 未变 | ✅ | ✅ |

## Evidence

| Contract ID | Invariant | Golden Fixture | Expected Result | E2E Required | CI Required |
| ----------- | --------- | -------------- | --------------- | ------------ | ----------- |
| P14C-EVID-001 | 每次 attempt 有 durable event | N/A | audit file 含全部 attempt | ✅ | ✅ |
| P14C-EVID-002 | audit 重启后完整恢复 | N/A | 重新加载 outcomes 一致 | ✅ | ✅ |
| P14C-EVID-003 | quality_reasons[] 保留 | golden/reasons/ | reasons 非空且有内容 | ✅ | ✅ |
