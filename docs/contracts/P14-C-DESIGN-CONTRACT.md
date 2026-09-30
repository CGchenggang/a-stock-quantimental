# P14-C Design Contract — Revised

> 本文档是 P14-C（Data Quality / Reconciliation / Source Health）的行为契约。
> 由 P14-C-R3 独立验收发现的 7 项阻塞点驱动重建。
>
> 状态：DRAFT — awaiting independent contract review
>
> 修订历史：
> v1: 初始版本（P14-C-R1 前）
> v2: R3 修复——增加 Revision Integrity / Nine Dimensions / Provenance split /
>     SOURCE_EMPTY durable evidence / completeness denominator / bidirectional traceability

---

## 1. Purpose

P14-C 对 P14-B raw/normalized information 逐条评估质量、按来源一致性校验、
并输出可审计的 quality/reconciliation/health 报告。P14-C 只消费证据，不产生信号。

## 2. Scope

### 2.1 P14-C 负责

| 职责 | dimension_id |
|------|-------------|
| Data quality | COMP / VAL / TIME / FRESH / CONS / REV / PROV / PIT / SH |
| Missingness | 按原因分六类（见 §6） |
| Completeness | expected vs actual entity/date/pair coverage 审计 |
| Freshness | 消费 P14-A freshness policy，按 record 计算 FRESH/STALE |
| Revision integrity | gap / duplicate revision / payload mutation / available_time regression |
| Cross-source reconciliation | 一致性比较（保留全部 provenance，不裁决） |
| Source health | 从可观测 ingestion 证据 deterministic 聚合 |
| Quality decision | ADMISSIBLE / ADMISSIBLE_WITH_WARNING / REJECTED / UNRESOLVED + quality_reasons |
| Audit evidence | quality_report / source_health / completeness / reconciliation JSON |

### 2.2 P14-C 不负责

alpha generation, factor selection/weighting, portfolio policy, trading
decision, calibration, P13-T holdout, LLM stock selection, PIT 判断,
freshness policy 定义。

## 3. Boundary

### 3.1 P14-A remains authoritative for

PIT (available_time <= decision_time), available_time 语义, freshness policy
authority, provenance 基础语义, normalization, dedup/conflict 基础语义,
research boundary 常量。

### 3.2 P14-B remains authoritative for

raw immutability, raw ingestion audit (raw_records.jsonl +
raw_ingestion_audit.jsonl), ingestion_id, adapter metadata, durable
ingestion attempt semantics.

### 3.3 P14-C may

consume evidence, classify quality, compute completeness, reconcile, derive
source health. P14-C 不得重新定义 P14-A/P14-B 已冻结的底层事实。

---

## 4. Terminology

| 术语 | 定义 |
|------|------|
| EXPECTED_CONTRACT | 冻结的 a priori 集合，定义每个 source 应该交付哪些 entity/date。独立于 actual payload。 |
| Source Observation | adapter.fetch() + adapter.parse() 对一次 source 调用的实际返回 |
| Ingestion Attempt | 一次 store.put() 或 store.audit_event() 的调用 |
| Canonical Raw Record | 成功通过 store.put(ACCEPTED) 的不可变记录 |
| Durable Audit Event | 写入 raw_ingestion_audit.jsonl 的一条不可变事件 |
| Research Information Record | 通过 P14-A to_information_record 投影的记录 |
| Virgin Zone | decision_time >= VIRGIN_START (2026-09-23) |
| Research Zone | decision_time < VIRGIN_START |

---

## 5. Source Observation Contract

每次 adapter.ingest() 产生一种 Source Observation：

| Observation Type | 条件 | 产出 |
|-----------------|------|------|
| ACCEPTED | parse 成功且 store.put 返回 ACCEPTED | RawIngestRecord + RawInformationRecord |
| DUPLICATE | store.put 返回 DUPLICATE | 不产生新 canonical record |
| RAW_MUTATION_DETECTED | store.put 返回 RAW_MUTATION_DETECTED | 不产生新 canonical record |
| REJECTED (PARSE_FAILURE) | adapter.parse() 抛出异常 | 不产生 canonical record |
| REJECTED (UNRESOLVED) | available_time 缺失 | 不产生 canonical record |
| SOURCE_ERROR | adapter.fetch() 抛出异常 | 不产生任何 record |
| SOURCE_EMPTY | adapter.fetch() 返回 `[]` | 不产生任何 record |

