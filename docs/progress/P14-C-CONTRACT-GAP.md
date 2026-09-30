# P14-C Contract Gap Analysis

> 对比 P14-C Design Contract（冻结后的应有行为）与当前实现（868b729..HEAD）的差异。

## Gap Summary

| Contract ID | Invariant | Current Implementation | Gap | Future Implementation Required |
| ----------- | --------- | ---------------------- | --- | ------------------------------ |
| P14C-EXP-001 | Expected set 独立于 actual payload | `_compute_completeness` 已修复为从 EXPECTED_CONTRACT 取 expected | **已修复** | 否 |
| P14C-EXP-002 | missing entity 可检测 | 已实现 | **已修复** | 否 |
| P14C-EXP-003 | missing date 可检测 | 已实现 | **已修复** | 否 |
| P14C-EXP-004 | pair coverage 可计算 | 已实现 entity-date pair | **已修复** | 否 |
| P14C-MISS-001 | SOURCE_ERROR 分类 | `classify_missingness` 已定义；BrokenSourceAdapter 已加入 audit | **已修复** | 否 |
| P14C-MISS-002 | PARSE_FAILURE 分类 | ParseFailureAdapter 已加入 audit | **已修复** | 否 |
| P14C-MISS-003 | SOURCE_EMPTY 分类 | `EMPTY_SUCCESS` report status → SOURCE_EMPTY 分类 | **已修复** | 否 |
| P14C-MISS-004 | EXPECTED_ABSENCE 分类 | `expected_absence=True` in EXPECTED_CONTRACT | **已修复** | 否 |
| P14C-MISS-005 | UNEXPECTED_MISSING 分类 | company_announcement contract 有额外 expected date | **已修复** | 否 |
| P14C-MISS-006 | UNRESOLVED_AVAILABILITY | available_time=None → UNRESOLVED | **已修复** | 否 |
| P14C-COMP-001~004 | Completeness 计算 | 已实现 expected/actual/pair/coverage | **已修复** | 否 |
| P14C-FRESH-001~003 | Freshness 委托 P14-A | 已实现；policy_id 从 registry 保留 | **已修复** | 否 |
| P14C-REV-001~003 | Revision integrity | 已实现三类检测 | **已修复** | 否 |
| P14C-RECON-001~006 | Reconciliation evidence | 已实现 end-to-end 字段 | **已修复** | 否 |
| P14C-SH-001~006 | Source health 六态 | 已实现 deterministic 聚合 | **已修复** | 否 |
| P14C-DET-001~002 | Determinism | 双次 byte-identical 已验证 | **已修复** | 否 |
| P14C-BND-001~004 | Boundary | research_boundary.py 锁定 | **已修复** | 否 |
| P14C-EVID-001~003 | Durable evidence | RawStore audit_event + raw_ingestion_audit.jsonl | **已修复** | 否 |
| **P14C-QD-001** | REJECTED 不得静默删除 | `record_quality_decision` 输出 REJECTED + reasons，但 **quality_report.json 的 evidence 字段未包含逐条 REJECTED 记录明细** | **GAP** | 是——quality_report 需在 evidence 中列出全部 REJECTED record 的 record_id + reasons |
| **P14C-QD-002** | quality_reasons[] 保留 | record 层面保留，但 quality_report 的 dimension evidence 中仅显示 issue 汇总计数，**未逐条列出每条 record 的 quality_reasons** | **GAP** | 是——需要在 evidence 中添加逐条 record 的 quality_reasons |
| **P14C-SH-003** | STALE 需要从实际 freshness 计算 | source_health.py 的规则正确，但 **`run_p14c_quality_audit.py` 中 macro_pmi_cn 的 fresh=0/stale=5 说明 policy_id 正确传递了但 freshness 计算的 decision_time 需要确认是否与 RESEARCH_END_T 对齐** | **需确认** | 否——实现正确但 decision_time 选择影响结果 |
| **P14C-BND-004** | production factor registry 不变 | **当前 src diff 中无 factor 修改**——但 `information/__init__.py` 增加了 `to_information_record` export，需确认不改变 FACTOR_REGISTRY | **已确认安全** | 否 |

## 逐条 Gap 详情

### GAP-1: Quality report evidence 未逐条列出 REJECTED records

**Contract**: P14C-QD-001 — REJECTED 的 record 不得静默删除。

**Current**: `quality_report.json` 的 `validity` dimension evidence 仅有 `unresolved_avail` 摘要（source_id + reason 截断 120 字符），未包含完整 record_id 和全部 quality_reasons。

**Future implementation**: 在 `quality_report.json` 的 `validity.evidence` 中列出全部 REJECTED record 的 `{record_id, source, source_id, quality_reasons[]}`。

**Priority**: Medium — 影响审计可追溯性，不影响正确性。

### GAP-2: Quality report evidence 未逐条列出 quality_reasons

**Contract**: P14C-QD-002 — quality_reasons[] 保留。

**Current**: `quality_report.json` 的 dimensions 仅含汇总计数和 issue 摘要，未逐条列出每条 record 的 quality_reasons。

**Future implementation**: 添加 `quality_report.json.record_decisions[]` 数组，每条含 `{record_id, quality_status, quality_reasons[]}`。

**Priority**: Medium — 提升审计粒度。

### GAP-3: STALE freshness 的 decision_time 对齐

**Contract**: freshness 用 `decision_time`（= RESEARCH_END_T）与 available_time 的差判断。

**Current**: `_compute_freshness_per_record(research, RESEARCH_END_T)` 使用了正确的 decision_time。但 35d macro policy 对 2026-01-31 available 的 record 计算结果为 stale（差值 > 35d），这**在 policy 语义下是正确的**——不是 bug。

**No code change needed**：当前行为与 contract 一致。需要在 acceptance 文档中说明 stale 是因为 policy max_age 而非 bug。

**Priority**: Low — 文档说明即可。
