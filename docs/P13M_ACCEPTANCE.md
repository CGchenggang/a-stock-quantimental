# P13-M Acceptance Report — SW1 历史成员 + PIT-safe 行业相对强弱因子

- 日期：2026-09-28（本地时间）
- 仓库：`CGchenggang/a-stock-quantimental`（本地 `E:\git-ground\a-stock-quantimental`）
- 基线 HEAD：`fe975cf92c39f46fd040efd7aaed62c0e72a931e`（Fix pooled membership date normalization）
- 执行方：zcode（按 `ZCODE_AStock_Quantimental_Handoff_20260928/` 交接推进）
- 重要约定：**按用户要求本次只修改本地仓库、不推送 GitHub**。因此"CI 绿色"以本地全量 pytest 等价验证；GitHub Actions 结果将在下次推送时产生（见 Limitations R1）。

---

## 1. 数据来源与覆盖

| 项 | 值 |
|---|---|
| 官方申万历史成员 XLS | `data/industry/StockClassifyUse_stock.xls`（Sheet1，12925 行 × 4 列：股票代码/计入日期/行业代码/更新日期） |
| PIT membership CSV | `data/industry/sw_official_sw1_membership_all.csv`（12925 条成员记录，5930 只唯一股票，38 个申万一级行业） |
| 价格库 | `data/clean/cn_stock_daily/<symbol>.jsonl`（91 只本地股票，每股约 1633 个交易日，event≈15:00 / available=当日 16:00 +08:00） |
| 验证集 | `data/industry/validation_universe_76.txt`（76 只，唯一；`000156`、`000428` 无官方 SW1 历史，作边界用例） |
| 交易日覆盖 | 1633 个 event days（约 2019 → 2026-09） |

## 2. PIT 规则（未改动，全部保持）

- `effective_from` = 变更/计入日期当天 00:00 +08:00
- `effective_to` = 下一次变更日期当天 00:00 +08:00
- `available_time` = 下一自然日 16:00 +08:00（项目保守约定，不声称真实发布时间）
- 第一条历史记录之前不向前推断行业；不用当前行业回填历史；历史 peer return 按当时可用 membership。

本次优化新增的 PIT 论证（已实现并在测试中锁定）：return day **早于** decision day 时，effective-day 的 `on_or_before` membership 映射与决策时间无关，可安全跨决策日缓存；return day **等于** decision day 时必须使用排除当日生效（尚未 available）的 `before` 映射，且不得缓存。缓存按 `_advance_pit_return_state` 报告的"脏日"失效，晚到 revision 会正确使受影响日期的聚合失效。

## 3. P7 修复：RecommendationLedger / DecisionPacket API（范围外发现一并修复）

CI run `36440420036` 的 pytest job 失败根因（三个真实实现 bug，测试为规格、无生产调用方）：

1. `append()` 用 `dict(record)` 序列化 dataclass（`DecisionPacket` 不可迭代）→ TypeError。修复：`as_dict()` 优先，否则 `dataclasses.asdict()`。
2. `feature_version` 被声明为 keyword-only，而 P7 规格允许位置传参（`ledger.append(p, "f1")`）。
3. **交接未发现的新 bug**：`_append` 写的是字面量 `"\\n"`（反斜杠+n），JSONL 无真实换行，`load()` 解析必然失败（`test_ledger_append_only` 的 `json.de...` 错误）。

统一后的 API：`append()` 返回并落盘扁平事件（record 字段在顶层 + `feature_version` + `input_snapshot` + `outcomes={}`）；outcome 以追加式事件落盘（磁盘不可变），`load()` 读取视图按 `(symbol, decision_time)` 把 `T+n` outcomes 合并回 recommendation 行；`backfill_returns` 按顶层字段匹配。**未修改任何测试。** `tests/test_agent_ledger.py`、`test_p7_integration.py`、`test_ledger_append_only.py`、`test_ledger_metrics.py` 全部通过。

## 4. pooled 性能定位与修复（核心工作）

### 4.1 测量（不凭感觉）

