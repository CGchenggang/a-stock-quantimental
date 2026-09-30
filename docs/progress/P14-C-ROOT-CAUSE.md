# P14-C Root Cause Analysis

> 从 P14-C 初始实现到 R5 的全部独立验收发现中，追溯每个问题的根因。

## 方法

对 P14-C 初始实现（73f8dd8）到 R5（f7bd995）之间的全部验收发现，按以下分类：

- **A** Design Contract 缺失
- **B** Semantic definition 不明确
- **C** Fixture/Test design 错误
- **D** Implementation bug
- **E** Integration/E2E 缺失
- **F** CI/process 缺失
- **G** Documentation drift
- **H** Repository hygiene

每个问题回答："最初为什么没有在实现之前被发现？"

## Root Cause Matrix

| # | Issue | 首次发现 | 表面问题 | 根因 | 分类 | 应由 Contract 解决？ | 应由 Golden Test 解决？ | Implementation bug？ |
|---|-------|---------|---------|------|------|---------------------|----------------------|---------------------|
| 1 | Completeness expected set 从 actual payload 派生 | R1 验收 | `expected_entities = {p["entity_id"] for p in payloads}` | **实现前未冻结 expected contract 的 authority**——代码先写了 normalization/audit，completeness 只是附属输出，没有独立定义"什么应该存在" | **A** | ✅ EXPECTED_CONTRACT 必须独立于 payload 冻结 | ✅ missing date/entity 检测 | |
| 2 | SOURCE_ERROR 与 EXPECTED_ABSENCE 混淆 | R1 验收 | `broken_source` 同时标记为 SOURCE_ERROR 和 expected_absence=True | **Design Contract 缺失**——没有提前定义"什么算 source error"与"什么算 expected absence"的互斥边界 | **A+B** | ✅ 互斥关系必须冻结 | ✅ 两者不得同时出现在同一 source | |
| 3 | SOURCE_EMPTY 语义边界不清 | R2 验收 | `SOURCE_EMPTY` 与 `EXPECTED_ABSENCE` 混用 | **B**——没有定义"adapter 正常返回零 payload"与"contract 声明不需要数据"的区别 | **A+B** | ✅ | ✅ | |
| 4 | STALE 从硬编码 `stale_n = 0` 得出 | R1 验收 | source_health 输入的 stale 计数被硬编码为 0 | **A+D**——设计时未定义 freshness 与 source health 的连接方式；实现时忘了连接 | **A** | ✅ freshness policy 是唯一 STALE 来源 | ✅ | ✅ `stale_n = 0` 是实现 bug |
| 5 | Reconciliation 端到端 evidence 缺失 | R2 验收 | reconciliation.json 缺少 event_time/ingested_at/provenance 等字段 | **A+E**——设计时未冻结 reconciliation 输出的最低字段集 | **A** | ✅ 最低字段集冻结 | ✅ 端到端 artifact 断言 | |
| 6 | `_compute_freshness_per_record` FRESH/STALE 未导入 | R3 验收 | NameError: name 'FRESH' is not defined | **D**——实现时忘记 import；测试只覆盖了 happy path，没有覆盖所有代码路径 | | | | ✅ |
| 7 | `_compute_completeness` expected_absence 分支 UnboundLocalError | R3 验收 | expected_count 在 expected_absence 分支未初始化 | **D** | | | | ✅ |
| 8 | parse_failure_source 不在 EXPECTED_CONTRACT 中 | R3 验收 | completeness 无法对 parse_failure_source 计算 coverage | **A**——增加了新 source 但忘了更新 contract | **A** | ✅ 每个 source 必须在 contract 中注册 | | ✅ |
| 9 | Reconciliation E2E test 缺失 | R3 验收 | 测试只调 `reconcile()` 函数，不验证最终 JSON artifact | **E**——单元测试与 integration test 之间有 gap | **E** | | ✅ 端到端 artifact 断言 | |
| 10 | SOURCE_ERROR/PARSE_FAILURE durable evidence 未贯穿 | R2 验收 | `audit_event` 存在但 P14-C audit fixture 没有真正触发 adapter failure | **A+E**——没有预先定义"durable evidence chain 必须覆盖哪些异常" | **A** | ✅ 每种异常的 evidence chain 冻结 | ✅ | |
| 11 | Generated test artifacts 进入 git | R3 验收 | `tests/_p13s_immunity_tmp/` 等 11 个文件被 track | **H**——没有预先设置 .gitignore 排除规则 | **H** | | | ✅ .gitignore 遗漏 |
| 12 | `data/clean/` 等大规模数据进入 git diff | R3 验收 | 557 行 data/workspace 文件出现在 P14-C diff 中 | **H**——这些文件是 P13-M 时代的副产品，P14-C 未主动清理 | **H** | | | ✅ |
| 13 | CI run 不可独立验证 | R2/R3 验收 | `workflow_runs: []` / `statuses: []` | **F**——acceptance 查询用了短 SHA + Status API（Actions 用 check-runs 而非 status）；未认证 403 被映射为空 | **F** | | | ✅ 查询方法问题 |
| 14 | P14C_ACCEPTANCE.md 过时 | R3 验收 | 声称 "src diff = 空" 但实际有 501 行 src 修改 | **G**——acceptance report 写于实现初期，后续修改未同步更新 | **G** | | | ✅ |
| 15 | to_information_record 丢失 freshness_policy_id | R4 验收 | source_health 的 STALE 始终为 0 | **D**——`raw_store.py` 的投影硬编码 `freshness_policy_id=None` | | | | ✅ |

## 根因总结

### 主要根因分类统计

| 分类 | 数量 | 占比 |
|------|------|------|
| **A** Design Contract 缺失 | 7 | 47% |
| **B** Semantic definition 不明确 | 2 | 13% |
| **C** Fixture/Test design 错误 | 0 | 0% |
| **D** Implementation bug | 5 | 33% |
| **E** Integration/E2E 缺失 | 2 | 13% |
| **F** CI/process 缺失 | 1 | 7% |
| **G** Documentation drift | 1 | 7% |
| **H** Repository hygiene | 2 | 13% |

（部分 issue 属于多个分类，合计 > 15）

### 结论

> P14-C 反复返工的**主要问题**是 **A（Design Contract 缺失）**，占全部根因的约 47%。
> 这意味着：如果在写代码之前先冻结一份 Design Contract（expected set 独立性、
> missingness taxonomy、durable evidence chain、reconciliation 最低字段集），
> 大部分 R1-R5 返工本可避免。

**实现问题**（D 类，5 个）虽然也是真实 bug，但它们是"有了 Contract 之后测试就能
发现的问题"——不是"没有 Contract 就根本不会想到要测试的盲区"。

**R3 是一个分水岭**：R3 的 7 项发现中，6 项属于 D（实现 bug），说明 R1-R2 修复后
代码质量已经提升，剩下的是工程质量问题而非设计盲区。但 R1 的 5 项发现中 4 项
属于 A（Design Contract 缺失），说明最初的设计就没有定义清楚。

**核心教训：先冻结 Contract，再写代码。**