**冻结规则**：

- SOURCE_EMPTY observation 由 adapter.fetch() 返回零 payload 产生。
- SOURCE_EMPTY observation **不生成** canonical raw record。
- SOURCE_EMPTY observation **不生成** raw_payload_hash（没有 payload 可 hash）。
- SOURCE_EMPTY observation **不生成** ingestion_id。
- SOURCE_EMPTY observation **写入** raw_ingestion_audit.jsonl 作为 durable evidence。
- 禁止用一个 source 同时承载 SOURCE_ERROR + SOURCE_EMPTY + EXPECTED_ABSENCE。

---

## 6. Durable Evidence Contract

### 6.1 存储文件

| 文件 | 内容 | 格式 |
|------|------|------|
| raw_records.jsonl | 仅 ACCEPTED 的 canonical record | JSONL, 每行一条 |
| raw_ingestion_audit.jsonl | **每一次** ingestion attempt 的事件 | JSONL, 每行一条 |

### 6.2 Audit Event Schema

每个 durable audit event 必须包含以下字段：

| 字段 | 类型 | Mandatory | 说明 |
|------|------|-----------|------|
| outcome | str | ✅ | ACCEPTED / DUPLICATE / RAW_MUTATION_DETECTED / SOURCE_ERROR / REJECTED / SOURCE_EMPTY / AUTH_ERROR / TIMEOUT |
| source | str | ✅ | 来源标识 |
| source_id | str | ⚠️ | SOURCE_ERROR 时可能为 null |
| revision | int | ⚠️ | SOURCE_ERROR 时可能为 null |
| incoming_raw_payload_hash | str / null | ⚠️ | SOURCE_ERROR 时 null |
| stored_raw_payload_hash | str / null | ⚠️ | DUPLICATE / MUTATION 时为已有 hash |
| ingestion_id | str / null | ⚠️ | SOURCE_ERROR 时 null |
| adapter_version | str | ✅ | |
| error | str / null | 可选 | 失败原因 |

### 6.3 SOURCE_EMPTY 事件的特殊语义

SOURCE_EMPTY observation：
- **属于** durable audit event（写入 raw_ingestion_audit.jsonl）。
- **不是** canonical raw record（不进入 raw_records.jsonl）。
- **不生成** raw_payload_hash（没有 payload 可 hash）。
- **不生成** ingestion_id（没有 canonical record 可标识）。
- restart 后 evidence **仍然存在**（JSONL 文件持久化）。
- replay 时**不会重新生成** canonical raw record（因为本来就没有 payload）。

### 6.4 不变量

- **INV-EVID-001**: 每一次 ingestion attempt 必须在 raw_ingestion_audit.jsonl 中有一条事件。
- **INV-EVID-002**: raw_ingestion_audit.jsonl 重启后必须完整恢复。
- **INV-EVID-003**: SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY 的 evidence 不得仅存在于进程内存。
- **INV-EVID-004**: SOURCE_EMPTY observation 不产生 canonical raw record、raw_payload_hash 或 ingestion_id。
- **INV-EVID-005**: source failure (SOURCE_ERROR) 和 parse failure (REJECTED) 在 audit 中的 outcome 字段必须可区分。

---

## 7. Missingness Contract

### 7.1 六类互斥分类（冻结）

| Class | event_type / 来源 | 定义 | 不属于该类别的情况 |
|-------|-----------------|------|-------------------|
| SOURCE_ERROR | adapter.fetch() 抛出异常 | source fetch/transport/auth/timeout 失败 | parse 失败 → PARSE_FAILURE |
| PARSE_FAILURE | adapter.parse() 抛出异常 | source 成功返回数据但解析失败 | fetch 失败 → SOURCE_ERROR |
| SOURCE_EMPTY | adapter.fetch() 返回 `[]` | source 请求成功且返回合法空结果 | fetch/parse 失败；contract 声明不需要数据 |
| EXPECTED_ABSENCE | EXPECTED_CONTRACT 声明 | entity/date 不要求存在数据 | contract 要求存在但实际缺失 |
| UNEXPECTED_MISSING | expected contract 要求存在但 actual 缺失 | expected_entities/dates 非空但 actual 为空 | contract 未要求 |
| UNRESOLVED_AVAILABILITY | available_time 为 None 或格式错误 | 无法确定 available_time | source 明确声明了 available_time |

