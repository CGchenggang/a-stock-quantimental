# P14-E Golden Test Design

> STATUS: DESIGN ONLY
>
> **本文件是设计，不是可执行测试。** 禁止在本阶段创建 pytest / Harness /
> production 实现（`tests/contracts/p14e/` 尚不得存在）。执行属于后续
> Harness 阶段。
>
> 冻结依据：P14-E Design Contract v1.1（`712faf9`）+ Acceptance Matrix
> v2（FROZEN）。每个 Golden 必须给出 Input / Expected Evidence / Expected
> Bundle / Expected Failure / Contract Coverage 五要素；禁止 should /
> probably / approximately / reasonable 等不可验证描述。

---

## 0. 公共约定（全部 Golden 共用）

- 记录输入一律使用 P14-A `RawInformationRecord` 语义的确定性 fixture；
  时间戳全部合成：研究区 2026-03-01..2026-03-06（+08:00），未来仅
  `2099-01-01T09:00:00+08:00`；**禁止任何真实 `2026-09-23+` 日期**
  （P13-U 守卫，P14E-M-015）。
- 每个 Golden 的 Expected Bundle 字段以合同 §7.1 结构为准：
  `schema_version / query / as_of / result_id / evidence[] /
  candidate_trace[] / exclusions[] / counts / bundle_id`。
- Evidence 字段以 §4.1 三类为准；evidence_id 公式 = §4.2。
- 断言全部基于手写期望值；禁止从实现输出生成期望（反作弊 P14E-016）。

## 覆盖映射（17/17）

| Golden | Contract IDs |
|--------|--------------|
| G-001 | P14E-001, P14E-017 |
| G-002 | P14E-001, P14E-014 |
| G-003 | P14E-003, P14E-010 |
| G-004 | P14E-005 |
| G-005 | P14E-005, P14E-006 |
| G-006 | P14E-004 |
| G-007 | P14E-005 |
| G-008 | P14E-002, P14E-011 |
| G-009 | P14E-007, P14E-009, P14E-013, P14E-014 |
| G-010 | P14E-008 |
| G-011 | P14E-012 |
| G-012 | P14E-015 |
| 机械源码扫描（非 fixture，Harness 阶段执行） | P14E-016 |

---

## G-001 Evidence Identity / Reverse Traceability

- **Contract Coverage**: P14E-001, P14E-017
- **Input**: 两个同内容记录 A、B（source=cn_stock_quote, source_id=q-e1,
  revision=0, event/available/ingested/adapter/payload 全同），分别以
  不同列表顺序注入构造；另备第三记录 C（payload 数值不同 →
  raw_payload_hash 不同）。
- **Expected Evidence**: A、B 的 evidence_id 相等且等于手写
  sha256(canonical_json(8 Identity fields))；C 的 evidence_id 不等；
  evidence 携带 (ingestion_id, raw_payload_hash)，能在 P14-B
  raw_records.jsonl 对应行核验。
- **Expected Bundle**: bundle 包含 evidence 恰 1 条（A/B 折叠），
  bundle_id 与手写重算一致。
- **Expected Failure**: 同 payload 产生两个不同 evidence_id；或重排导致
  ID 变化；或 (ingestion_id, raw_payload_hash) 在 raw 层不可解析。
- **Contract Coverage 断言**: P14E-M-001、P14E-M-017。

## G-002 Ingestion Separation

- **Contract Coverage**: P14E-001, P14E-014
- **Input**: 同一 fact（同 8 Identity fields）的两个 ingestion event：
  ingested_at 分别为 `2026-03-02T16:05:00+08:00` 与
  `2026-03-03T09:00:00+08:00`。
- **Expected Evidence**（语义链，REPAIR-001 冻结）：第二次 attempt 因
  P14-B 判定 **DUPLICATE** → 不覆盖 canonical stored record → Evidence
  使用**最终 canonical stored record**（其 ingested_at 为首次 ACCEPTED
  attempt 的值，provenance 可追踪到具体入库事件）→ **evidence_id 不因
  duplicate attempt 分叉**（ingested_at 不参与 evidence_id，§4.1
  Audit-only）。恰一个 evidence_id。
