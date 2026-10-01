# P14-E Design Contract — Research Information Evidence / Provenance Layer

> STATUS: DRAFT
>
> **P14-E is not implementation-authorized.**
>
> 本文档是 P14-E（Research Information Evidence / Provenance Layer）的
> 行为契约草案。P14-E 建立在已独立验收的 P14-A/B/C/D 之上，回答一个问题：
> 一次 P14-D 查询结果由哪些原始信息组成、每条信息来自哪里、哪个版本被
> 选中、为什么被选中、以及能否从最终 evidence 反向追溯到原始记录。
>
> 修订历史：
> v1: Contract Draft（P14-E-001 任务；未经独立 Contract Acceptance，
>     本文件不得作为实现依据）
> v1.1: REPAIR-001 语义修复——§6.3 重写（方案 A：Bundle 只证明其自身
>       as_of 的版本选择；跨 as_of 必须新查询/新 Bundle，删除"任意
>       as_of 可重推"）；§4 重构（Identity/Content/Audit-only 字段
>       分类，消除 §4.2 与 §13 的 ingested_at 歧义；同 payload 异
>       ingestion event → 相同 evidence_id）

---

## 1. Purpose

P14-D 已经能够返回 PIT-safe 的规范化查询结果（`result_id`）。P14-E 在其
之上建立 Evidence / Provenance 层，使每个结果都能回答：

```text
这个结果由哪些原始信息组成？
每条信息来自哪个 source / source_id / revision？
原始 payload 是什么？什么时候发生？什么时候可见？
哪个版本被选中？为什么？在别的 as_of 下会不会选别的版本？
最终结果由哪些 evidence 支撑？能否反向追溯到原始记录？
```

P14-E 输出 Evidence / Provenance / Traceability / Auditability；绝不输出
Decision / Recommendation / Prediction（P14E-016）。

## 2. Authority（不重新定义）

### 2.1 P14-A remains authoritative for

`RawInformationRecord` 数据模型与 `canonical_json`、`record_id`、PIT
admissibility（`available_time <= as_of`，含边界相等）、
`visible_revisions` 的版本选择语义（最大 revision → 同 revision 最早
available_time → 最小 canonical_json，P14-D-REPAIR-001 修正后冻结）、
provenance 基础字段。

### 2.2 P14-B remains authoritative for

raw immutability、`raw_records.jsonl` / `raw_ingestion_audit.jsonl`、
`canonical_payload_hash`、`ingestion_id`（= sha256(source | source_id |
revision | raw_payload_hash | adapter_version)）、`RAW_MUTATION_DETECTED`
检出。P14-E 复用这些身份原语，不重新实现。

### 2.3 P14-C remains authoritative for

异常分类体系（SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY /
EXPECTED_ABSENCE / UNEXPECTED_MISSING / UNRESOLVED_AVAILABILITY）。
P14-E 不把这些状态合并为任何泛化的 "missing"（P14E-010）。

### 2.4 P14-D remains authoritative for

`ResearchQuery`（entity / information_type / as_of / 可选 source）、
`run_query` 结果契约（query 回显 / records / excluded / counts /
`result_id`）、exclusion 分类（NOT_YET_AVAILABLE / OUTSIDE_AS_OF /
UNRESOLVED_AVAILABILITY）、canonical 排序键
`(source, source_record_id, available_time, revision, canonical_json)`、
virgin-zone 入口守卫。P14-E 消费 P14-D 结果，不修改 P14-D 冻结语义。

### 2.5 P13-U remains authoritative for

`research_end = 2026-09-22`、`virgin_start = 2026-09-23`、
`assert_research_zone` fail-fast 守卫（P14E-015）。

## 3. Terminology

| 术语 | 定义 |
|------|------|
| Evidence | 一条可见记录的可审计投影：身份字段 + 完整 provenance + payload 身份（§4） |
| Evidence Bundle | 一次查询的完整证据集合：query 身份 + result 链接 + evidence[] + 候选/落选 trace + exclusions（§7） |
| evidence_id | Evidence 的内容寻址确定性 ID（§4.2） |
| bundle_id | Evidence Bundle 的内容寻址确定性 ID（§8） |
| candidate trace | 同 lineage 中参与版本选择但未胜出的记录及其落选原因（§6） |
| Lineage | 同一 `(source, source_id)` 的修订序列 |

