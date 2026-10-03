# P14-E Production Implementation Design Package

> STATUS: DESIGN READY — PRODUCTION IMPLEMENTATION NOT AUTHORIZED
>
> 本文是基于已独立接受的 P14-E Design Contract v1.1、Production Design
> Contract v1.1、Implementation Contract v1.0 以及 P14-E-006 Golden/Harness
> 形成的生产实现设计包。下一阶段 Agent 按本设计直接实施，无需重新解释
> 上游 Contract。
>
> 上游权威链：
> P14-E Design Contract v1.1 (17afd2d)
> → P14-E-004 Production Contract v1.1 (a72502f)
> → P14-E-005 Implementation Contract v1.0 (70634cbe)
> → P14-E-006 Golden/Harness (17afd2d, accepted f553b22)
> → 本设计包

---

## 1. Architecture Overview

### 1.1 Authority Chain（不可重定义）

```text
P14-B RawStore          raw evidence 唯一权威（append-only JSONL）
        ↓ 只读
P14-A models/projection  RawIngestRecord → RawInformationRecord
        ↓ 只读
P14-D run_query          PIT visibility + version selection 唯一权威
        ↓ 只读（resolved result）
P14-E Evidence Runtime   evidence 构造 / bundle 持久化 / reverse trace
        ↓
Consumer
```

### 1.2 模块布局

```text
src/astock_v2/information/evidence.py       Evidence / EvidenceBundle 构造
src/astock_v2/information/evidence_store.py JSONL 持久化 + reload 验证
```

仅这两个新文件；不修改既有 P14-A/B/C/D 模块。

### 1.3 组件图

```text
┌─────────────────────────────────────────────────┐
│                  Consumer                        │
└────────────────────┬────────────────────────────┘
                     │ query_evidence(bundle_id)
                     ▼
┌─────────────────────────────────────────────────┐
│           EvidenceStore (evidence_store.py)      │
│  append-only JSONL / idempotent / reload         │
└────────────────────┬────────────────────────────┘
                     │ bundle_id lookup
                     ▼
┌─────────────────────────────────────────────────┐
│        Evidence Bundle Manager (evidence.py)     │
│  create_bundle / freeze_bundle / validate_bundle │
└──────┬──────────────────┬───────────────────────┘
       │                  │
       ▼                  ▼
┌──────────────┐  ┌───────────────────────────────┐
│ P14-D result │  │  P14-B RawIngestRecord         │
│ (resolved)   │  │  (identity primitives)         │
└──────────────┘  └───────────────────────────────┘
```

---

## 2. Evidence Identity（继承已接受 P14-E Contract §4）

### 2.1 Identity Fields（参与 evidence_id）

```text
source, source_id, revision, event_time,
available_time, adapter_version, raw_payload_hash, ingestion_id
```

### 2.2 evidence_id 公式

```python
evidence_id = hashlib.sha256(
    json.dumps(identity_fields_dict, sort_keys=True,
               ensure_ascii=False, separators=(",", ":"))
    .encode("utf-8")
).hexdigest()
```

### 2.3 ingested_at

Audit-only：不参与 evidence_id，不参与 PIT 可见性。已存储记录的
ingested_at 不可变（P14-B immutability + DUPLICATE 语义）。

### 2.4 Identity Classes

| 类别 | 字段 |
|------|------|
| Evidence Identity | 8 字段（§2.1） |
| Content Identity | raw_payload 的语义内容（仅以 raw_payload_hash 表示） |
| Provenance Identity | 全 11 字段（含 audit-only ingested_at） |
| Ingestion Identity | P14-B ingestion_id 公式 |

---

## 3. Evidence Bundle Schema（继承 Production Contract §9 / Implementation §6）