- **Expected Bundle**: bundle 唯一；**bundle_id 不因被拒绝的 duplicate
  attempt 而改变**——原因是该 attempt 未进入 stored record set，而非
  "ingested_at 不参与 bundle_id"：bundle_id 是完整 bundle canonical
  content 的 hash，evidence 携带 audit-only `ingested_at`（最终 stored
  record 的值），因此 bundle_id 由最终 stored record 决定。被拒绝的
  duplicate attempt 不出现在 bundle 任何字段。
- **Expected Failure**: duplicate attempt 导致 evidence_id 分叉；
  DUPLICATE 覆盖 stored record；duplicate attempt 的 ingested_at 泄入
  bundle；或实现/文档把 "ingested_at 不参与 evidence_id" 错误扩展为
  "ingested_at 不参与 bundle_id"（bundle 内容与 hash 将不一致）。
- **Contract Coverage 断言**: P14E-M-001、P14E-M-014。

## G-003 PIT Visibility Boundary

- **Contract Coverage**: P14E-003, P14E-010
- **Input**: 三记录 R1（available = 2026-03-03T15:59:59+08:00）、
  R2（available = 2026-03-03T16:00:00+08:00）、
  R3（available = 2026-03-03T16:00:01+08:00）；查询 as_of =
  `2026-03-03T16:00:00+08:00`；另含一条 entity 不匹配的 R4。
- **Expected Evidence**: 仅 R1、R2 进入 evidence（R2 为边界相等 → 可见）；
  R3、R4 不产生 evidence。
- **Expected Bundle**: exclusions 恰两条且 reason 逐字为
  `NOT_YET_AVAILABLE`（R3）与 `OUTSIDE_AS_OF`（R4）——P14-D 枚举原样
  携带，无合并；counts = {evidence: 2, candidates: 0, exclusions: 2,
  examined: 4}。
- **Expected Failure**: R3 可见；R2 不可见；reason 被改写或合并为
  "missing"。
- **Contract Coverage 断言**: P14E-M-003、P14E-M-010。

## G-004 Counterfactual Trace Boundary

- **Contract Coverage**: P14E-005
- **Input**: lineage（source=macro_pmi_cn, source_id=pmi-m01）：
  rev0 available T1=`2026-03-02T16:00:00+08:00`，rev1 available
  T2=`2026-03-05T09:00:00+08:00`。以 as_of=T1+1d
  （`2026-03-03T16:00:00+08:00`）生成 bundle(T1)。
- **Expected Evidence**: bundle(T1) 的 evidence 选中 rev0；rev1 **不进入
  evidence**；rev1 **不进入 candidate_trace**（trace 仅含本 as_of 下
  admissible 的候选，§6.2）；rev1 的 **payload、raw_payload_hash、
  ingestion_id 不出现在 bundle 的任何字段**。
- **Expected Bundle**: bundle(T1) 对 rev1 的唯一呈现是 P14-D exclusion
  条目，且该条目恰含 P14-D 冻结的四个字段
  `{source, source_id, reason=NOT_YET_AVAILABLE, available_time=T2}`。
  语义边界（REPAIR-001 冻结）：**"知道存在一个未来尚不可用记录"不等于
  "泄露未来 Evidence 内容"**——exclusion 的存在与 available_time 是
  P14-D 已冻结的 observation 事实，允许进入早于 T2 的 bundle；被禁止的
  是把 post-as-of record 的 payload / raw_payload_hash / ingestion_id /
  future Evidence / future candidate_trace / future revision-selection
  state 带入更早 as_of 的 Evidence Bundle。bundle(T1) 内不存在任何
  post-as-of 的 record（evidence）或 candidate。
- **Expected Failure**: rev1 的 payload、raw_payload_hash 或
  ingestion_id 出现在早于 T2 的 bundle 任何字段；rev1 进入
  candidate_trace 或 evidence；bundle(T1) 被用于生成 Bundle(T2) 的信息
  状态；单 bundle 给出跨 as_of 结论。
