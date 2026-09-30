# P14-C Research Plan — Data Quality / Reconciliation / Source Health

- 日期：2026-09-30
- 基线：`84021d6`（P14-B 验收终点）；P14-B 已独立验收 PASS。
- 性质：**可审计的数据质量闸门**（infrastructure / research-quality gate）。不是 alpha/factor/recommendation/trading development。

## 1. 核心问题

对 P14-B raw / normalized information 回答十个问题：完整性、缺失实体/日期、时间字段异常、revision 异常、duplicate/conflict、freshness、source 健康、多来源一致性、哪些记录可进研究层、哪些必须隔离。

## 2. Quality Model（9 维度，每个带 status/reason/metrics/evidence）

Completeness / Validity / Timeliness / Freshness / Consistency / RevisionIntegrity / ProvenanceIntegrity / PITAdmissibility / SourceHealth。

## 3. 关键设计

### Missingness 分类（§6）
EXPECTED_ABSENCE / UNEXPECTED_MISSING / SOURCE_EMPTY / SOURCE_ERROR / PARSE_FAILURE / UNRESOLVED_AVAILABILITY——按可观测原因分类，优先级：source error > parse failure > unresolved availability > source empty > expected absence > unexpected missing。不做统一 MISSING。

### Timestamp quality（§7）
逐字段检测：malformed、无时区、ingested_at < available_time（我方管线不可能先于可得时间存储——可证明的违规）。available_time vs event_time 的顺序**按 source contract 判断**：契约声明 `available_after_event` 则违规可报，无法证明则报 `available_vs_event_unprovable`（UNKNOWN，不猜测）。`future timestamp` 仅在显式提供 reference_time 时检测（deterministic，非 runtime now）。

### PIT quality（§8）
完全委托 P14-A `pit.is_admissible`——P14-C 是 PIT quality auditor，不是第二套 PIT。计数：PIT_ADMISSIBLE / PIT_REJECTED / AVAILABLE_TIME_MISSING / AVAILABLE_TIME_AFTER_DECISION。

### Freshness（§9）
复用 P14-A freshness policy；报告键规范化为大写 FRESH/STALE/UNKNOWN/MISSING_POLICY/UNRESOLVED。freshness window 是 infrastructure policy，不是 alpha threshold，不优化。

### Revision integrity（§10）
检测 same_revision_different_payload / revision_gap / revision_available_time_regression。异常只 detected + reported + preserved，不删除、不自选"可信 revision"。

### Cross-source reconciliation（§12/§13）
组键 = (entity_id, entity_type, event_time, unit, currency)；同组 ≥2 来源给 ≥2 个不同非空 value → CONFLICT，双值/difference/relative_difference/timestamps/provenance 全保留。Tolerance policy 显式版本化：`DEFAULT_POLICY`（strict equality，abs=0/rel=0）；`reconcile_pair` 供单对判断。不从数据结果反向调 tolerance。

### Source health（§14/§15）
从可观测证据 deterministic 聚合（无 ML、无手工标签）：attempted/accepted/rejected/duplicates/mutations/errors/fresh/stale/coverage。规则：无 attempt 且无错误 → UNRESOLVED；无 accepted 且有 errors → ERROR；attempted>0 但全空 → EMPTY；errors/mutations/rejected>0 → DEGRADED；stale 占多数 → STALE；否则 OK。全部理由写入 reasons[]。

### Record quality decision（§16/§17）
ADMISSIBLE / ADMISSIBLE_WITH_WARNING / REJECTED / UNRESOLVED + `quality_reasons[]`。PIT verdict 委托 P14-A；provenance 违规 → REJECTED；availability 缺失 → UNRESOLVED；stale/时间戳警告 → WITH_WARNING。**quality gate 不绕过 P14-A PIT**——PIT 判断仍调用 `pit.is_admissible`。

## 4. Virgin 保护

P13-U 常量从 `research_boundary.py` 单一来源导入（P14-A 提升）；`test_p13u_virgin_boundary_unchanged` 锁定 RESEARCH_END/VIRGIN_START 不变；quality audit 的所有 fixture 日期 < 2026-09-23；P13-Q/P13-R guard 回归测试继续通过。

## 5. 产物与复现

`scripts/run_p14c_quality_audit.py --out-dir <dir>`：deterministic fixtures（含 10 类质量异常：missing available_time、duplicate ingestion、mutation（未接受）、late/missing available_time、stale、revision timeline、conflicting sources、UNRESOLVED 变体）→ `quality_report.json` / `source_health.json` / `completeness.json` / `reconciliation.json` / `manifest.json`。双次运行 byte-identical（manifest 输入含 P13-R audit 与 RAW_STORE_AUDIT 文档 hash）。注意：raw store 是 append-only——对比前必须清理输出目录。