- 旧代码 10 股 benchmark：exit 0，**410s**（其中 pooled context 构建约 390s）。
- 阶段计时：membership 载入 0.15s、记录载入 1.52s（123,793 条）、PIT state 0.22s、历史 membership 预计算 0.05s —— **~100% 耗时在 pooled 决策日主循环**。
- cProfile（旧代码）：`build_universe_industry_relative_context_maps` 622.78s，其中函数自身 380.9s + **13.3 亿次 `dict.get`（219.3s）**。
- py-spy 30s 行级采样（50Hz，1499 样本）：**~91% CPU 落在旧实现的 fallback 深扫描循环**（对 60 天以前的旧 return day 逐个 × 全部 76 股查 membership；memo 仅单决策日有效，跨日全部重算）。
- 峰值内存（旧代码，外部轮询）：642MB（cProfile 下）。历史"10GB/数十分钟"问题在 `e8a9d44` 后已不复现。

### 4.2 修复（语义保持）

`src/astock_v2/industry_relative.py`：

1. **跨日全局聚合缓存** `(return_day, industry_code) → (sum, count)`：历史日聚合与决策时间无关，一次计算全程复用；按 `_advance_pit_return_state` 新返回的"脏日集合"精确失效（晚到 revision/补数据安全）。
2. **peer 扫描精确裁剪**：只遍历 `symbols_by_ever_code[code]`（曾持有该行业代码的股票，保持 universe 顺序 = 单股构建器求和顺序），替代原来的全 universe 扫描。
3. **decision day 当日聚合不缓存**（保持 available 语义），候选日列表改为增量维护（新增/删除仅来自 advance 报告的变更日），消除每决策日 12.4 万次迭代的集合重建。
4. 统一 recent/fallback 双循环为单一 newest-first 扫描，保留单股构建器的精确选日顺序。

### 4.3 效果

| 指标 | 旧实现 | 新实现 |
|---|---|---|
| pooled context 构建（76 universe，干净计时） | ~390s | **12.1–13.1s（~32x）** |
| cProfile 下 pooled 构建 | 622.78s | 40.56s |
| 10 股 benchmark 端到端 | 410s | **133s** |
| 76 股 benchmark 端到端 | 未完成（历史数十分钟/中断） | **1101s（18.4 min），exit 0** |
| 峰值 RSS（pooled 构建） | 642MB（cProfile 下） | **394MB**（20Hz 采样） |
| context 行数 / 有效目标 | 114,683 / 74 | **114,683 / 74（完全一致）** |

76 股剩余耗时的 ~90% 在每股评估（`build_local_factor_rows` 的因子计算，单股 ~12s；热点 `factors/__init__.py:16` 的 typing `__subclasscheck__`），与 pooled 构建无关 → 下一阶段优化点。

## 5. 真实验收记录

产物均为本地文件（`data/industry/` 在 `.gitignore`，不入库）：

| 运行 | 文件 | exit | wall | 输出 |
|---|---|---|---|---|
| 单股 000001 | `p13m_000001_single_v2.txt` | 0 | 16s | 1612 factor rows / 67 windows / 1340 OOS |
| 4 股 | `p13m_4stock_real_run.txt` | 0 | 71s | 16 variant 行 + pooled |
| 10 股（新代码，正式） | `p13m_10stock_real_run_v4.txt` + `p13m_10stock_context.json` | 0 | 133s | 40 variant 行，pooled 12,940 OOS |
| 10 股（旧代码基线） | `p13m_10stock_real_run.txt` | 0 | 410s | 40 variant 行，pooled 11,600 OOS（请求集少 000001） |
| 10 股复跑 | `p13m_10stock_real_run_v5.txt` + `p13m_10stock_context_rerun.json` | 0 | 140s | 与 v4 全等 |
| 76 股（正式） | `p13m_76stock_real_run.txt` + `p13m_76stock_context.json` | 0 | **1101s** | **308 variant 行（76×4），pooled 94,760 OOS**，零 traceback/KeyError |

判定标准逐项满足：exit code 0、输出非空、baseline / industry_5 / industry_20 / industry_5_20 全出现、pooled 统计存在、无 traceback / KeyError、耗时已记录。

边界行为：`000156`、`000428`（无 SW1 历史）在 76 股运行中产 0 行（打印 nan 占位行），被正确跳过且不影响其他股票 —— 无 KeyError（`current_membership.get()` 语义保持）。