## 4. Evidence Identity（P14E-001 / P14E-002）

### 4.1 字段分类（REPAIR-001 冻结）

| 类别 | 字段 | 参与 evidence_id |
|------|------|------------------|
| Identity fields | source, source_id, revision, event_time, available_time, adapter_version, raw_payload_hash, ingestion_id | **是** |
| Content fields | raw payload 的语义内容——仅以其内容地址 `raw_payload_hash` 表示；payload 本体留在 P14-B `raw_records.jsonl`，不复制进 Evidence | 经 raw_payload_hash 参与 |
| Audit-only fields | ingested_at（本系统入库时间） | **否**（仅审计） |

### 4.2 evidence_id

```text
evidence_id = sha256(canonical_json(全部 Identity fields))
```

冻结性质（P14E-001）：

1. 确定性：相同 Identity fields → 相同 evidence_id。
2. 内容寻址：`raw_payload_hash` 参与 ID，payload 语义内容变化 → ID 变化。
3. 与插入顺序无关、与 Python 对象序无关、与运行环境无关。
4. canonical serialization 使用 sort_keys + 紧凑分隔符（与 P14-D
   `result_id` 同一序列化规范）。
5. **相同 raw payload 在不同 ingestion event 下得到相同 evidence_id**：
   P14-B 的 `ingestion_id` = sha256(source | source_id | revision |
   raw_payload_hash | adapter_version) 确定且不含 ingested_at；RawStore
   幂等——同键同 payload 的后续 attempt 为 DUPLICATE，仅首次 ACCEPTED
   成为 stored record。因此不存在"同 payload 分叉出多个 evidence"。
6. 与 P14-B 的关系：`raw_payload_hash` 与 `ingestion_id` 原样取自 P14-B
   权威值；P14-E 不另算第二套 payload hash，不重定义 P14-B 身份语义。
7. `ingested_at` 属 Audit-only：它随 Evidence 携带供审计（本系统何时
   入库），不参与 evidence_id；已存储记录的 ingested_at 不可能变化
   （P14-B immutability + DUPLICATE 语义），故 ID 在重放间稳定。

### 4.3 Provenance 完整性（P14E-002）

每个 Evidence 必须携带 §4.1 全部三类字段（含 Audit-only 的
`ingested_at`）。任何字段缺失 → 构造失败（fail-fast），不允许生成
"部分 provenance"的 Evidence（P14E-011）。

## 5. PIT 继承（P14E-003）

P14-E 不发明任何新的可见性规则：

```text
可见 ⇔ available_time <= as_of     （含边界相等，P14-D/P14-A 冻结语义）
```

```text
event_time   信息事件发生时间（报告期间、行情时点）
available_time  研究系统可获得该信息的时间
as_of           查询决策时间点
```

三者保持正交。禁止以 `event_time <= as_of` 作为可见性充分条件；禁止因
`ingested_at` 更新而改变 PIT visibility（可见性只由 available_time 与
as_of 决定，P14E-014）。

## 6. Version / Restatement Provenance（P14E-004 / P14E-005）

Evidence Bundle 必须为每个 lineage 记录版本选择的完整 trace：

### 6.1 胜出者

胜出 evidence 携带选择理由记录，理由枚举冻结：

```text
SELECTED_HIGHEST_REVISION          lineage 内最高 admissible revision
SELECTED_EARLIEST_ON_REVISION_TIE  同 revision 并列 → 最早 available_time
SELECTED_CANONICAL_TIEBREAK        revision 与 available_time 都并列
                                   → 最小 canonical_json
```

### 6.2 落选者（candidate trace）

在**本 bundle 的 as_of 下 admissible** 且未胜出的候选记录进 trace，落选
原因枚举冻结：

```text
REJECTED_LOWER_REVISION              存在更高 admissible revision
REJECTED_REVISION_TIE_NOT_EARLIEST   同 revision，但 available_time 更晚
REJECTED_CANONICAL_TIEBREAK          revision 与 available_time 都相同，
                                     canonical_json 更大
```

### 6.3 选择可重推性——仅限本 Bundle 的 as_of（P14E-005，REPAIR-001 方案 A 冻结）

