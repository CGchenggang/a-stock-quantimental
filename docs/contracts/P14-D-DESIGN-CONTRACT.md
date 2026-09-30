# P14-D Design Contract — PIT-safe Research Information Query Layer

> 本文档是 P14-D（PIT-safe Research Information Query Layer）的行为契约。
> 建立在已独立验收的 P14-A/B/C 之上；不回退、不重构、不重新定义任何
> P14-C 已冻结语义。
>
> 状态：DRAFT — awaiting independent contract review
>
> 修订历史：
> v1: 初始版本（P14-D 实现前）

---

## 1. Purpose

P14-D 回答一个问题：研究系统如何在指定 as-of 时间点查询"当时已经可获得
的信息"。查询结果必须可复现、可审计、可追溯到具体 source record，且
在任意历史 as-of 时间点都被证明只使用了当时可获得的信息。

## 2. Scope

### 2.1 P14-D 负责

| 职责 | 说明 |
|------|------|
| information retrieval | 从 research information records 中按 scope 检索 |
| PIT filtering | `available_time <= as_of` 可见性判定（P14-A authority） |
| version selection | 同一 lineage 多版本的确定性选择 |
| provenance | 每条结果可追溯到 source record |
| deterministic ordering | 结果的规范化排序与规范化序列化 |
| exclusion accounting | 不可见记录的不可见原因分类 |

### 2.2 P14-D 不负责

factor scoring, prediction, ranking, alpha, recommendation, policy,
portfolio, trading, LLM decision, stock selection。查询层不得自动产生
任何股票推荐（P14D-010）。

## 3. Authority（不重新定义）

### 3.1 P14-A remains authoritative for

PIT 判定（`available_time <= as_of`，含边界相等）、`available_time`
语义、`visible_revisions` 的版本选择语义、provenance 基础语义、
`RawInformationRecord` 数据模型、freshness policy。

### 3.2 P14-B remains authoritative for

raw immutability、`raw_records.jsonl` / `raw_ingestion_audit.jsonl`、
`ingestion_id`、`raw_payload_hash`、adapter metadata。

### 3.3 P14-C remains authoritative for

异常分类体系（SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY /
EXPECTED_ABSENCE / UNEXPECTED_MISSING / UNRESOLVED_AVAILABILITY）、
completeness、reconciliation、source health。P14-D 复用
`UNRESOLVED_AVAILABILITY`，不另造第二套异常语义。

### 3.4 P13-U remains authoritative for

research/virgin 边界（`research_end = 2026-09-22`、
`virgin_start = 2026-09-23`）与 `assert_research_zone` fail-fast 守卫。
P14-D 的查询入口对 `as_of >= virgin_start` 必须 raise。

## 4. Terminology

| 术语 | 定义 |
|------|------|
| Research Query | 一次研究信息查询：entity + information_type + as_of（+ 可选 source scope） |
| as_of | 查询的决策时间点；只有 `available_time <= as_of` 的信息可见 |
| lineage | 同一 `(source, source_id)` 的修订序列 |
| visible record | 通过 PIT 判定且属于查询 scope 的记录 |
| exclusion | 未进入结果的记录及其不可见原因 |
| information_type | 记录的 `entity_type` 字段（精确匹配） |

## 5. Query Model（冻结）

```python
ResearchQuery:
    entity           # 必填；匹配 record.entity_id（精确）
    information_type # 必填；匹配 record.entity_type（精确）
    as_of            # 必填；带时区的 ISO-8601 时间戳
    source           # 可选；提供时匹配 record.source（精确），缺省不限
```

不增加其他字段。任何字段为空、`as_of` 缺少时区 → 查询构造失败。

## 6. PIT Core（冻结）

```text
visible(record, as_of)  <=>  available_time <= as_of     （含边界相等）
```

- `event_time` **绝不**参与可见性判定（P14D-003）。
- `event_time != available_time`：信息所属期间与可获得时间是两个正交
  维度（例：财务报告期间 2025-12-31，披露时间 2026-04-30；as_of =
  2026-03-01 时该信息不可见）。
