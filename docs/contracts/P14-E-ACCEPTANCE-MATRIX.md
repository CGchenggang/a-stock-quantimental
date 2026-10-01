# P14-E Acceptance Matrix

> STATUS: DRAFT — awaiting independent Contract acceptance
>
> 每一行：Matrix ID ↔ Contract ID ↔ Requirement ↔ Verification method ↔
> Expected evidence。本阶段禁止创建 Golden / Harness / production
> implementation；Verification method 是规划，不是已完成验证。

| Matrix ID | Contract ID | Requirement | Verification method | Expected evidence |
|-----------|------------|-------------|---------------------|-------------------|
| P14E-M-001 | P14E-001 | evidence_id 内容寻址、确定、顺序无关；同 payload 异 ingestion event → 同 ID（ingested_at 不参与） | 未来 Golden（同内容异序构造 → 同 ID；改 payload hash → 异 ID；同键同 payload 二次入库（DUPLICATE 路径）→ 仍同 ID） | 三断言全部成立 |
| P14E-M-002 | P14E-002 | provenance 字段完整（§4.1 九字段） | 未来 Harness（缺字段构造 raise） | 缺任一字段 ValueError |
| P14E-M-003 | P14E-003 | 可见性继承 available_time <= as_of | 未来 Golden（event_time 早 + available 晚 → 不可见） | 记录不进入 evidence |
| P14E-M-004 | P14E-004 | 选择理由与落选 trace 枚举冻结 | 未来 Harness（多版本 lineage 断言 trace） | 枚举值与 §6 完全一致 |
| P14E-M-005 | P14E-005 | 本 as_of 的版本选择由 bundle 内容 + 冻结规则机械重推；跨 as_of 需新查询/新 bundle（方案 A） | 未来 Golden（rev1@T1/rev2@T2：as_of<T2 生成 bundle A 选 rev1，as_of>=T2 生成 bundle B 选 rev2；两 bundle 各自 PIT-safe 且各自可由内容重推） | 两 bundle 断言各自成立；单 bundle 不承载跨 as_of 结论 |
| P14E-M-006 | P14E-006 | result.records ↔ evidence 一一对应 + result_id 链接 | 未来 Harness | 数量相等且 bundle.result_id == result_id |
| P14E-M-007 | P14E-007 | 三类列表排序键冻结 | 未来 Golden（乱序输入 → 同序 bundle） | canonical 顺序一致 |
| P14E-M-008 | P14E-008 | bundle 内 ID 唯一、重复输入不重复 | 未来 Harness（重复记录注入） | evidence 数不变 |
| P14E-M-009 | P14E-009 | bundle_id 确定性 + 无环境字段 | 未来 Golden 双跑 byte-identical | bundle_id 相等、无 runtime 字段 |
| P14E-M-010 | P14E-010 | exclusion/missingness 枚举不合并 | 未来 Harness（八类状态逐类断言） | 枚举与 P14-C/D 冻结值一致 |
| P14E-M-011 | P14E-011 | provenance 不完整 → 构造 fail-fast | 未来 Harness（缺 hash 记录注入） | raise，无部分 bundle |
| P14E-M-012 | P14E-012 | 同 key 异 hash → 构造 fail-fast | 未来 Harness（mutation 记录注入） | raise；P14-B 检测语义未被复制 |
| P14E-M-013 | P14E-013 | durable JSONL：append-only、幂等、reload 全量校验 | 未来 Harness（写→重载→重算 bundle_id） | reload 后 bundle_id 一致；重复写被拒 |
| P14E-M-014 | P14E-014 | 相同输入重放相同双 ID | 未来 Golden 双跑 | result_id 与 bundle_id 均相等 |
| P14E-M-015 | P14E-015 | virgin 守卫 + 合成未来日期 | 未来 Harness（as_of=2099 → raise） | raise；fixture 无真实 virgin 日期 |
| P14E-M-016 | P14E-016 | 反作弊键禁止 + API 面受限 | 未来机械扫描（源码扫描） | 命中即 FAIL；无 scoring/recommendation 面 |
| P14E-M-017 | P14E-017 | bundle_id → P14-B 原始行反向可追溯 | 未来 Harness（全链回放核验） | ingestion_id/raw_payload_hash 在 raw_records.jsonl 核验通过 |

说明：Verification method 全部为规划项（Golden / Harness / 机械扫描），
在独立 Contract acceptance 授予前不得实现。