### 7.2 Expected Absence vs Source Empty

```text
EXPECTED_ABSENCE
  = according to domain expectation, this entity/date pair
    is intentionally not required

SOURCE_EMPTY
  = the source returned zero observations for a request
```

**这两个概念完全分离。**

### 7.3 不变量

- **INV-MISS-001**: 六类互斥，任何 observation 只能属于一类。
- **INV-MISS-002**: SOURCE_EMPTY 不能被重新解释为 EXPECTED_ABSENCE。
- **INV-MISS-003**: PARSE_FAILURE 不能被重新解释为 SOURCE_ERROR。
- **INV-MISS-004**: EXPECTED_ABSENCE 不能由"实际没数据"自动推导。

---

## 8. Expected Contract

### 8.1 Authority 来源

EXPECTED_CONTRACT 是 expected universe 的唯一事实来源。它**独立于** actual
payload 定义。

**禁止**从 actual payload 推导 expected set。

**禁止**在 EXPECTED_CONTRACT 中包含测试控制字段
（expected_empty / broken_source / force_source_error / fixture_mode）。

### 8.2 结构

```python
EXPECTED_CONTRACT = {
    source_id: {
        "expected_entities": [str, ...],
        "expected_dates": [str, ...],
    }
}
```

### 8.3 不变量

- **INV-EXP-001**: EXPECTED_CONTRACT 在 audit 运行前定义。
- **INV-EXP-002**: ingestion 失败不改变 EXPECTED_CONTRACT。
- **INV-EXP-003**: 每个 source 在 EXPECTED_CONTRACT 中最多出现一次。
- **INV-EXP-004**: expected_pairs 由 expected_entities × expected_dates 的
  笛卡尔积构成。

---

## 9. Completeness Contract

### 9.1 集合定义

```text
E  = expected entity set         ← EXPECTED_CONTRACT[source].expected_entities
D  = expected date set           ← EXPECTED_CONTRACT[source].expected_dates
P  = expected pair set           ← {(e, d) for e in E for d in D}
A_entity = actual entity set     ← from successfully ingested records
A_date   = actual date set       ← from successfully ingested records
A_pair   = actual pair set       ← from successfully ingested records
```

### 9.2 计算公式

```text
missing_entities = E − A_entity
missing_dates    = D − A_date
missing_pairs    = P − A_pair

expected_count   = |P|
actual_count     = |P| − |missing_pairs|
coverage_ratio   = actual_count / expected_count
                   (1.0 if expected_count == 0)
```

### 9.3 状态定义

| 状态 | 条件 |
|------|------|
| 完整 | missing_entities = ∅ 且 missing_dates = ∅ 且 missing_pairs = ∅ |
| 部分完整 | 某些 entity/date/pair 缺失但非全部 |
| 完全缺失 | actual_entities = ∅ 且 expected_entities ≠ ∅ |
| 合法预期缺失 | EXPECTED_CONTRACT 声明 expected_absence = True |

### 9.4 不变量

- **INV-COMP-001**: coverage_ratio 由 |P| 和 |P ∩ A| 计算，不得手工填写。
- **INV-COMP-002**: missing data **不得**被 forward-fill / 默认值填充 / 静默删除。
- **INV-COMP-003**: expected set 独立于 actual ingestion 结果。
- **INV-COMP-004**: entity / date / pair 三种粒度的 missing 集合必须分别报告。
- **INV-COMP-005**: expected contract 中明确声明 expected_absence 的 entity/date
  **不计入** coverage denominator。

---

## 10. Timestamp Quality Contract

### 10.1 检查项

| Check | 条件 | 分类 |
|-------|------|------|
| {field}_malformed | 字段无法解析为 ISO 8601 | VIOLATION |
| timezone_missing | 字段不含 timezone | VIOLATION |
| ingested_before_available | ingested_at < available_time | VIOLATION |
| available_before_event | available_time < event_time（当 contract 声明 available_after_event） | VIOLATION |
| available_vs_event_unprovable | source contract 无法证明顺序 | UNKNOWN |
| {field}_in_future | 字段 > reference_time | VIOLATION |

