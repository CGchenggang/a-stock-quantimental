# P14-C Design Contract

> 本文档是 P14-C（Data Quality / Reconciliation / Source Health）的行为契约。
> 一经独立验收冻结，后续修改须通过正式 contract change 流程。
>
> 状态：DRAFT — awaiting independent contract review

## 1. Scope

### 1.1 P14-C 负责

| 职责 | 说明 |
|------|------|
| Data quality | 对 raw/normalized information 逐条评估质量 |
| Missingness | 对缺失数据按原因分类（六类） |
| Completeness | 对 expected vs actual entity/date/pair 做 coverage 审计 |
| Freshness | 消费 P14-A freshness policy，按 record 计算 FRESH/STALE |
| Revision integrity | 检测 revision gap / duplicate revision / payload mutation / available_time regression |
| Cross-source reconciliation | 对同一事实的多个来源做一致性比较（保留全部 provenance，不裁决） |
| Source health | 从可观测 ingestion 证据 deterministic 聚合 per-source 健康状态 |
| Quality decision | 逐条输出 ADMISSIBLE / ADMISSIBLE_WITH_WARNING / REJECTED / UNRESOLVED + quality_reasons |
| Audit evidence | 输出结构化 quality_report.json / source_health.json / completeness.json / reconciliation.json |

### 1.2 P14-C 不负责

| 排除项 | 原因 |
|--------|------|
| Alpha generation | P14-C 是 quality gate，不产生投资信号 |
| Factor selection / weighting | 属于 P13 研究 / P14-E production |
| Portfolio policy | 属于 Recommendation Engine（P13-R） |
| Trading decision | 属于 production trading path |
| Calibration | 属于 P13-Q probability layer |
| P13-T holdout evaluation | 独立阶段，数据条件未满足 |
| LLM stock selection | 属于后续 Agent 阶段 |
| PIT 判断 | P14-A `pit.is_admissible` 是唯一 authority |
| Freshness policy 定义 | P14-A `FRESHNESS_POLICIES` 是唯一来源 |

## 2. Missingness Taxonomy（冻结）

六类互斥（按优先级降序排列）：

| Class | 定义 | 触发条件 | 不属于该类别的情况 | Durable evidence | Source health 影响 | Completeness 影响 | Research layer |
|-------|------|---------|-------------------|-----------------|-------------------|------------------|---------------|
| SOURCE_ERROR | source fetch/transport/auth/timeout 失败 | adapter.fetch() 抛出异常 | parse 失败（→PARSE_FAILURE）；contract 声明不需要数据（→EXPECTED_ABSENCE） | adapter.error → durable audit_event | ERROR | 0 records counted | 不可进入 |
| PARSE_FAILURE | source 成功返回数据但解析失败 | adapter.parse() 抛出异常 | fetch 失败（→SOURCE_ERROR）；返回零 payload（→SOURCE_EMPTY） | audit_event(REJECTED) | ERROR 或 DEGRADED | 0 records counted | 不可进入 |
| SOURCE_EMPTY | source 请求成功、无 fetch/parse 失败、返回合法空结果 | adapter.fetch() 返回 `[]` | fetch/parse 失败；contract 声明不需要数据 | IngestionReport(status=EMPTY_SUCCESS) | EMPTY | 0 records counted | 无记录可进入 |
| EXPECTED_ABSENCE | 根据独立 expected contract，该 entity/date 不要求存在数据 | EXPECTED_CONTRACT 显式声明 `expected_absence=true` 或 expected_entities/dates 为空 | contract 要求存在但实际缺失（→UNEXPECTED_MISSING）；source 失败（→SOURCE_ERROR） | EXPECTED_CONTRACT 声明本身 | 不影响（合法缺失） | expected=0, coverage=1.0（by definition） | N/A |
| UNEXPECTED_MISSING | contract 要求该 entity/date 存在，但实际没有可接受记录 | expected_entities/dates 非空但 actual 为空 | contract 未要求（→EXPECTED_ABSENCE）；source 失败（→SOURCE_ERROR） | completeness delta（expected−actual） | DEGRADED 或 STALE | coverage<1.0 | 不可进入（缺失本身是 gap） |
| UNRESOLVED_AVAILABILITY | available_time 无法确定（缺失/格式错误） | record.available_time 为 None 或空 | source 明确声明 available_time（→正常 PIT 判断） | to_information_record 抛出 ValueError | UNRESOLVED 或 DEGRADED | 该 record 不计入 coverage | 不可进入 |

**规则**：
- EXPECTED_ABSENCE **不能**由"实际没数据"自动推导。
- SOURCE_EMPTY **不能**与 EXPECTED_ABSENCE 混淆——前者是"请求成功但返回空"，
  后者是"contract 声明不需要请求"。
