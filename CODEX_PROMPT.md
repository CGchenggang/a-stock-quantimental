# 可直接复制给 Codex 的启动指令

你现在负责把这个工程实施成一个可运行、可测试、可持续迭代的 A-Stock Quantimental 2.0。

请先阅读 CODEX_START_HERE.md、CODEX_IMPLEMENTATION_PLAN.md、AGENT_RULES.md、MIGRATION_MAP.md、CODE_AGENT_TASK.md、CODEX_EXECUTION_CHECKLIST.md、docs/**、src/astock_v2/**、tests/**，以及 V1 的 auto_main.py、SKILL.md、scripts/**。

第一阶段先审计，不要假装 scaffold 已完成。严格 P0→P8：每阶段编码、测试、更新 docs/progress/Px.md，并真实标记 IMPLEMENTED/PARTIAL/SCAFFOLD_ONLY/NOT_IMPLEMENTED/BLOCKED_EXTERNAL_DEPENDENCY。

禁止虚构 provider、realtime、新闻、财务、资金流或回测；严格防止 PIT/look-ahead/survivorship leakage；概率必须经过 OOS + calibration 才能解释；回测考虑 T+1、涨跌停、停牌、滑点和交易成本；LLM 不得修改量化引擎数值。

最终验收：pytest -q；python -m astock_v2.cli init；python -m astock_v2.cli demo 000001；python -m astock_v2.cli backtest --csv data/sample_ohlcv.csv。