### 10.2 不变量

- **INV-TS-001**: 三个时间字段语义分离（event_time / available_time / ingested_at）。
- **INV-TS-002**: 不得用 event_time 替代 available_time。
- **INV-TS-003**: 不得用 ingested_at 替代 available_time。
- **INV-TS-004**: source contract 无法证明顺序时报告 UNKNOWN，不猜测。

---

## 11. Revision Integrity Contract

### 11.1 REV-001: Revision sequence

revision 不要求连续（允许 gap）。gap 被检测并报告为 ANOMALY 但不影响 quality status。

### 11.2 REV-002: Duplicate revision

```text
duplicate revision
  = same (source, source_id, revision) + same canonical JSON
```

如果 canonical JSON 不同 → same_revision_different_payload ANOMALY。

### 11.3 REV-003: Payload mutation

```text
same (source, source_id, revision) + different canonical JSON
  = RAW_MUTATION_DETECTED
```

P14-B RawStore 已负责检测。P14-C 消费检测结果并统计。

### 11.4 REV-004: available_time regression

如果 revision N+1 的 available_time 早于 revision N：
- classification = revision_available_time_regression
- severity = ANOMALY
- research handling = 报告但保留，不删除

### 11.5 REV-005: PIT visibility

revision anomaly 不得破坏 P14-A `available_time <= decision_time`。
P14-A 仍然是 PIT authority。

---

## 12. Duplicate / Conflict Contract

### 12.1 Duplicate

```text
duplicate = same (source, source_id) + same canonical JSON
```

由 RawStore 幂等 put 自动处理。audit event 记录 outcome=DUPLICATE。

### 12.2 Payload mutation

```text
same (source, source_id, revision) + different canonical JSON
  = RAW_MUTATION_DETECTED
```

P14-B RawStore 已负责检测和报告。

### 12.3 Cross-source conflict

```text
same (entity_id, event_time, unit, currency)
+ >= 2 sources
+ >= 2 distinct non-null values
  = CONFLICT
```

P14-A `detect_conflicts` 已负责检测。P14-C 消费检测结果并统计。

### 12.4 不变量

- **INV-DUP-001**: 不得自动选择 source winner。
- **INV-DUP-002**: 不得自动平均。
- **INV-DUP-003**: 不得静默 resolution。
- **INV-DUP-004**: 不同 source 的 value 都必须保留。

---

## 13. Freshness Contract

### 13.1 唯一来源

P14-A `freshness_status(record, decision_time, policies)` 是 freshness 的
唯一判断函数。P14-C 不定义第二套 freshness policy 或 threshold。

### 13.2 报告键

P14-C 将 P14-A 的小写状态（fresh/stale/unknown/missing_policy）规范化为
大写（FRESH/STALE/UNKNOWN/MISSING_POLICY），并追加 UNRESOLVED
（available_time 缺失）。

### 13.3 不变量

- **INV-FRESH-001**: freshness 判断必须调用 P14-A `freshness_status`。
- **INV-FRESH-002**: 不得硬编码 stale 计数。
- **INV-FRESH-003**: freshness policy 是 infrastructure 配置，不是 alpha threshold。
- **INV-FRESH-004**: FRESH / STALE / UNRESOLVED 三种证据必须在 audit 中产生。

---

## 14. Reconciliation Contract

### 14.1 必须保留的字段

每个 reconciliation group 中的每个 contributing source 必须保留：

```text
source, source_id, value, event_time, available_time, ingested_at,
ingestion_id, raw_payload_hash, provenance
```

每个 group 必须保留：

```text
difference, relative_difference, policy_id, policy_version, status
```

### 14.2 不变量

- **INV-RECON-001**: 不得自动选择 source winner。
- **INV-RECON-002**: 不得自动平均。
- **INV-RECON-003**: 不得静默 resolution。
- **INV-RECON-004**: 不同 source 的 value 都必须保留。
- **INV-RECON-005**: tolerance policy 必须版本化（policy_id + policy_version）。

---

## 15. Provenance Contract

### 15.1 Record Provenance（Type A）

适用于：canonical raw record, accepted record, rejected record with payload,
revision, reconciliation record。