## 6. pooled == single（正确性）

1. **合成数据单测**：`tests/test_industry_relative.py::test_pooled_context_matches_single_stock_context` —— 4 只股票 pooled 与独立 single 精确相等 + 复跑 pooled 完全相等。**通过（优化前后均通过）。**
2. **真实数据精确校验**（新工具 `scripts/verify_p13m_pooled_single.py`，对照 `--context-out` JSON）：
   - 10 股正式运行 context：**10/10 精确相等**（每个 decision day、每个因子值 `==`）。
   - 76 股 context 抽样 11 只（含首尾/边界）：**11/11 精确相等**。
   - 000001 专项：pooled 1613 日 context 与 single 完全相等（0 行差异）。
3. **端到端指标一致**：000001 在 10 股 pooled 运行、76 股 pooled 运行、独立单股运行三次的 baseline 指标**逐位一致**（accuracy 0.445522 / brier 0.249821 / log_loss 0.692873 …），且与交接前的历史单股 debug 文件 `p13m_000001.txt` 一致。
4. **新旧实现等价**：新代码 10 股运行的全部 40 行 variant 指标与旧代码输出**逐字节一致**（context 行数 114,683/74 亦一致）。

## 7. 可复现性（repeated pooled == identical）

- 10 股正式运行复跑一次：**context JSON 逐字节相同（`cmp` 通过）**，stdout 46/46 行全等（唯一差异为 `--context-out` 路径回显）。
- 跨运行规模稳定性：10 股运行与 76 股运行的 10 个重叠 symbol 的 context **全部逐字段相等** —— pooled 结果不依赖请求集。
- 旧代码也复跑过一次（v2/v3，9 股请求集）同样逐字节一致。

## 8. 四种 factor variant 与 OOS 指标

协议：252 train / 20 test / 20 step / 1 gap；logistic 500 epochs；同一配对样本。

**76 股 pooled（94,760 OOS 预测）**：

| variant | accuracy | brier | log_loss | Δaccuracy | Δbrier | Δlog_loss |
|---|---|---|---|---|---|---|
| baseline | 0.522932 | 0.250401 | 0.694463 | — | — | — |
| industry_5 | 0.522984 | 0.250403 | 0.694467 | +0.000602 | +0.000824* | +0.002142* |
| industry_20 | 0.522246 | 0.250417 | 0.694496 | −0.001340 | +0.000837* | +0.002172* |
| industry_5_20 | 0.522404 | 0.250419 | 0.694501 | −0.001182 | +0.000839* | +0.002176* |

\* Δbrier/Δlog_loss 为相对 baseline 的差值（正值表示劣于 baseline；brier/log loss 越低越好）。

**10 股 pooled（12,940 OOS 预测）**：baseline 0.537403/0.249519/0.693077；industry_5_20 accuracy Δ+0.000696。

结论（如实）：在本验证集上，行业相对因子的 pooled OOS 提升**接近零且方向不一致**（accuracy Δ 在 ±0.14% 内，brier/log loss 略劣于 baseline）。单股层面部分股票为正（如 000016 +0.006、000009 +0.003），部分为负（000017 −0.014、000010 −0.005）。**因子当前不构成可依赖的 alpha 证据**；本次工程目标是让评估管线可复现、可审计，因子有效性留待后续样本外验证。

## 9. 测试与"CI"状态

| 项 | 基线 HEAD `fe975cf` | 本次工作后 |
|---|---|---|
| P13-M 单测（`test_industry_relative` 等 13 项） | 通过 | **通过** |
| P7 ledger 测试（4 个文件） | **3 失败** | **全部通过（实现修复，未改测试）** |
| 本地全量 pytest | 22 failed / 154 passed | **19 failed / 157 passed**（净修复 3 个，失败集合逐条比对确认） |
| GitHub Actions | p13m job success；pytest job failure（P7） | **未推送，无法产生新 run**（见 R1） |

