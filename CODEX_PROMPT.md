# 可直接复制给 Codex 的启动指令

你现在负责把这个工程实施成一个可运行、可测试、可持续迭代的 A-Stock Quantimental 2.0。

请先完整阅读：

- CODEX_START_HERE.md
- CODEX_IMPLEMENTATION_PLAN.md
- AGENT_RULES.md
- MIGRATION_MAP.md
- CODE_AGENT_TASK.md
- CODEX_EXECUTION_CHECKLIST.md
- docs/architecture.md
- docs/factor_spec.md
- docs/backtest_protocol.md
- docs/agent-contract.md
- src/astock_v2/**
- tests/**

如果工作区同时包含 V1，请完整检查：

- auto_main.py
- SKILL.md
- scripts/**
- README
- 旧 tests

第一阶段禁止直接大规模编码。

先输出：

1. 当前项目结构；
2. V1 → V2 映射；
3. 已实现；
4. 部分实现；
5. scaffold；
6. 缺失；
7. 数据源依赖；
8. 潜在数据泄漏；
9. P0 详细实施计划。

确认后严格按照 P0 → P8 实施。

每阶段：

- 写代码；
- 写测试；
- 运行测试；
- 更新 docs/progress/Px.md；
- 汇报实际状态；
- 再进入下一阶段。

不要为了让项目看起来完成而创建假的 provider、假的 realtime、假的新闻、假的财务数据或假的回测结果。

任何外部依赖无法访问时，标记：

BLOCKED_EXTERNAL_DEPENDENCY

任何只有接口没有真实实现的功能，标记：

SCAFFOLD_ONLY

任何尚未实现的功能，标记：

NOT_IMPLEMENTED

只有真实实现并且测试通过，才能标记：

IMPLEMENTED

特别注意：

- Point-in-Time；
- available_time；
- look-ahead；
- survivorship bias；
- calibration；
- OOS；
- T+1；
- 涨跌停；
- 停牌；
- slippage；
- transaction cost；
- correlated factors；
- proxy vs fact。

LLM 不能修改量化引擎的概率、收益、风险或回测结果。

第一阶段从 P0 开始。
