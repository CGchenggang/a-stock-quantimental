# P14-E Production Acceptance Matrix

> STATUS: DRAFT — P14-E-004 — awaiting independent contract acceptance
>
> Production Implementation: NOT AUTHORIZED. Verification Method 列为规划
> （在 Harness 阶段执行）；Golden/Test Binding 指向 P14-E-003 已接受的
> Golden 引擎对照或未来生产 Harness 检查。
>
> Closure: Contract P14E-P-001..023 ↔ Matrix P14E-P-M-001..023 = 23/23

| Matrix ID | Contract ID | Requirement | Testability | Expected Evidence | Expected Result | Failure Condition | Golden/Test Binding |
|-----------|------------|-------------|-------------|-------------------|-----------------|-------------------|---------------------|
| P14E-P-M-001 | P14E-P-001 | 模块布局：仅 evidence.py + evidence_store.py；src 文件集 pin | 机械文件清单扫描 | 文件列表 == pin | 无额外 P14-E runtime 文件 | 出现其他 runtime 文件 | 源扫描（未来生产 Harness） |
| P14E-P-M-002 | P14E-P-002 | evidence_id = sha256(canonical_json(8 Identity fields)) | Golden 同输入对照 | 与 Golden 引擎逐位一致 | 同记录同 ID | ID 漂移或与 Golden 不一致 | P14-E-003 Golden 引擎对照 |
| P14E-P-M-003 | P14E-P-003 | 四类身份字段分类 | 机械字段集断言 | evidence 字段集 == 冻结集 | audit-only 不在 evidence_id 输入 | 分类漂移 | Golden G-001 对照 |
| P14E-P-M-004 | P14E-P-004 | ingestion_id 公式逐字继承 P14-B | 同输入对照 P14-B | production.ingestion_id == RawIngestRecord.ingestion_id | 相等 | 第二套公式 | P14-B RawStore 对照 |
| P14E-P-M-005 | P14E-P-005 | ingested_at 四维语义 + DUPLICATE 不分叉 | Golden G-002 同语义执行 | evidence_id/bundle_id 语义与 G-002 一致 | 无分叉 | duplicate attempt 分叉 | Golden G-002 |
| P14E-P-M-006 | P14E-P-006 | PIT 继承（含边界相等） | Golden G-003 同语义执行 | boundary 三元组行为一致 | == 可见 | 边界或 event_time 泄漏 | Golden G-003 |
| P14E-P-M-007 | P14E-P-007 | 选择链 + 两级枚举冻结 | Golden G-006 同语义执行 | reason/trace 枚举与 §7 一致 | 全枚举匹配 | 枚举外值或候选丢失 | Golden G-006 |
| P14E-P-M-008 | P14E-P-008 | post-as-of 内容零泄漏；四字段 exclusion | Golden G-004/G-007 同语义执行 | hash/id/payload 不在早 bundle | 零泄漏 | 任一泄漏 | Golden G-004/G-007 |
| P14E-P-M-009 | P14E-P-009 | mapping_key 冻结 + 1:1 + 无 orphan | Golden G-005 同语义执行 | 4 元组集合相等 + counts 相等 | 精确 1:1 | 集合不等/orphan | Golden G-005 |
| P14E-P-M-010 | P14E-P-010 | bundle 模型字段与参与性 | 机械 schema 断言 | 字段集与 §9 一致 | schema 精确 | 字段漂移 | 生产 Harness schema 检查 |
| P14E-P-M-011 | P14E-P-011 | canonical serialization 规范 | 同输入字节对照 | 与 Golden 引擎字节一致 | sort_keys/紧凑/unicode 不转义 | 序列化漂移 | Golden 引擎对照 |
| P14E-P-M-012 | P14E-P-012 | bundle_id 确定性 + 重复折叠 | Golden G-009/G-010 同语义执行 | 跨序同 ID；无重复 evidence | 确定性成立 | ID 漂移 | Golden G-009/G-010 |
| P14E-P-M-013 | P14E-P-013 | 持久化：append-only/幂等/reload 双重校验 | Golden G-009 同语义执行（含篡改负例） | reload 通过 + 篡改被拒 | 语义一致 | reload 漂移或篡改通过 | Golden G-009 |
| P14E-P-M-014 | P14E-P-014 | reverse trace 五类错误分类 | 负例矩阵（未找到/多匹配/身份不等/损坏行） | 各类独立触发对应错误 | 分类精确 | 全部归为 NOT_FOUND | 生产 Harness 负例 |
| P14E-P-M-015 | P14E-P-015 | tamper Cases A-F 检测矩阵 | 六篡改场景逐一执行 | 全部检出 | 检出且 fail-fast | 任一未检出 | 生产 Harness 篡改矩阵 |
| P14E-P-M-016 | P14E-P-016 | missing/failure 状态语义 | Golden G-003/G-008 同语义执行 | 空结果合法；fail-fast 场景一致 | 状态不合并 | 枚举合并/降级 bundle | Golden G-003/G-008 |
| P14E-P-M-017 | P14E-P-017 | provenance 失败整体 fail-fast | Golden G-008 同语义执行 | raise 且无持久化 | 无降级 bundle | 部分 bundle 产出 | Golden G-008 |
| P14E-P-M-018 | P14E-P-018 | 重放边界（双 ID 稳定） | Golden G-009 重放双跑 | result_id+bundle_id 稳定 | 确定性 | 环境字段泄漏 | Golden G-009 |
| P14E-P-M-019 | P14E-P-019 | adapter_version 参与双层身份 | 同 payload 异 adapter_version 构造 | ingestion_id 与 evidence_id 均不同 | 身份分叉（合法） | adapter_version 被忽略 | 生产 Harness 单元 |
| P14E-P-M-020 | P14E-P-020 | 契约版本/schema_version 绑定 | 机械版本断言 | bundle.schema_version == "p14e-evidence-bundle-1" | 绑定成立 | 版本漂移 | 生产 Harness schema 检查 |
| P14E-P-M-021 | P14E-P-021 | 反作弊键 + 调用形态禁止 | 机械源码扫描（剥 docstring/字符串） | 零命中 | 无违规 | 任一命中 | 源扫描 |
| P14E-P-M-022 | P14E-P-022 | API 面仅限 evidence/bundle 基础设施 | 公开符号扫描 | 无决策语义符号 | 面受限 | 决策符号出现 | 源扫描 |
| P14E-P-M-023 | P14E-P-023 | 生产实现与 Golden 引擎逐位一致 | 同输入双跑对照（fixtures 重放） | evidence_id/bundle_id/canonical 字节一致 | 逐位一致 | 任一不一致 | P14-E-003 fixtures 重放 |
