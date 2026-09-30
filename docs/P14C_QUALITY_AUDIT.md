# P14-C Quality Audit — 逐维度核验

- 日期：2026-09-30
- 范围：`src/astock_v2/information/quality.py`、`reconciliation.py`、`source_health.py`；产物 `data/industry/p14c/`

## Completeness

Audit 覆盖 4 个 fixture source（cn_index_daily / company_announcement / macro_pmi_cn / us_index_daily），10 个 deterministic fixture（含全部质量异常变体）。`completeness.json` 报告 expected_sources（4）/ sources_with_accepted_rows（4）。76-stock universe 的完整性由 P13 阶段覆盖，此处审计信息 source 维度。

## Missingness

`classify_missingness` 六类词表锁定（EXPECTED_ABSENCE / UNEXPECTED_MISSING / SOURCE_EMPTY / SOURCE_ERROR / PARSE_FAILURE / UNRESOLVED_AVAILABILITY），优先级 source_error > parse_failure > unresolved_availability > source_empty > expected_absence > unexpected_missing。测试锁定全部分类与优先级。

## Timestamp Quality

三个硬检查（malformed event/available/ingested、ingested_before_available）+ 语义检查（available_before_event 按 `available_after_event` 契约判定；无法证明 → UNKNOWN）。`test_timestamp_semantic_uncertainty_not_guessed` 锁定不做猜测。future timestamp 仅对显式 reference_time 检测。

## PIT Quality（delegation）

`pit_quality` 全部调用 P14-A `pit.is_admissible`；无第二套判断。计数含 PIT_ADMISSIBLE / PIT_REJECTED / AVAILABLE_TIME_MISSING / AVAILABLE_TIME_AFTER_DECISION。测试用 SimpleNamespace shim 证明 None/超窗两类边界均正确归入对应计数。

## Freshness

`freshness_quality` 报告键 UPPERCASE 规范化（FRESH/STALE/UNKNOWN/MISSING_POLICY/UNRESOLVED）。测试锁定：35d macro policy 下 20 天 fresh/38 天 stale；无 policy id → UNKNOWN。

## Revision Integrity

`revision_integrity_issues` 检出三类异常：same_revision_different_payload、revision_gap、revision_available_time_regression。异常只报告不删除（`test_revision_anomalies_preserved_not_deleted`）。

## Duplicate / Mutation / Conflict 统计

消费 P14-B ingestion audit（durable raw_ingestion_audit.jsonl）与 P14-A `detect_conflicts`。P14-C 不重实现 dedup/mutation 检测。

## Cross-source Reconciliation

`reconcile` 按 (entity_id, entity_type, event_time, unit, currency) 分组；同组 ≥2 来源给 ≥2 个不同非空 value → CONFLICT（双值/difference/relative_difference/timestamps/provenance 全保留）；一致性由冻结 tolerance policy 判定（strict equality 默认）。测试锁定：同值 CONSISTENT、异值 CONFLICT、abs/rel tolerance、policy 版本随行、输入顺序无关。

## Source Health

`source_health` 从可观测证据 deterministic 聚合：UNRESOLVED（无 attempt）/ ERROR（无 accepted 且有 errors）/ EMPTY（attempted>0 全空）/ STALE（stale 占多数）/ DEGRADED（errors/mutations/rejected/coverage<1）/ OK。全部理由写入 reasons[]。测试锁定：OK、DEGRADED（duplicates+mutations）、STALE、ERROR、EMPTY、coverage<1、确定性、无 ML 声明。

## Quality Decision

`record_quality_decision`：provenance 违规 → REJECTED；available 缺失/UNRESOLVED → UNRESOLVED；PIT_REJECTED → REJECTED；stale/timestamp 警告 → ADMISSIBLE_WITH_WARNING；否则 ADMISSIBLE。quality_reasons[] 全保留。**quality gate 不绕过 P14-A PIT**：PIT verdict 始终来自 `pit.is_admissible`。

## Determinism

全部输出 sort_keys + 无时间戳/随机字段；fixture 审计双次运行 byte-identical（见 ACCEPTANCE §Reproducibility）。