Evidence Bundle 只证明**其自身 as_of** 下的版本选择：由 bundle 内容
（candidate trace 的 `(revision, available_time)` + §2.1 冻结选择规则）
即可机械重推"为什么 revision N 在该 as_of 被选中、revision N-1 为什么
落选"，无需重放实现代码。

**跨 as_of 的问题不在单个 bundle 的语义范围内。** 例如"在更早的 as_of
下是否会选中 revision N-1"，必须以该 as_of 重新执行 P14-D query 并生成
新的 Evidence Bundle（新 bundle 自身仍是 PIT-safe 的）。

冻结理由：candidate_trace 只包含本 as_of 下 admissible 的候选；若要求
单个 bundle 回答"任意 as_of"，则 bundle 必须掌握 post-as-of 的候选信息，
这直接违反 P14E-015（禁止 future / post-as-of evidence 进入过去
Evidence）并动摇 P14-D/P14-A 冻结的 PIT 边界。三个原始要求中，与 PIT
边界冲突的"任意 as_of 可重推"被删除（REPAIR-001）。

Restatement 语义不变：T1 <= as_of < T2 只见 original，as_of >= T2 才见
restated（P14-D 冻结）；其验证方式是"两个 as_of → 两个各自 PIT-safe、
各自可重推的 bundle"。

## 7. Query Result → Evidence Bundle Mapping（P14E-006 / P14E-007 / P14E-008）

### 7.1 Bundle 结构（冻结）

```text
EvidenceBundle:
    schema_version          "p14e-evidence-bundle-1"
    query                   P14-D query 规范回显（entity/information_type/as_of/source）
    as_of                   同 query.as_of（显式冗余，便于单独审计）
    result_id               该 bundle 派生自的 P14-D result_id
    evidence[]              每条可见记录一个 Evidence（§4）
    candidate_trace[]       §6.2 落选候选（仅本 as_of 下 admissible）
    exclusions[]            P14-D excluded 原样携带（reason 分类不合并）
    counts                  {evidence, candidates, exclusions, examined}
    bundle_id               §8
```

### 7.2 一一对应（P14E-006）

`result.records` 与 `bundle.evidence` 一一对应：每条可见记录恰好映射一个
Evidence；bundle 不得包含 result 中不存在的 evidence，也不得遗漏。
`result_id` 使 bundle ↔ result ↔ query 的链接可审计。

### 7.3 排序与唯一性（P14E-007 / P14E-008）

```text
evidence[]          按 (source, source_id, revision) 升序
candidate_trace[]   按 (source, source_id, revision, available_time,
                    raw_payload_hash) 升序
exclusions[]        继承 P14-D 排序（source, source_id, reason）
```

同一 bundle 内 evidence_id 唯一（可见记录已按 lineage 折叠，每个 lineage
最多一个胜出 evidence）；candidate trace 条目唯一（键
`(source, source_id, revision, available_time, raw_payload_hash)`）。
重复输入记录不产生重复 evidence。

## 8. Bundle Determinism（P14E-009）

```text
bundle_id = sha256(canonical_json(bundle 去除 bundle_id 后的完整内容))
```

冻结性质：相同 (query, as_of, records) → 相同 bundle_id 与
byte-identical canonical 序列化；与输入顺序、dict 顺序、文件系统顺序、
运行环境无关；bundle 内禁止 runtime timestamp / UUID / random /
machine path / 任何环境相关值。

## 9. Missing / Unavailable 状态（P14E-010）

`exclusions[]` 原样携带 P14-D exclusion 记录，reason 枚举不扩展、不合并：

```text
NOT_YET_AVAILABLE / OUTSIDE_AS_OF / UNRESOLVED_AVAILABILITY   （P14-D 冻结）
```

P14-C 六类 missingness（SOURCE_ERROR / PARSE_FAILURE / SOURCE_EMPTY /
EXPECTED_ABSENCE / UNEXPECTED_MISSING / UNRESOLVED_AVAILABILITY）保持为
上游 authority；P14-E 不得引入泛化 "missing" 标签，不得重新定义任何一类。
若未来需要把 P14-C completeness/missingness 证据挂入 bundle，必须先走
Contract Repair。

## 10. Provenance Failure（P14E-011）