```json
{
  "schema_version": "p14e-evidence-bundle-1",
  "query": {
    "entity": "...", "information_type": "...",
    "as_of": "...", "source": null
  },
  "as_of": "...",
  "result_id": "sha256...",
  "evidence": [
    {
      "source": "...", "source_id": "...",
      "revision": 0, "event_time": "...",
      "available_time": "...", "adapter_version": "...",
      "raw_payload_hash": "...", "ingestion_id": "...",
      "entity_id": "...", "information_type": "...",
      "ingested_at": "...",
      "evidence_id": "sha256...",
      "selection_reason": "SELECTED_HIGHEST_REVISION"
    }
  ],
  "candidate_trace": [
    {
      "source": "...", "source_id": "...", "revision": 1,
      "available_time": "...", "raw_payload_hash": "...",
      "ingested_at": "...",
      "rejection_reason": "REJECTED_LOWER_REVISION"
    }
  ],
  "exclusions": [
    {"source": "...", "source_id": "...",
     "reason": "NOT_YET_AVAILABLE", "available_time": "..."}
  ],
  "counts": {
    "evidence": 0, "candidates": 0, "exclusions": 0, "examined": 0
  },
  "bundle_id": "sha256..."
}
```

---

## 4. Production API（六接口）

### 4.1 create_bundle

```python
def create_bundle(
    query_result: dict,           # P14-D run_query 的已解析输出
    authoritative_evidence_records: list[RawIngestRecord],
) -> dict:
```

- Authority: P14-D 已解析 result + P14-B identity
- Side effect: 无（内存构造）
- Failure layers: `input_validation`（provenance 不完整）；`authority_violation`（非 resolved result）；`identity_failure`（mutation 检出）
- MUST NOT: 调用 `run_query`、`is_admissible`、`visible_revisions`、`select_lineage` 或任何 PIT/选择逻辑

### 4.2 freeze_bundle

```python
def freeze_bundle(bundle: dict) -> dict:
```

- 返回 canonical 冻结副本；冻结后任何内容变更可检测

### 4.3 store_bundle

```python
def store_bundle(bundle: dict, path: Path) -> bool:
```

- Side effect: append 一行到 `evidence_bundles.jsonl`
- 同 bundle_id 重复 append → 返回 False（幂等拒绝）
- Failures: `storage_failure`

### 4.4 query_evidence

```python
def query_evidence(path: Path, bundle_id: str) -> dict:
```

- 只读；按 bundle_id 查找；不改状态
- Failures: `storage_failure`（未找到）

### 4.5 reverse_trace

```python
def reverse_trace(evidence: dict, raw_rows: list[dict]) -> dict:
```

- 解析 `(ingestion_id, raw_payload_hash)` → 权威 raw row
- Failures: FOUR-CLASS taxonomy（NOT_FOUND / AMBIGUOUS / IDENTITY_MISMATCH / CORRUPTED）

### 4.6 validate_bundle

```python
def validate_bundle(bundle: dict, result: dict) -> None:
```

- mapping_key 1:1 校验；result_id 链接校验
- Failures: `input_validation`

---

## 5. Data Flow

```text
P14-D run_query(records, query)
        ↓ resolved result
P14-E create_bundle(query_result, authoritative_records)
        ↓ EvidenceBundle (CREATE)
P14-E freeze_bundle(bundle)
        ↓ EvidenceBundle (FROZEN, canonical bytes locked)
P14-E store_bundle(frozen, path)
        ↓ EvidenceBundle (STORED in evidence_bundles.jsonl)
Consumer query_evidence(path, bundle_id)
        ↓ EvidenceBundle (read-only view)
Consumer reverse_trace(evidence, raw_rows)
        ↓ authoritative raw record
```

---

## 6. Persistence Design

### 6.1 File

```text
路径:      调用方提供的 Path（与 P14-B 审计文件同目录约定）
格式:      JSONL；每行一个完整 bundle（canonical serialization）
编码:      UTF-8；newline="\n"
```

### 6.2 Write Semantics

