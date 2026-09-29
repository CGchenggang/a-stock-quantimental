# P13-U Acceptance Report — Virgin Holdout Data Accumulation & Integrity Gate

- 日期：2026-09-29
- 基线：`8dcd4eb`（P13-S 验收终点）
- 文档：`docs/P13U_RESEARCH_PLAN.md`、`docs/P13U_PIT_AUDIT.md`
- 产物：`data/industry/p13u/`（6 个 JSON，双次运行 byte-identical）
- 状态：**implementation complete; awaiting independent acceptance**——PASS 由外部验收判定。

## 1. What was tested

Research-only 数据完整性闸门：冻结 P13-T 判定的边界（research_end=2026-09-22 / virgin_start=2026-09-23），扫描 76-stock 价格库的 virgin zone（仅存在性/完整性，零性能指标），双层污染检测（consumed dates + 研究产物扫描），symbol-clustered 之外的 gate 状态机（ACCUMULATING/READY_MINIMUM/READY_RECOMMENDED/BLOCKED），frozen manifest（边界 + 7 个冻结文件 SHA256），以及接入 P13-Q/P13-R 入口的 fail-fast research-zone guard。

**P13-T NOT YET EXECUTED. P13-U confirms whether the virgin holdout is accumulating safely.**

## 2. 当前 Gate 状态（真实运行）

| 项 | 值 |
|---|---|
| research_end（冻结） | 2026-09-22 |
| virgin_start（冻结） | 2026-09-23 |
| latest_research_consumed_date | 2026-09-22 |
| latest_available_data_date | 2026-09-24 |
| **virgin_trading_days** | **2** |
| **gate_status** | **ACCUMULATING** |
| **contamination_detected** | **False** |
| p13_t_executable_minimum（≥20 天） | False |
| p13_t_executable_recommended（≥60 天） | False |
| 缺失数据 | 09-23/09-24 各缺 `000004`、`000016`（coverage.json 如实报告，不删股票） |

## 3. Frozen Manifest（`frozen_manifest.json`，SHA256 前 16 位）

| 冻结文件 | SHA256 |
|---|---|
| universe_file（validation_universe_76.txt） | 8fa347df1b06a843 |
| p13o_audit（consumed 边界事实来源） | c60fac96d0611b6b |
| p13q_calibration_registry | 643a3dcd2c53a944 |
| p13r_policy_registry | 361791f8bf072778 |
| p13r_analysis_config（cost/risk assumptions） | 6a0b5b9e000c3c01 |
| p13s_report_schema | a4e4c5ebc56ad837 |
| p13t_determination | e97108690caf98d2 |

（映射说明：任务文字中的 cost_assumption/risk_assumption 由 `p13r_analysis_config`（cost_scenarios）与 `p13r_policy_registry`（risk_constraints）承载；无独立的 PIT contract 文件——PIT 契约由 P13-T 判定文档与各阶段 PIT audit 承载，均列入 frozen_hashes。未虚构任何 hash。）

## 4. Research-zone guard（防研究消费）

`assert_research_zone` 已接入 P13-Q/P13-R 分析入口：任何 `decision_time ≥ 2026-09-23` 的行 → `ValueError("VIRGIN HOLDOUT DATA CANNOT BE CONSUMED BY RESEARCH PIPELINE ...")` fail-fast。最小修改（两处 import + 两行调用），语义零变化，56 个 P13-Q/R/S 既有测试全部通过（回归锁定）。未来 P13-T 评估须显式知情豁免该 guard。

## 5. Verification Results

| 项 | 结果 |
|---|---|
| 全量 pytest | **261 passed / 0 failed**（243 + 18 新增） |
| P13-U dedicated tests | **18 passed**（覆盖交接 §16 的 25 项要求：边界冻结×2、virgin 识别×3、gate 阶梯×5、缺失检测×2、污染×2、边界不移动×1、future immunity×1、确定性×1、hash×3、policy/calibration 不可改×2、无指标×1、无推荐×1、factor 快照×1、guard×3） |
| Reproducibility | **byte-identical = yes**（6 个产物双次运行 cmp 全过；无时间戳/UUID） |
| Future-row immunity | **pass**（`test_research_end_does_not_move_with_future_data`：数据到 2026-10-10 边界不动；`test_frozen_manifest_immune_to_future_rows`） |
| Production diff | `git diff 77594d9a..HEAD -- src/astock_v2` = **空** |
| 污染状态 | **contamination_detected = False**（未发生 VIRGIN HOLDOUT CONTAMINATION DETECTED 停止条件） |

## 6. CI（已核验，客观事实）

- **Workflow**: tests；**Run ID**: 36591228302；**Commit**: `96a2aae`（push 触发）
- **pytest job**: success —— 含 `Full pytest suite` step（实际命令 `python -m pytest -q -ra`）= **success**；P13-M pooled regression step success
- **p13m job**: success
- **P13-U coverage**: `pytest --collect-only tests/test_p13u_holdout_gate.py` = 18 tests collected，全部被 full suite 执行（全量 261 = 243 + 18）
- 过程说明：首个 P13-U commit（1f3b9a3）曾因遗漏提交两个入口文件的 guard 修改而使 CI pytest job 失败（run 36590048778）；补提交 `96a2aae` 后全绿。核验 URL：https://github.com/CGchenggang/a-stock-quantimental/actions/runs/36591228302

## 7. Known Limitations

- 运行时的数据读取行为无法从产物检测；污染检测覆盖"研究产物中出现 virgin decision_time"这一可审计事实（文档声明）。
- 交易日判定基于 universe 内实际数据（无外部交易日历）；节假日/停牌表现为 missing_symbols，如实报告。
- `expected=76` 含两只无 SW1 membership 的股票（000156/000428）——它们在价格库中的存在性仍被检查（数据完整性），只是不产生 factor/OOS 行。

## 8. P14 预告衔接

P13-U 完成后，virgin holdout 的积累由本 gate 持续监控（数据每推进一天重跑一次即得最新状态）。下一阶段 P14（Multi-Market Information Infrastructure）与 virgin holdout 保护正交：P14 的新数据源接入必须同样遵守 `assert_research_zone` guard。

## 9. Git Commits（本阶段）

| commit | 内容 |
|---|---|
| feat: add P13-U virgin holdout integrity gate | gate 脚本 + guard 接入 |
| test: add P13-U holdout gate tests | 18 项 |
| docs: add P13-U research plan, PIT audit and acceptance | 本报告 |

（最终 HEAD SHA 与 CI run ID 以推送后为准，详见 §6；P13-U 不自行宣布 PASS，P13-T 亦未执行。）