- `available_time` 为空/不可解析的记录（P14-C `UNRESOLVED_AVAILABILITY`）
  永不可见。

## 7. Exclusion Reasons（冻结，复用 P14-C 分类）

```text
NOT_YET_AVAILABLE         available_time > as_of（含 event_time 无论如何）
OUTSIDE_AS_OF             scope 不匹配（entity / information_type / source）
UNRESOLVED_AVAILABILITY   available_time 缺失（复用 P14-C 分类，不新造）
```

每条未进入结果的记录必须能归入且仅归入一类（P14D-002/008）。

## 8. Version Selection / Restatement（冻结）

- 同一 lineage（`(source, source_id)`）内多个 admissible 版本：选择
  **最大 revision** 的版本（P14-A `visible_revisions` authority；
  revision 相同则取最早 `available_time`，再按 canonical json，
  全程确定性，P14D-004）。
- Restatement：original `available_time = T1`，restated
  `available_time = T2`。查询 `as_of < T2` **不得**返回 restated
  版本；`as_of >= T2` 才可见（P14D-005）。
- 不同 lineage（不同 source_id）是不同信息事件，各自独立进入结果。

## 9. Result Contract（冻结）

每个查询结果包含：

```text
query          查询本身的规范化回显（entity / information_type / as_of / source）
records        可见记录列表，每条含 provenance（见 §10）
excluded       未进入结果的记录及原因（§7）
counts         {visible, excluded, examined}
result_id      规范化序列化的 SHA-256
```

Provenance（每条 record，全部服务于 PIT/audit/reproducibility，
不无限增加字段）：

```text
source, source_record_id, entity_id, information_type,
event_time, available_time, revision, ingested_at,
adapter_version, raw_payload_hash, ingestion_id
```

确定性（P14D-006）：相同 (records, query) → 相同 canonical result
（byte-identical）。排序键冻结：
`(source, source_id, available_time, revision, canonical_json)`。
禁止 runtime timestamp / UUID / random / machine path / 环境相关顺序。

## 10. Boundary（冻结）

- 查询入口对 `as_of >= virgin_start` 必须 fail-fast raise（P13-U
  `assert_research_zone` 守卫，冻结常量 `VIRGIN_START = 2026-09-23`；
  P14D-009）。
- 测试 fixture 需要未来时间必须使用合成日期（如 `2099-01-01`），
  不得使用真实 virgin-zone 数据。

## 11. Anti-Cheat（冻结）

生产查询代码不得包含：`fixture_mode`、`expected_result_override`、
`golden_override`、`test_only`、`skip_validation`、`force_visible`、
`force_hidden`、`if running_under_test` 分支；不得通过 fixture 名、
golden id、环境变量或测试参数改变真实 PIT 行为。

## 12. Invariant Registry

全部 P14D-001..010 定义于本文件 §5-§11，Acceptance Matrix 每条至少
一行，Golden fixtures 覆盖见 Matrix。

- **P14D-001**: 正常 PIT 查询：admissible 记录按 scope 进入结果。
- **P14D-002**: `available_time > as_of` 的记录不可见，原因
  NOT_YET_AVAILABLE。
- **P14D-003**: `event_time <= as_of` 但 `available_time > as_of` 的
  信息仍不可见——event_time 不参与可见性。
- **P14D-004**: 同一 lineage 多个 admissible 版本时，确定性选择唯一
  版本（最大 revision）。
- **P14D-005**: restatement 在 `as_of < T2` 时不可见。
- **P14D-006**: 相同输入重复执行得到 byte-identical 的规范化结果。
- **P14D-007**: 每条结果记录携带完整 provenance，可追溯到 source record。
- **P14D-008**: scope 外信息不泄露进结果，原因 OUTSIDE_AS_OF。
- **P14D-009**: virgin-zone 决策时间被守卫拒绝；测试输入不消费真实
  virgin 数据。
- **P14D-010**: 查询层不产生 prediction / recommendation / trading
  decision（仅 information retrieval）。