```text
append-only: 每次调用追加一行；禁止就地修改
原子性:      单行写入（newline 终止）；进程崩溃不会产生部分行
幂等:        同 bundle_id 重复 append → 拒绝（返回 False），不追加
```

### 6.3 Read/Reload Semantics

```text
逐行解析:   json.loads(line)
校验 1:     重算 bundle_id == 行内 bundle_id
校验 2:     每 Evidence 的 (ingestion_id, raw_payload_hash) 在
            P14-B raw_records.jsonl 中存在且匹配
任一失败:   raise → 无部分返回
```

### 6.4 Duplicate / Conflict

```text
同 bundle_id 重复写入 → 拒绝（幂等）
同 (source, source_id, revision) 异 raw_payload_hash → 构造期 fail-fast
  （P14-B RAW_MUTATION_DETECTED 为权威检测者，生产层消费并拒绝）
```

---

## 7. Failure Semantics

### 7.1 Failure Taxonomy（六层）

| 层 | 错误 | 触发条件 | Retryable | Audit |
|----|------|----------|-----------|-------|
| input_validation | provenance/schema/枚举不合法 | CREATE/VALIDATE 检查 | 否 | 是 |
| authority_violation | 非 resolved result / 越权操作 | 构造/调用检查 | 否 | 是 |
| pit_violation | as_of >= virgin_start | P13-U 守卫 | 否 | 是 |
| identity_failure | evidence_id/bundle_id 重算不一致 | 构造或 reload | 否 | 是 |
| storage_failure | 文件 I/O / 幂等冲突 / 损坏行 | 写/读操作 | 视情况 | 是 |
| trace_failure | reverse trace FOUR-CLASS | 解析失败 | 否 | 是 |

### 7.2 Failure Response

```text
构造期失败 → raise（无部分 bundle，无持久化）
reload 期失败 → raise（无部分返回）
六层均 fail-fast，禁止吞错继续
```

---

## 8. PIT Boundary（继承 P14-D，P14E-P-006）

```text
visible ⇔ available_time <= as_of_time（含边界相等）
```

- event_time / ingested_at / query 处理时间：不参与可见性
- as_of >= virgin_start (2026-09-23) → P13-U 守卫 fail-fast
- research_end = 2026-09-22（冻结常量）

---

## 9. Concurrency / Idempotency

| 场景 | 处理 |
|------|------|
| 同 bundle_id 重复 append | 拒绝（返回 False）|
| 同 evidence_id 重复构造 | 确定性——同输入同 ID，天然幂等 |
| 并发 append | 单进程假设（与 P14-B 一致）；无锁 |
| 部分写入（崩溃） | 下一 reload 时 JSON 解析失败 → fail-fast |
| 重复提交同一 bundle | 幂等拒绝；不产生第二行 |
| retry after failure | 无部分状态 → 可安全重试 |

---

## 10. Integrity / Tamper Detection

| 篡改 | 检测点 | 结果 |
|------|--------|------|
| Evidence 字段变更 | bundle_id 重算不匹配 | reload fail-fast |
| ingestion_id 篡改 | reverse trace NOT_FOUND | fail-fast |
| raw_payload_hash 篡改 | reverse trace NOT_FOUND | fail-fast |
| mapping 篡改 | validate_bundle 集合不等 | fail-fast |
| as_of 篡改 | bundle_id 变化 | 检出 |
| 排序篡改 | canonical 重算不等 | 检出 |

---

## 11. Observability

```text
audit 流:    每次生命周期迁移 / 失败 → 一条 audit 记录
trace IDs:   bundle_id / evidence_id / result_id / ingestion_id
日志约定:    结构化 JSON；不含 raw payload 内容
敏感数据:    raw payload 不进入日志（仅 hash）
```

---

## 12. Test Matrix（Contract → Golden → Production）

