# P14-E Implementation Acceptance Matrix

> STATUS: DRAFT — P14-E-005 — awaiting independent contract acceptance
>
> Production Implementation: NOT AUTHORIZED. Verification Method 为规划
> （在实现后的 Harness/Golden 阶段执行）。
>
> Closure: Contract P14E-I-001..024 ↔ Matrix P14E-I-M-001..024 = 24/24

| Matrix ID | Contract ID | Requirement | Testability | Expected Evidence | Expected Result | Failure Condition | Golden/Test Binding |
|-----------|------------|-------------|-------------|-------------------|-----------------|-------------------|---------------------|
| P14E-I-M-001 | P14E-I-001 | Included 边界（模型/身份/生命周期/持久化/追溯/审计/校验/失败模型） | 机械范围断言 | 实现面与 §2.1 一致 | 全覆盖 | 缺组件 | 实现 Harness 结构检查 |
| P14E-I-M-002 | P14E-I-002 | Excluded 边界（alpha/factor/trading/portfolio/execution/broker/order/LLM；P13-T/U） | 机械符号扫描 | 零决策语义符号 | 无越界 | 任一越界符号 | 源扫描 |
| P14E-I-M-003 | P14E-I-003 | 权威链 + 三禁止 | 负例（写 RawStore/重建历史/覆盖 PIT 的尝试） | 全部被拒 | 零权威违反 | 任一得逞 | 实现 Harness 负例 |
| P14E-I-M-004 | P14E-I-004 | CMP-EVIDENCE 七元组行为 | Golden 同输入对照 | 与 Golden 引擎逐位一致 | 一致 | ID/序列化漂移 | P14-E-003 fixtures 重放 |
| P14E-I-M-005 | P14E-I-005 | CMP-STORE 七元组行为 | Golden G-009 同语义执行 | append/幂等/reload 语义一致 | 一致 | 写入/reload 漂移 | Golden G-009 |
| P14E-I-M-006 | P14E-I-006 | CMP-MANAGER 状态机编排 | 全迁移矩阵执行 | 合法迁移全通、非法全拒 | 状态机精确 | 非法迁移得逞 | 实现 Harness 生命周期矩阵 |
| P14E-I-M-007 | P14E-I-007 | CMP-TRACE 四类行为 | 四类负例 + 成功路径 | 分类精确 | 四类独立触发 | 合并为 NOT_FOUND | Golden G-001 + 实现 Harness 负例 |
| P14E-I-M-008 | P14E-I-008 | CMP-AUDIT 记录流 | 迁移/失败事件审计断言 | 每事件有记录、无 runtime 字段 | 完整审计 | 丢审计或 runtime 字段 | 实现 Harness 审计检查 |
| P14E-I-M-009 | P14E-I-009 | CMP-VALIDATION 规则集 | 每规则正负用例 | 全部按冻结规则触发 | 触发精确 | 漏检/误检 | Golden G-008 + 实现 Harness |
| P14E-I-M-010 | P14E-I-010 | 身份继承（8 字段 + ingested_at audit-only） | Golden G-001/G-002 同语义执行 | ID 公式逐位一致 | 一致 | 身份漂移 | Golden G-001/G-002 |
| P14E-I-M-011 | P14E-I-011 | CREATE 态规则 | 正例 + mutation/provenance 负例 | 通过或 fail-fast | 语义一致 | 部分产物存活 | Golden G-008 对照 |
| P14E-I-M-012 | P14E-I-012 | VALIDATE 态规则 | 跳过校验负例 | 拒绝跳过 | 状态机精确 | 跳过得逞 | 实现 Harness 生命周期矩阵 |
| P14E-I-M-013 | P14E-I-013 | FREEZE 态规则（重算一致 + 冻结不可变） | 篡改冻结内容负例 | 检出 | 检测精确 | 变更未检出 | Golden G-009 篡改负例 |
| P14E-I-M-014 | P14E-I-014 | STORE 态规则（append-only/幂等） | Golden G-009 同语义执行 | STORED/DUPLICATE-REJECTED 正确 | 语义一致 | 覆盖写/重复行 | Golden G-009 |
| P14E-I-M-015 | P14E-I-015 | QUERY 态只读 | 查询后状态断言 | 状态不变 | 只读保证 | 查询改状态 | 实现 Harness 只读检查 |
| P14E-I-M-016 | P14E-I-016 | TRACE 态四类路由 | 四类输入逐一执行 | 对应错误类抛出 | 路由精确 | 错类/吞错 | Golden G-001 对照 |
| P14E-I-M-017 | P14E-I-017 | AUDIT 生命周期同绑 | audit 写失败注入 | 迁移整体失败 | 同生命周期 | 静默丢审计 | 实现 Harness 负例 |
| P14E-I-M-018 | P14E-I-018 | FOUR-CLASS 冻结（无 HASH_MISMATCH 第五类） | 机械枚举扫描 | 枚举恰四类 | 无第五类 | 出现 HASH_MISMATCH | 源扫描 |
| P14E-I-M-019 | P14E-I-019 | 持久化规则（JSONL 约束优先/版本/哈希/恢复） | Golden G-009 + schema 断言 | 语义与 schema_version 一致 | 一致 | 存储语义漂移 | Golden G-009 |
| P14E-I-M-020 | P14E-I-020 | 六层失败分类 | 六层各一触发用例 | 层次独立触发 | 分类精确 | 层合并 | 实现 Harness 失败矩阵 |
| P14E-I-M-021 | P14E-I-021 | Detection/Response/Audit 三元组 | 每层三元组断言 | 三者齐备 | 全层齐备 | 缺 audit 或响应 | 实现 Harness 失败矩阵 |
| P14E-I-M-022 | P14E-I-022 | 六接口语义（In/Out/副作用/权限/失败） | 接口契约逐项执行 | 与 §10 一致 | 语义精确 | 副作用越权/失败错层 | 实现 Harness 接口测试 |
| P14E-I-M-023 | P14E-I-023 | 兼容性（P14-A/B/C/D/E 全 PASS） | 依赖一致性重跑 | 结论 PASS | 无冲突 | 任一 conflict | 依赖审计脚本 |
| P14E-I-M-024 | P14E-I-024 | 确定性/反作弊/边界继承 | Golden 双跑 + 源扫描 + 边界扫描 | 全绿 | 继承完整 | 任一漂移 | Golden G-009/G-012 + 源扫描 |
