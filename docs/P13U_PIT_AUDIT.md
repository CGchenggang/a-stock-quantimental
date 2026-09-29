# P13-U PIT Audit — Virgin Holdout Integrity Gate

- 日期：2026-09-29
- 范围：P13-U（`scripts/run_p13u_gate.py`，产物 `data/industry/p13u/`）+ 接入 P13-Q/P13-R 入口的 research-zone guard

## 1. 输入数据边界

Gate 只读取两类数据：(a) 本地价格库 `data/clean/cn_stock_daily/`（76-stock universe 范围内），仅提取 `event_time` 日期与 symbol 存在性——**不读取、不聚合任何价格/收益数值**；(b) P13-O audit 的 decision_time 集合（已消费边界的事实来源）。hash 输入为冻结文件的字节（universe、两个 registry、cost-risk config、P13-S schema、P13-T 判定文档）。

## 2. decision_time / data_available_time

冻结边界 `RESEARCH_END=2026-09-22`、`VIRGIN_START=2026-09-23` 为模块常量（只可通过代码编辑修改，可审计），frozen_manifest 记录其值。gate 不从 latest data date 推导边界（`test_research_end_does_not_move_with_future_data` 锁定 2026-10-10 场景下边界不动）。

## 3. Freshness rule

P13-U 不计算 freshness（那是 P13-S 报告层职责）；gate 自身的日期语义只有 virgin/非 virgin 与数据存在性。

## 4. Future-row immunity

`test_frozen_manifest_immune_to_future_rows`：向数据追加新 virgin 行后，frozen_manifest 的边界与 hash 不变；`test_research_end_does_not_move_with_future_data`：数据推进到 2026-10-10 时 research_end/virgin_start 不移动。研究产物扫描（污染检测）只读不写。

## 5. Report generation boundary

gate 输出仅含存在性/完整性信息（日期、计数、hash、状态）。结构断言测试（`test_no_performance_metrics_or_recommendations`）锁定输出不含 accuracy/brier/log_loss/hit_rate/recommendation/policy_metrics 任何字样——**P13-U 不产生任何具有研究含义的聚合指标**。

## 6. 自然语言生成为何不引入未来信息

`render_markdown` 类的模板渲染在本阶段不存在（gate 无人类可读报告渲染需求）；全部输出为 JSON 结构化事实。不存在自由文本生成路径，因此不存在通过生成内容引入未来信息的通道。

## 7. Research pipeline guard

`assert_research_zone` 已接入 P13-Q/P13-R 分析入口：任何 `decision_time ≥ 2026-09-23` 的行进入研究管线即 `ValueError("VIRGIN HOLDOUT DATA CANNOT BE CONSUMED BY RESEARCH PIPELINE ...")` fail-fast（测试锁定，含边界日期 2026-09-22 仍放行的 exclusive 语义）。该 guard 属 §18 允许的通用 infrastructure 最小修改：不加策略、不改语义、纯 fail-fast，回归测试 56 个 P13-Q/R/S 测试全部通过。

## 8. 已知边界

- 运行时的数据读取行为（谁在何时读了 virgin 行）无法从产物检测；污染检测覆盖"研究产物中出现 virgin 日期"这一可审计事实。
- `000004`、`000016` 在 09-23/09-24 缺数据，gate 如实报告（coverage.json），不视为污染、不删除股票。
