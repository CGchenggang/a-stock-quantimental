# P14-E Acceptance Matrix

> STATUS: FROZEN — P14-E-002 — awaiting Harness verification
>
> 冻结依据：P14-E Design Contract v1.1（REPAIR-001 语义，HEAD
> `712faf9b2fcbf146e69033b43415c5b57e509dc8`）已通过 Independent Contract
> Acceptance。本 Matrix 冻结 Contract ↔ Golden ↔ Verification 对应关系；
> 状态为 FROZEN 而非 PASS/ACCEPTED——PASS 由后续 Harness + Golden 实际
> 执行结果决定。
>
> 修订历史：
> v1: DRAFT（P14-E-001，17 行 5 列）
> v1.1: REPAIR-001（M-001 / M-005 语义行更新）
> v2: P14-E-002 冻结——7 列结构（Verification Method / Golden Fixture /
>     Expected Result / Failure Condition），绑定 Golden G-001..G-012

| Matrix ID | Contract ID | Requirement | Verification Method | Golden Fixture | Expected Result | Failure Condition |
|-----------|------------|-------------|---------------------|----------------|-----------------|-------------------|
| P14E-M-001 | P14E-001 | evidence_id = sha256(canonical_json(8 个 Identity fields))，内容寻址、确定、顺序无关；同 payload 异 ingestion event → 同 ID | Golden：同内容异序构造 / payload hash 变体 / DUPLICATE 重入 | G-001, G-002 | 三断言成立：异序同 ID；hash 变体异 ID；DUPLICATE 重入同 ID | 同 payload 分叉出两个 evidence_id；或重排导致 ID 变化 |
| P14E-M-002 | P14E-002 | Evidence 必须携带 §4.1 全部三类字段（含 Audit-only ingested_at） | Golden：逐字段缺失构造 | G-008 | 任一字段缺失 → 构造 raise | 缺字段仍产出 Evidence |
| P14E-M-003 | P14E-003 | 可见性 ⇔ available_time <= as_of（含边界相等）；event_time / ingested_at 不参与可见性 | Golden：boundary 三元组（< / == / >） | G-003 | 仅 available_time <= as_of 可见 | event_time 授予可见性；> as_of 记录可见；== 不可见 |
| P14E-M-004 | P14E-004 | lineage 选择理由（SELECTED_*）与落选原因（REJECTED_*）枚举冻结，trace 完整 | Golden：多版本 lineage 断言 trace | G-006 | 枚举与 §6 完全一致；每个 admissible 候选恰一条 trace | 出现枚举外理由；候选静默丢失 |
| P14E-M-005 | P14E-005 | Bundle 只证明其自身 as_of 的版本选择；跨 as_of 需新查询/新 bundle（方案 A） | Golden：两个 as_of → 两个独立 bundle 各自断言 | G-004, G-005, G-007 | 两 bundle 各自 PIT-safe 且各自可由内容重推；单 bundle 不承载跨 as_of 结论 | 未来 revision 出现在更早 bundle；单 bundle 给出跨 as_of 结论 |
| P14E-M-006 | P14E-006 | result.records ↔ evidence 一一对应；bundle 携带 result_id 链接 | Golden：bundle 与 P14-D result 对照 | G-005 | counts 相等；bundle.result_id == result.result_id | 数量不一致；result_id 链接缺失 |
| P14E-M-007 | P14E-007 | evidence[] / candidate_trace[] / exclusions[] 排序键冻结（§7.3） | Golden：乱序输入 → 同序 bundle | G-009 | 三类列表顺序与输入顺序无关 | 输出顺序随输入顺序漂移 |
| P14E-M-008 | P14E-008 | bundle 内 evidence_id 唯一；重复输入不产生重复 evidence | Golden：重复记录注入 | G-010 | 每 lineage 恰一个 evidence；trace 条目唯一 | 重复 evidence 行；trace 重复 |
| P14E-M-009 | P14E-009 | bundle_id = sha256(canonical_json(去除 bundle_id 的完整内容))；byte-identical；无 runtime/环境字段 | Golden：双跑字节比对 + 禁词扫描 | G-009 | 双跑 bundle_id 相等且字节一致；无 generated_at/uuid/machine path | bundle_id 漂移；出现 runtime 字段 |
| P14E-M-010 | P14E-010 | exclusions 原样携带 P14-D reason 枚举（NOT_YET_AVAILABLE / OUTSIDE_AS_OF / UNRESOLVED_AVAILABILITY），不合并、不重定义 | Golden：exclusion reason 断言 | G-003 | reason 与 P14-D result 逐字一致 | 合并为泛化 "missing"；枚举被改写 |
| P14E-M-011 | P14E-011 | provenance 不完整 → bundle 构造整体 fail-fast；不存在降级 bundle / PROVENANCE_INCOMPLETE 标记 bundle | Golden：缺 hash 记录注入 | G-008 | raise；无任何 bundle 写出 | 产出部分 bundle 或降级标记 bundle |
| P14E-M-012 | P14E-012 | 同 (source, source_id, revision) 异 raw_payload_hash → 构造 fail-fast；mutation 检测权威在 P14-B | Golden：mutation 记录注入 | G-011 | raise；不静默任选其一 | 静默接受 mutation 进入 evidence |
| P14E-M-013 | P14E-013 | durable JSONL：append-only、bundle_id 幂等（重复写拒绝）、reload 全量校验（重算 id + 对 P14-B raw 核验） | Golden：持久化 → 重载 → 重算 | G-009 | reload 后 bundle_id 与存储一致；重复写被拒 | reload 漂移；重复 append 被接受 |
| P14E-M-014 | P14E-014 | 相同 (query, as_of, records) 重放 → 相同 result_id 与 bundle_id；bundle 无环境字段；ingested_at 不参与身份与可见性 | Golden：重放双跑（含异 ingested_at 变体） | G-002, G-009 | 双 ID 稳定；ingested_at 差异不改变 ID | 任一 ID 漂移；ingested_at 影响 ID |
| P14E-M-015 | P14E-015 | as_of >= virgin_start (2026-09-23) fail-fast；fixture 输入无真实 virgin 日期（未来仅合成 2099-01-01） | Golden：守卫 raise + fixture 日期扫描 | G-012 | raise；扫描零命中 | 守卫被绕过；真实 virgin 日期进入 fixture |
| P14E-M-016 | P14E-016 | 反作弊键（fixture_mode/expected_result_override/golden_override/test_only/skip_validation/force_visible/force_hidden/running_under_test）禁止；公开 API 面仅限 evidence/bundle 构造、持久化、重载、核验 | 机械源码扫描（Harness 阶段执行；非 fixture） | N/A (source scan) | 零命中；无 scoring/ranking/recommendation/trading 符号 | 任一禁词命中；出现决策面符号 |
| P14E-M-017 | P14E-017 | bundle_id → evidence → (ingestion_id, raw_payload_hash) → P14-B 原始行反向可追溯 | Golden：全链回放核验 | G-001 | 链路在 P14-B raw_records.jsonl 中核验通过 | 任一环节不可解析 |