| Contract ID | Golden | Production Test |
|-------------|--------|-----------------|
| P14E-P-001..003 | G-001..G-003 | unit: identity/boundary |
| P14E-P-004..008 | G-004..G-007 | unit: trace/lifecycle |
| P14E-P-009..012 | G-008..G-010 | unit: persistence/mutation |
| P14E-P-013..015 | G-009/G-012 | unit: reload/boundary |
| P14E-P-016..017 | 源扫描 | source scan |
| P14E-P-018..019 | G-009/G-012 | unit: determinism |
| P14E-I-001..009 | IG-101..107 | unit: six components |
| P14E-I-010..017 | IG-101..103 | unit: lifecycle/audit |
| P14E-I-018..024 | IG-102/106/107 | unit: trace/failure/API |
| P14E-I-M-003 | IG-104 | negative: authority |
| P14E-I-M-014 | IG-102 | negative: four-class |
| P14E-I-M-015 | IG-105 | negative: read-only |

---

## 13. CI Gate

```yaml
# 追加到 .github/workflows/tests.yml
- name: P14-E Production tests
  run: python -m pytest -q -ra tests/test_p14e_production.py
```

（由 Production Implementation 阶段添加；本设计阶段不修改 workflow。）

---

## 14. Production Task Breakdown

| Task ID | Purpose | Files | Dependencies | Acceptance |
|---------|---------|-------|--------------|------------|
| P14-E-PI-001 | Evidence dataclass + evidence_id | evidence.py | P14-B RawIngestRecord | unit tests pass |
| P14-E-PI-002 | create_bundle (resolved-result consumption) | evidence.py | PI-001 | Golden IG fixtures pass |
| P14-E-PI-003 | candidate_trace + selection_reason | evidence.py | PI-002 | Golden IG-101 pass |
| P14-E-PI-004 | EvidenceBundle + freeze | evidence.py | PI-003 | freeze immutability |
| P14-E-PI-005 | EvidenceStore (append/reload/verify) | evidence_store.py | PI-004 | Golden IG-103/105 pass |
| P14-E-PI-006 | Reverse trace (FOUR-CLASS) | evidence.py | PI-001 | Golden IG-102 pass |
| P14-E-PI-007 | Failure model (six layers) | evidence.py | PI-001..006 | all layers raise |
| P14-E-PI-008 | Integration (P14-D handoff) | evidence.py | PI-002..007 | full lifecycle pass |
| P14-E-PI-009 | Production tests | tests/ | PI-001..008 | all pass |
| P14-E-PI-010 | CI integration | workflow | PI-009 | exact-head CI green |
| P14-E-PI-011 | Documentation | docs/ | all | PROJECT_STATUS updated |
| P14-E-PI-012 | Acceptance package | docs/ | all | ready for review |

---

## 15. Compatibility / Migration

| Current | Target | Action |
|---------|--------|--------|
| P14-B RawStore (raw_records.jsonl) | P14-E Evidence identity source | reuse (read-only) |
| P14-D run_query result | P14-E create_bundle input | integrate |
| P14-A to_information_record | P14-E project step | reuse (read-only) |
| No persistence | evidence_bundles.jsonl | new (P14-E-PI-005) |
| No reverse trace | reverse_trace API | new (P14-E-PI-006) |
| P14-A provenance.py | P14-E Type A provenance | reconcile (field names) |

无 schema migration（新建 JSONL 文件，无旧数据需迁移）。

---

## 16. Definition of Ready（本文档已满足）

✅ Contract: P14-E Design Contract + Production Contract + Implementation Contract 全部独立验收
✅ Architecture: P14-D authority 边界明确；P14-E 职责明确；无重复 PIT/选择逻辑
✅ Data: Evidence schema / Bundle schema / identity / provenance 全部定义
✅ Integrity: P14-B authority chain / reload authority / append-only / mutation detection 全部定义
✅ Failure: 六层失败分类映射完成；负路径映射完成
✅ Testing: Golden → Production test 映射完成
✅ CI: exact-head gate 已定义
✅ Scope: 生产实现尚未执行；P13-T/U 未触碰；P14-F 未触碰