- PARSE_FAILURE **不能**与 SOURCE_ERROR 混淆——前者是"数据到了但解析失败"，
  后者是"数据根本没到"。

## 3. Expected Contract（冻结）

### 3.1 Authority 来源

EXPECTED_CONTRACT 是 P14-C 的 expected universe 唯一事实来源。它定义
每个 source 应该交付哪些 entity/date。

**绝对禁止**从 actual payload 推导 expected set。

### 3.2 结构

```python
EXPECTED_CONTRACT = {
    source_id: {
        "expected_entities": [str, ...],   # 应交付的 entity_id 列表
        "expected_dates": [str, ...],      # 应交付的 event date 列表
        "expected_absence": bool,          # True = contract 声明不需要数据
        "expected_empty": bool,            # True = deliberate SOURCE_EMPTY fixture
    }
}
```

### 3.3 不变量

- **INV-EXP-001**: EXPECTED_CONTRACT 必须在 audit 运行前定义，不从 actual payload 推导。
- **INV-EXP-002**: 如果 ingestion 失败导致某 entity/date 的 payload 消失，EXPECTED_CONTRACT 仍然包含它。
- **INV-EXP-003**: 每个 source 在 EXPECTED_CONTRACT 中最多出现一次。
- **INV-EXP-004**: expected_pairs = {(entity, date) for entity in expected_entities for date in expected_dates}。

## 4. Completeness Contract（冻结）

### 4.1 计算方式

```text
expected_entities  ← EXPECTED_CONTRACT[source].expected_entities
expected_dates     ← EXPECTED_CONTRACT[source].expected_dates
expected_pairs     ← {(entity, date) for entity in expected_entities
                                  for date in expected_dates}

actual_entities    ← {r.entity_id for r in successfully ingested records
                                  if r.source == source}
actual_dates       ← {r.event_time[:10] for r in successfully ingested records
                                  if r.source == source}
actual_pairs       ← {(r.entity_id, r.event_time[:10]) for r in ...}

missing_entities   ← expected_entities − actual_entities
missing_dates      ← expected_dates − actual_dates
missing_pairs      ← expected_pairs − actual_pairs

expected_count     ← len(expected_pairs)
actual_count       ← expected_count − len(missing_pairs)
coverage_ratio     ← actual_count / expected_count  (1.0 if expected_count == 0)
```

### 4.2 状态定义

| 状态 | 条件 |
|------|------|
| 完整 | missing_entities = ∅ 且 missing_dates = ∅ 且 missing_pairs = ∅ |
| 部分完整 | 某些 entity/date 缺失但非全部 |
| 完全缺失 | actual_entities = ∅ 且 expected_entities ≠ ∅ |
| 合法预期缺失 | EXPECTED_CONTRACT 声明 expected_absence = True |

### 4.3 不变量

- **INV-COMP-001**: coverage_ratio 由 expected_pairs 与 actual_pairs 的集合差计算，不得手工填写。
- **INV-COMP-002**: missing_entities/dates **不得**被 forward-fill、默认值填充或静默删除。
- **INV-COMP-003**: expected set 独立于 actual ingestion 结果。
- **INV-COMP-004**: entity/date/pair 三种粒度的 missing 集合必须分别报告。

## 5. Freshness Contract（冻结）

### 5.1 唯一来源

P14-A `freshness_status(record, decision_time, policies)` 是 freshness 的唯一判断函数。

P14-C **不定义**第二套 freshness policy 或 threshold。

### 5.2 报告键

P14-C 将 P14-A 的小写状态（fresh/stale/unknown/missing_policy）规范化为大写
（FRESH/STALE/UNKNOWN/MISSING_POLICY），并追加 UNRESOLVED（available_time 缺失）。

### 5.3 不变量

- **INV-FRESH-001**: freshness 判断必须调用 P14-A `freshness_status`。
- **INV-FRESH-002**: 不得硬编码 stale 计数。
- **INV-FRESH-003**: freshness policy 是 infrastructure 配置，不是 alpha threshold。

## 6. Evidence Contract（冻结）

### 6.1 Evidence chain

```text
source adapter
    ↓ fetch() / parse()
ingestion attempt
    ↓ store.put() → ACCEPTED / DUPLICATE / RAW_MUTATION_DETECTED
    ↓ store.audit_event() → SOURCE_ERROR / AUTH_ERROR / TIMEOUT / REJECTED
durable audit file (raw_ingestion_audit.jsonl)
    ↓ audit_event 读取
quality classification (record_quality_decision)
    ↓
source_health (from observable metrics)
    ↓
completeness (from EXPECTED_CONTRACT vs actual)
    ↓
final quality_report.json
```

### 6.2 每种异常的 evidence 来源与消费