- **Contract Coverage 断言**: P14E-M-005。

## G-005 Independent As-of Bundle

- **Contract Coverage**: P14E-005, P14E-006
- **Input**: G-004 同一 lineage；分别执行 query(as_of=T1+1d) 与
  query(as_of=T2)。
- **Expected Evidence**: bundle1 选中 rev0；bundle2 选中 rev1；
  bundle1.evidence ∩ bundle2.evidence（按 evidence_id）= ∅。
- **Expected Bundle**: 两 bundle 是独立 artifact：各自携带自己的
  as_of / result_id / bundle_id；bundle2.result_id == query(as_of=T2)
  的 result.result_id（1:1 映射，P14E-006）；两 bundle_id 不同。
- **Expected Failure**: 单一 bundle 同时服务两个 as_of；result_id 链接
  缺失或指向错误 result。
- **Contract Coverage 断言**: P14E-M-005、P14E-M-006。

## G-006 Revision Selection

- **Contract Coverage**: P14E-004
- **Input**: lineage（source_id=q-sel）四个 admissible 记录：rev1@03-02、
  rev3@03-04、rev2@03-03、以及同 rev3@03-05（更晚 available_time）；
  as_of=2026-03-06T16:00:00+08:00。
- **Expected Evidence**: 胜出 rev3@03-04，selection reason =
  `SELECTED_EARLIEST_ON_REVISION_TIE`（同 rev3 并列 → 最早
  available_time 胜出，继承 P14-D 冻结链：highest visible revision →
  earliest available_time → canonical tie break，不重新定义）。
- **Expected Bundle**: candidate_trace 恰三条：rev1（
  `REJECTED_LOWER_REVISION`）、rev2（`REJECTED_LOWER_REVISION`）、
  rev3@03-05（`REJECTED_REVISION_TIE_NOT_EARLIEST`）；排序按 §7.3。
- **Expected Failure**: 枚举外理由；rev3@03-05 胜出（违反同 revision
  earliest 规则）；候选丢失。
- **Contract Coverage 断言**: P14E-M-004。

## G-007 Restatement

- **Contract Coverage**: P14E-005
- **Input**: G-004 lineage 的原始/重述对（rev0@T1 original、rev1@T2
  restated，payload 数值不同）。
- **Expected Evidence**: query(as_of ∈ [T1, T2)) → evidence 仅 rev0，
  restated 记录以 exclusion（NOT_YET_AVAILABLE）出现；query(as_of >= T2)
  → evidence 仅 rev1。
- **Expected Bundle**: 两个 bundle 各自 PIT-safe、各自可由内容重推
  （方案 A）。restated（rev1）在早于 T2 的 bundle 中**仅以 P14-D
  exclusion 四字段**出现：`{source, source_id,
  reason=NOT_YET_AVAILABLE, available_time=T2}`——其 payload 数值、
  raw_payload_hash、ingestion_id **不进入**早于 T2 的 bundle 任何字段；
  as_of >= T2 的 bundle 才包含 rev1 的完整 evidence（含 payload 身份）。
- **Expected Failure**: as_of < T2 时 rev1 数值可见；restated 进入更早
  bundle 的 candidate_trace。
- **Contract Coverage 断言**: P14E-M-005。

## G-008 Provenance Completeness

- **Contract Coverage**: P14E-002, P14E-011
- **Input**: 完整记录 R_ok；三个残缺变体：R_no_ing（缺 ingested_at）、
  R_no_hash（metadata 无 raw_payload_hash）、R_no_ingid（metadata 无
  ingestion_id）。
- **Expected Evidence**: R_ok 构造成功且九字段齐全；三个残缺变体逐个
  构造 raise（ValueError）。
- **Expected Bundle**: bundle 构造在任一残缺记录存在时整体 fail-fast，
  无任何 bundle 写出（包括不含该记录的"部分 bundle"也不允许——整批
  fail-fast，P14E-011）。
- **Expected Failure**: 残缺记录被跳过/补默认值；产出降级 bundle 或
  PROVENANCE_INCOMPLETE 标记 bundle。