冻结规则：任何记录若无法构成完整 provenance（§4.1 有字段缺失或
ingestion_id / raw_payload_hash 无法从 P14-B 权威值取得），则：

1. 该记录不得产生 Evidence；
2. 该记录所在 lineage 不得进入 candidate trace；
3. Bundle 构造整体 **fail-fast**（raise），不产出部分 bundle；
4. 不存在"降级 bundle"或"带 PROVENANCE_INCOMPLETE 标记的 bundle"。

理由：Evidence 层的存在意义是可审计性；允许不完整 provenance 进入 bundle
会静默破坏反向追溯。实现不得留自由解释空间。

## 11. Mutation / Tamper Detection（P14E-012）

Evidence 的 payload 身份是 P14-B 的 `raw_payload_hash` 与 `ingestion_id`。
冻结规则：

1. P14-B 已负责检测 same (source, source_id, revision) + 不同 canonical
   payload → `RAW_MUTATION_DETECTED`（durable audit）；P14-E 不重新实现。
2. Evidence Bundle 构造时若发现同一线程内出现相同
   `(source, source_id, revision)` 但 `raw_payload_hash` 不同的候选记录，
   构造 **fail-fast**（raise）：这是 P14-B 语义下的 mutation 证据，
   不允许静默任选其一进入 evidence。
3. bundle 持久化后重载时必须校验 evidence 的 `ingestion_id` 与
   `raw_payload_hash` 仍能对应（见 §12 reload 语义）；对应不上 → 重载
   fail-fast。

## 12. Persistence Boundary（P14E-013）

P14-E **要求 durable evidence artifact**。理由：Evidence 的审计价值跨越
进程生命周期；仅 in-memory 会使"从 bundle_id 反向追溯"依赖进程存活，
与 P14-B durable audit 的既有架构原则不一致。

冻结 schema 与语义：

```text
文件        evidence_bundles.jsonl（与 P14-B 审计文件同目录约定）
格式        JSONL，每行一个完整 bundle（canonical serialization，§8）
身份        bundle_id 唯一；同 bundle_id 重复写入 → 拒绝（幂等保护）
写入        append-only；单行原子追加；禁止就地修改既有行
reload      重载后逐行重算 bundle_id 必须与行内 bundle_id 一致；
            且 evidence 的 (ingestion_id, raw_payload_hash) 必须能在
            P14-B raw_records.jsonl 中核验；任一失败 → fail-fast
```

## 13. Query Reproducibility（P14E-014）

给定相同 (query, as_of, records snapshot)，未来重新执行必须得到相同的
`result_id` 与 `bundle_id`。Bundle 内不允许任何外部环境变量字段。
`ingested_at` 是记录的既有事实字段，**不参与 evidence_id**（§4.1
Audit-only），也不参与可见性判定（§5）。已存储记录的 ingested_at 不可能
变化（P14-B immutable + DUPLICATE 语义）；ingested_at 的任何差异不改变
evidence 身份，也不改变任何 as_of 下的可见性结论。

## 14. Boundary / Security / Anti-Cheat（P14E-015 / P14E-016）

### 14.1 边界（P14E-015）

1. bundle 构造入口对 `as_of >= virgin_start (2026-09-23)` fail-fast
   raise（复用 P13-U `assert_research_zone`）。
2. 禁止使用 future evidence / post-as-of payload / hidden global state /
   current-latest data 重建过去 Evidence。
3. 测试 fixture 需要未来时间必须使用合成日期（如 `2099-01-01`）；
   真实 `2026-09-23+` 数据不得进入 P14-E 任何 contract/harness/golden/
   fixture（P13-T = STOPPED / NOT EXECUTED；P13-U = PROTECTED）。

### 14.2 反作弊（P14E-016）

生产代码禁止：`fixture_mode`、`expected_result_override`、
`golden_override`、`test_only`、`skip_validation`、`force_visible`、
`force_hidden`、`running_under_test` 分支、通过 fixture 名 / golden id /
环境变量改变真实行为。

### 14.3 Scope（P14E-016）

Evidence/Provenance 层的公开 API 面仅限 evidence 构造、bundle 构造、
持久化、重载与核验。禁止出现 scoring / ranking / recommendation /
prediction / trading / portfolio / alpha 语义的任何函数或字段。

