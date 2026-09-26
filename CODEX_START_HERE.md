# A-Stock Quantimental 2.0 — Codex 开工说明

第一轮不要直接大规模编码。先盘点 V1、V2 scaffold、测试、数据依赖、假实现和迁移风险，然后严格按 P0→P8 实施。

最终架构：
多源数据 → Point-in-Time → 数据质量 → 因子 → 去相关/标准化 → A股 Market Regime → 概率模型 → 风险模型 → Walk-forward/OOS → Recommendation Ledger → AI Research Agent → 研究报告/风险解释/证据整理。

LLM 负责信息理解、事件分类、证据整理、矛盾证据、报告、风险解释和复盘；不能修改量化概率、因子权重、收益、风险或回测结果。

每阶段必须编码、测试、更新 docs/progress/Px.md，并明确已完成、未完成、风险和下一阶段。不能用假数据把状态伪装成 IMPLEMENTED。

核心验收：
pytest -q
python -m astock_v2.cli init
python -m astock_v2.cli demo 000001
python -m astock_v2.cli backtest --csv data/sample_ohlcv.csv