- **Contract Coverage 断言**: P14E-M-002、P14E-M-011。

## G-009 Deterministic Bundle / Persistence

- **Contract Coverage**: P14E-007, P14E-009, P14E-013, P14E-014
- **Input**: 多 lineage 多版本记录集（≥3 lineage，含同 revision tie），
  以三种不同输入顺序（原序 / 逆序 / 随机置换的固定种子序）执行同一
  query；bundle 写入 `evidence_bundles.jsonl` 后重载。
- **Expected Evidence**: evidence[] / candidate_trace[] / exclusions[]
  三类列表在三种顺序下逐字节同序（§7.3 排序键）。
- **Expected Bundle**: 三次运行 bundle_id 相等且 canonical 序列化
  byte-identical；无 generated_at / uuid / machine path；持久化后 reload
  重算 bundle_id == 存储值，且 evidence 的 (ingestion_id,
  raw_payload_hash) 在 P14-B raw 层核验通过；同 bundle_id 二次 append 被
  拒（幂等保护）；同 query+as_of 重放 result_id 亦相等（P14E-014）。
- **Expected Failure**: 任一顺序变化导致 bundle_id 变化；reload 漂移；
  重复 append 被接受。
- **Contract Coverage 断言**: P14E-M-007、P14E-M-009、P14E-M-013、
  P14E-M-014。

## G-010 Duplicate Evidence

- **Contract Coverage**: P14E-008
- **Input**: 同 lineage 完全相同记录以 3 份重复注入（模拟 duplicate
  ingestion 后的记录集），另加一条不同 lineage 记录。
- **Expected Evidence**: 每 lineage 恰 1 条 evidence（共 2 条）；
  evidence_id 在 bundle 内唯一。
- **Expected Bundle**: counts.evidence == 2；candidate_trace 无重复条目
  （键 (source, source_id, revision, available_time, raw_payload_hash)
  唯一）。
- **Expected Failure**: 重复记录产生重复 evidence 行或重复 trace。
- **Contract Coverage 断言**: P14E-M-008。

## G-011 Mutation Detection

- **Contract Coverage**: P14E-012
- **Input**: 同 (source, source_id, revision) 的两条记录，payload 不同
  → raw_payload_hash 不同（模拟 P14-B RAW_MUTATION_DETECTED 语义的
  下游可见形态）。
- **Expected Evidence**: 不产生任何 evidence。
- **Expected Bundle**: bundle 构造整体 fail-fast（ValueError）；无
  bundle 写出；错误信息指明冲突 lineage。
- **Expected Failure**: 静默任选其一进入 evidence；或静默产出两个
  evidence。
- **Contract Coverage 断言**: P14E-M-012。

## G-012 Virgin Protection

- **Contract Coverage**: P14E-015
- **Input**: 查询 as_of = `2099-01-01T09:00:00+08:00`（合成未来日期）；
  以及全部 fixture 输入的日期扫描集。
- **Expected Evidence**: 不产生（构造前即失败）。
- **Expected Bundle**: 无。
- **Expected Failure**: 构造不 raise（守卫被绕过）；或任何 fixture 输入
  含 `[2026-09-23, 2028-01-01)` 区间内的真实日期（扫描命中即 FAIL；
  ≥2028 的合成日期豁免，且仅限守卫证明用途）。
- **Contract Coverage 断言**: P14E-M-015。

## 机械源码扫描（非 fixture；Harness 阶段执行）

- **Contract Coverage**: P14E-016
- **扫描对象**: P14-E 生产模块（Harness 阶段才存在）。
- **Expected**: 逐行扫描禁词 `fixture_mode / expected_result_override /
  golden_override / test_only / skip_validation / force_visible /
  force_hidden / running_under_test` 零命中（注释中的禁令声明豁免）；
  公开符号面不含 scoring / ranking / recommendation / trading / portfolio /
  alpha。
- **Expected Failure**: 任一禁词命中或决策面符号出现。
- **Matrix 对应**: P14E-M-016（Golden Fixture 列 = N/A (source scan)）。