```text
source, source_id, raw_payload_hash, ingestion_id, adapter_version,
event_time, available_time, ingested_at
```

引用 P14-A provenance contract：`astock_v2.information.provenance`。

### 15.2 Observation / Completeness Provenance（Type B）

适用于：SOURCE_EMPTY, SOURCE_ERROR, PARSE_FAILURE, EXPECTED_ABSENCE,
UNEXPECTED_MISSING, missing entity/date/pair。

```text
source, source_id, observation_type, observed_at, adapter_version,
expected_contract_id, entity_date_pair_scope, evidence_reference
```

**不应**强制要求不存在的 raw_payload_hash 或 canonical record id。

### 15.3 不变量

- **INV-PROV-A-001**: Record provenance 必须包含 raw_payload_hash。
- **INV-PROV-B-001**: Observation provenance 不得包含 raw_payload_hash
  （该字段对 observation 无意义）。

---

## 16. Source Health Contract

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

---

## 17. Nine Quality Dimensions（冻结）

| # | dimension_id | 名称 | 输入 evidence | status domain |
|---|-------------|------|--------------|--------------|
| 1 | completeness | expected vs actual entity/date coverage | completeness.json | PASS / WARN / FAIL |
| 2 | validity | provenance / content validity | quality_report validity dim | PASS / WARN / FAIL |
| 3 | timeliness | timestamp ordering / freshness | quality_report timeliness dim | PASS / WARN / FAIL |
| 4 | freshness | P14-A freshness_status per record | quality_report freshness dim | PASS / WARN / FAIL |
| 5 | consistency | cross-source value consistency | reconciliation.json | PASS / WARN / FAIL |
| 6 | revision_integrity | revision gap / duplicate / regression | quality_report rev dim | PASS / WARN / FAIL |
| 7 | provenance_integrity | provenance completeness | quality_report prov dim | PASS / WARN / FAIL |
| 8 | pit_admissibility | PIT counts per record | quality_report pit dim | PASS / WARN / FAIL |
| 9 | source_health | per-source ingestion health | source_health.json | PASS / WARN / FAIL |

每个 dimension 的 schema：

```json
{
  "dimension_id": "string",
  "status": "PASS | WARN | FAIL | UNRESOLVED",
  "reasons": ["string", ...],
  "metrics": { "key": numeric_or_string },
  "evidence": [ { ... }, ... ]
}
```

---

## 18. Quality Report Contract

最终 `quality_report.json` 必须包含：

```json
{
  "schema_version": "...",
  "decision_time": "...",
  "dimensions": {
    "completeness": { "status": "...", "reasons": [...], "metrics": {...}, "evidence": [...] },
    "validity": { ... },
    "timeliness": { ... },
    "freshness": { ... },
    "consistency": { ... },
    "revision_integrity": { ... },
    "provenance_integrity": { ... },
    "pit_admissibility": { ... },
    "source_health": { ... }
  }
}
```

---

## 19. Determinism Contract

- **INV-DET-001**: 相同输入 → byte-identical 输出（从两个独立空目录运行）。
- **INV-DET-002**: 禁止 runtime timestamp / random UUID / unordered iteration / machine path 进入 deterministic output。
- **INV-DET-003**: manifest 不含动态 timestamp。

---

## 20. Restart / Replay Contract

- **INV-RR-001**: process restart 后 durable audit file 必须完整恢复。
- **INV-RR-002**: 重复 replay 同一 payload 不得产生新的 canonical record。
- **INV-RR-003**: replay 的 audit event 必须标记为 DUPLICATE。

---

## 21. Research Boundary Contract

- RESEARCH_END = 2026-09-22, VIRGIN_START = 2026-09-23。
- P14-C fixture 日期必须 < 2026-09-23。
- P13-U virgin protection 不得削弱。
- P13-T = STOPPED / NOT EXECUTED。
- P14-C 不得使用 virgin zone 调参 / 做 calibration / 做 factor selection /
  做 policy selection / 将 P13-R validation 重新标记为 holdout。

## 22. Invariant Registry

全部 INV-* 编号在本文件 §6-§21 中定义，此处不再重复列举。
每个 INV-* 在 Acceptance Matrix 中至少对应一行。