本地剩余 19 个失败**全部为 HEAD 上既已存在**，与本次改动无关（失败集合 diff 证明），集中在 legacy/P8/provider 区域：`test_cli_research`(1)、`test_legacy_market_inputs`(4)、`test_legacy_market_provider_impl`(3)、`test_metrics`(1)、`test_p8c_legacy_intraday_semantics`(1)、`test_p8d_orchestration`(3)、`test_p8d_research_bridge`(2)、`test_provider_research`(3)、`test_review`(1)。多数不在任何 CI step 覆盖内；抽样诊断显示为真实行为/契约分歧（时区字符串比较、regime 默认值、浮点 `==` 断言等），需要结合 P8 历史逐个判定实现与测试谁对 —— **不在本次交接范围，未做"改测试变绿"处理**。

## 10. 本次代码变更清单

| 文件 | 变更 |
|---|---|
| `src/astock_v2/ledger.py` | P7 统一 API：asdict 序列化、位置参数 feature_version、修复 `"\n"` 换行、扁平事件 + 读视图 outcomes 合并、追加式 outcome 事件 |
| `src/astock_v2/industry_relative.py` | pooled 构建：跨日聚合缓存 + 脏日失效、ever-code peer 裁剪、增量候选日、单循环统一；`_advance_pit_return_state` 返回脏日集合（向后兼容） |
| `scripts/run_local_industry_relative_oos.py` | 新增 `--context-out`（审计导出）；`--symbol` 规范化（`lstrip("\ufeff")`，修 BOM 请求漏洞） |
| `scripts/profile_p13m_pooled.py` | 新增：阶段计时 + cProfile 剖析（诊断工具，不改生产语义） |
| `scripts/verify_p13m_pooled_single.py` | 新增：真实数据 pooled==single 精确校验工具 |

## 11. Limitations / 风险

- **R1 CI 未验证**：按用户指令未推送。p13m job 内容（`tests/test_industry_relative.py`）本地通过；但 CI pytest job 修复 P7 后会继续跑到 P8 step，其中的 `test_p8c_legacy_intraday_semantics`、`test_p8d_orchestration` 在本地 HEAD 即失败 —— 若在 Ubuntu 同样失败，**推送后 CI pytest 仍将红**，需先处理第 9 节的 19 个 pre-existing 失败（或确认其 Ubuntu 表现）。
- **R2 76 股评估耗时**：1101s 中 ~90% 在每股因子计算（`factors/__init__.py:16` typing 判断热点），pooled 构建仅 13s。扩大 universe 前应先优化评估路径。
- **R3 数据边界**：`000017` 等股票 SW1 历史存在但截至 2022 年（membership 已封口）；`000156/000428` 无 SW1 历史。价格库仅 91 只，行业 peer 池受限于本地 universe。
- **R4 因子有效性**：见第 8 节，当前无 pooled alpha 证据。

## 12. Next Phase（建议顺序）

1. 19 个 pre-existing pytest 失败的专项修复（P8/legacy 契约逐个判定，先 Ubuntu/Windows 差异分层）。
2. 推送后核对 GitHub Actions 两个 job（p13m + pytest）全绿。
3. 每股评估路径优化（`factors/__init__.py` 的每行 isinstance/typing 开销），目标 76 股端到端 < 5 min。
4. 行业相对因子的有效性研究（分行业/分 regime 分组、更长验证窗口、换手与成本）。
5. 将 `--context-out` + `verify_p13m_pooled_single.py` 纳入常规回归（可加入 CI）。

## 13. Definition of Done 对照

```text
[x] git synchronized（本地 HEAD = fe975cf 基线 + 本次本地提交；按指令未推 GitHub）
[x] 10 stock real run passed（exit 0 / 133s / 12,940 pooled OOS）
[x] 76 stock real run passed（exit 0 / 1101s / 94,760 pooled OOS / 308 行）
[x] pooled == single（单测 + 真实数据 21 只精确相等 + 000001 三路逐位一致）
[x] repeated pooled == identical（context JSON 逐字节一致）
[x] P7 pytest fixed（实现修复，未改测试）
[~] full pytest green —— P7 已修；另有 19 个 HEAD 既有的范围外失败（第 9 节），未擅自处理
[~] CI green —— 本地等价验证通过；GitHub Actions 需推送后产生（R1）
[x] P13M_ACCEPTANCE.md committed（本文档）
```