## 15. Evidence Chain（P14E-017）

冻结的全链关系（每一跳都必须可机械走通）：

```text
Raw Record (P14-B raw_records.jsonl, raw_payload_hash, ingestion_id)
    ↓  to_information_record（P14-A 权威投影）
Normalized Record (RawInformationRecord, canonical_json, record_id)
    ↓  available_time <= as_of（P14-A/P14-D 冻结规则）+ lineage 选择
Visible Revision (P14-D result.records)
    ↓  §7 映射
Evidence Bundle (bundle_id)
```

反向追溯冻结要求：从 `bundle_id` → bundle → evidence →
`(ingestion_id, raw_payload_hash)` → P14-B 原始行，必须能机械走通
（P14E-017）。禁止"只保存最终 result_id"而无法恢复 result → evidence →
source record 的设计。

## 16. Invariant Registry（P14E-001..017）

全部 Contract ID 在本文件 §4-§15 定义；Acceptance Matrix（DRAFT）每条
至少一行。

- **P14E-001**: evidence_id 为内容寻址确定性 ID，由 Identity fields
  （§4.1 八字段，含 P14-B raw_payload_hash 与 ingestion_id）完全决定；
  相同 raw payload 在不同 ingestion event 下得到相同 evidence_id
  （P14-B 幂等 + DUPLICATE 语义）；payload 语义内容变化则 ID 变化；
  与插入顺序/对象序/环境无关；ingested_at 为 Audit-only，不参与 ID。
- **P14E-002**: 每个 Evidence 携带 §4.1 全部三类字段（含 Audit-only 的
  ingested_at）；缺任一字段即构造失败。
- **P14E-003**: 可见性判定完全继承 P14-D/P14-A（available_time <= as_of，
  含边界相等）；event_time 与 ingested_at 不参与可见性。
- **P14E-004**: bundle 为每个 lineage 记录选择理由与全部落选候选，理由
  与落选原因枚举冻结（§6）。
- **P14E-005**: bundle 的版本选择可由 bundle 内容（candidate trace +
  §2.1 冻结规则）就**其自身 as_of** 机械重推；跨 as_of 问题不在单个
  bundle 语义范围内，必须以新 as_of 重新执行 P14-D query 生成新 bundle
  （REPAIR-001 方案 A；与 P14E-015 PIT 边界严格一致）。
- **P14E-006**: result.records 与 bundle.evidence 一一对应；bundle 携带
  result_id 链接。
- **P14E-007**: evidence[] / candidate_trace[] / exclusions[] 的排序键
  冻结（§7.3）。
- **P14E-008**: bundle 内 evidence_id 唯一、candidate trace 条目唯一；
  重复输入不产生重复 evidence。
- **P14E-009**: bundle_id 为 canonical 序列化的 sha256；相同输入
  byte-identical；禁止 runtime/环境字段。
- **P14E-010**: exclusion 与 missingness 状态沿用 P14-D/P14-C 冻结枚举，
  不合并、不重定义、不引入泛化 "missing"。
- **P14E-011**: provenance 不完整时 bundle 构造整体 fail-fast；不存在
  降级 bundle 或 PROVENANCE_INCOMPLETE 标记 bundle。
- **P14E-012**: payload 身份冲突（同 key 不同 raw_payload_hash）时构造
  fail-fast；mutation 检测权威在 P14-B，P14-E 消费并核验。
- **P14E-013**: durable evidence artifact（JSONL append-only、bundle_id
  幂等、reload 全量校验）为必需；schema 冻结（§12）。
- **P14E-014**: 相同 (query, as_of, records) 重放产生相同 result_id 与
  bundle_id；bundle 无环境字段；ingested_at 不参与 evidence 身份
  （§4.1）与可见性（§5），已存储记录的 ingested_at 不可变。
- **P14E-015**: as_of >= virgin_start fail-fast；禁止 future evidence /
  post-as-of payload / hidden state 重建过去 evidence；测试仅用合成
  未来日期。
- **P14E-016**: 反作弊控制键禁止；公开 API 面仅限 evidence/bundle
  构造、持久化、重载、核验；无 scoring/ranking/recommendation/trading。
- **P14E-017**: 从 bundle_id 到 P14-B 原始行的反向追溯链可机械走通。