| 异常 | Evidence 产生位置 | Durable 持久化位置 | 消费位置 |
|------|-----------------|-------------------|---------|
| SOURCE_ERROR | adapter.fetch() 抛出异常 | raw_ingestion_audit.jsonl `outcome=SOURCE_ERROR` | source_health(health=ERROR), quality_report(source_health dim) |
| PARSE_FAILURE | adapter.parse() 抛出异常 | raw_ingestion_audit.jsonl `outcome=REJECTED` | source_health(health=ERROR/DEGRADED), quality_report(validity dim) |
| SOURCE_EMPTY | adapter.fetch() 返回 `[]` | IngestionReport(status=EMPTY_SUCCESS) | completeness(missingness=SOURCE_EMPTY), source_health(health=EMPTY) |
| EXPECTED_ABSENCE | EXPECTED_CONTRACT 声明 expected_absence=true | EXPECTED_CONTRACT 本身 | completeness(missingness=EXPECTED_ABSENCE) |
| UNEXPECTED_MISSING | completeness delta（expected − actual） | completeness.json missing_entities/dates | completeness(missingness=UNEXPECTED_MISSING), source_health(health=DEGRADED) |

### 6.3 不变量

- **INV-EVID-001**: 每一次 ingestion attempt（无论成功或失败）必须在 durable audit file 中有一条事件。
- **INV-EVID-002**: durable audit file 重启后必须完整恢复。
- **INV-EVID-003**: SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY 的 evidence 不得仅存在于进程内存。

## 7. Reconciliation Contract（冻结）

### 7.1 必须保留的字段

每个 reconciliation group 中的每个 contributing source 必须保留：

```text
source, source_id, value, event_time, available_time, ingested_at,
ingestion_id, raw_payload_hash, provenance
```

每个 group 必须保留：

```text
difference, relative_difference, policy_id, policy_version, status
```

### 7.2 不变量

- **INV-RECON-001**: 不得自动选择 source winner。
- **INV-RECON-002**: 不得自动平均。
- **INV-RECON-003**: 不得静默 resolution。
- **INV-RECON-004**: 不同 source 的 value 都必须保留。
- **INV-RECON-005**: tolerance policy 必须版本化（policy_id + policy_version）。

## 8. Provenance Contract（冻结）

所有最终质量判断必须能追溯到：source / source_id / raw_payload / raw_payload_hash / ingestion_id / available_time / ingested_at / adapter_version。

**INV-PROV-001**: quality_status = UNRESOLVED 的 record（available_time 缺失）不得进入 research layer。

## 9. Source Health Contract（冻结）

| 状态 | 条件 | 优先级 |
|------|------|--------|
| ERROR | errors > 0 且 accepted = 0 | 最高 |
| EMPTY | attempted > 0, accepted = 0, errors = 0 | 高 |
| STALE | stale > fresh（freshness 占多数 stale） | 中 |
| DEGRADED | errors > 0 或 mutations > 0 或 rejected > 0 或 coverage < 1.0 | 中 |
| UNRESOLVED | attempted = 0 且 accepted = 0 且 errors = 0 | 低 |
| OK | 无上述任何条件 | — |

**INV-SH-001**: health 状态由 deterministic 规则从 observable metrics 计算。
**INV-SH-002**: 不得硬编码 stale 计数。
**INV-SH-003**: 不得引入 ML health score。

## 10. Quality Decision Contract（冻结）

| Decision | 条件 |
|----------|------|
| REJECTED | provenance issues 存在 或 PIT 不通过 |
| UNRESOLVED | available_time 缺失 |
| ADMISSIBLE_WITH_WARNING | PIT 通过但存在 stale/timestamp warning |
| ADMISSIBLE | 全部检查通过 |

**INV-QD-001**: REJECTED 的 record 不得静默删除——必须保留在 quality report 中并说明原因。
**INV-QD-002**: quality_reasons[] 不得被清空或缩短。

## 11. Determinism Contract（冻结）

- **INV-DET-001**: 相同输入 → byte-identical 输出（从两个独立空目录运行）。
- **INV-DET-002**: 禁止 runtime timestamp / random UUID / unordered iteration / machine path 进入 deterministic output。
- **INV-DET-003**: manifest 不含动态 timestamp。

## 12. Research Boundary Contract（冻结）

- RESEARCH_END = 2026-09-22, VIRGIN_START = 2026-09-23。
- P14-C fixture 日期必须 < 2026-09-23。
- P13-U virgin protection 不得削弱。
- P13-T = STOPPED / NOT EXECUTED。

## 13. Scope Exclusions

P14-C 不负责：alpha generation, factor selection, factor weighting,
portfolio policy, recommendation, trading decision, calibration,
P13-T holdout evaluation, LLM stock selection.
