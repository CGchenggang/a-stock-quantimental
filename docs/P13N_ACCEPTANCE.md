# P13-N Acceptance Report — 每股 factor evaluation 热路径优化

- 日期：2026-09-29
- 仓库：`CGchenggang/a-stock-quantimental`
- 基线：`d3c0bc0`（交接所指的 4 个 P13-N 提交之顶）→ 本阶段终点 `d370149`
- 性能基线文档：`docs/P13N_PERFORMANCE_BASELINE.md`（commit `46c1bd9`）
- 环境与数据：与 P13-M/P13-N baseline 完全一致（本地 Windows / Python 3.11.5 / 91 只本地日线 / 1633 个交易日）
- 验收方：ChatGPT（本报告提交后由其复核；本报告不自行宣布 P13-N 完成）

## 1. Baseline（必须先说明的正确性前提）

交接的 4 个 P13-N 提交在本地**不可运行**：

| 提交 | 问题 |
|---|---|
| `cee172f`（remove typing runtime checks） | 只删了 `typing.Mapping/Sequence` import，`_rows` 的运行时 isinstance 仍在引用 → 每次因子调用 `NameError`，9 个测试失败 |
| `bd1eab7`（optimize PIT factor-row construction） | 调用了从未定义的 `_prepare_pit_updates` → 每次 factor-row 构建 `NameError`，2 个测试失败 |

`ddd8259` 恢复两者（`collections.abc` 运行时等价替换 + 按逐日 `admissible_at` 语义物化 admission 调度），恢复后 177 passed，且 000001/10-stock/76-stock 输出与 P13-M golden 逐行一致——据此建立真实 baseline：

| 运行 | exit | wall | 备注 |
|---|---|---|---|
| 000001 single | 0 | 8s | 1612 factor rows / 67 windows / 1340 OOS |
| 10-stock | 0 | 91s | pooled 12,940 OOS |
| 76-stock | 0 | 591s | pooled 94,760 OOS / 308 variant rows |
| peak RSS | — | — | 393MB（外部轮询） |

cProfile（000001，13.17s@cProfile）：533 万次 `_number` + 535 万次 abc isinstance —— 根因：**每天把全量 admitted 历史喂给只读尾部 ~21 行的因子**，O(days²) 行扫描；次级：每日 4 次重复的 `_rows`/gate 解析、O(N²) 前缀切片与 `None in` 扫描（133 万次 dataclass `__eq__`）。

## 2. Optimization commits（每项独立 benchmark + regression）

| commit | 内容 | 实测收益（干净计时） |
|---|---|---|
| `ddd8259` | P13-N: restore undefined hot-path pieces（正确性恢复，baseline 前提） | 不可运行 → 可运行；177 passed |
| `911178c` | **P0** 尾部 (lookback+2) 截窗 + 逐行 filter-proof 探针 + 全量回退 | 单股 8→**5s**；10 股 91→**59s**；cProfile 13.2→2.3s（5.7×）；golden factor rows 逐字节一致 |
| `9b28bda` | **P1** `normalize_time` lru_cache（纯函数、键=完整输入串） | 门控重复解析 ~8 次/日 → ~2 次/日；单股/10 股计时在噪声内（诚实记录：此改动收益小而确定） |
| `71172e3` | **P2** admitted 密集事件序列表（append/insort/原位修订替换） | dataclass `__eq__` 1.33M→**0**，O(N²) 切片消除；当前 1633 日规模下秒级收益在噪声内（结构性余量），10 股 59→62s（噪声） |
| `d370149` | docs: 峰值 RSS 采样器（workspace/bench_with_rss.py，诊断工具） | — |

未动的：`industry_relative.py`（P0-P2 均无需触及）、因子数学定义、pstdev 的 exact-Fraction 路径（换实现会改浮点语义，明确不做）、walk-forward 协议、label 定义、fit_predict（numpy，0.62s@cProfile，非热点）。

## 3. Benchmark table（优化后，全部干净计时）

| 运行 | exit | wall | vs baseline | vs P13-M |
|---|---|---|---|---|
| 000001 single | 0 | **5s** | 8s → 1.6× | 16s → 3.2× |
| 10-stock | 0 | **58.3s**（bench_with_rss 进程内计时） | 91s → 1.56× | 133s → 2.3× |
| 76-stock | 0 | **323s** | 591s → **1.83×** | 1101s → **3.4×** |
| 76-stock 复跑 | 0 | 333s（3% 噪声） | — | — |
| peak RSS（10 股，进程内 20Hz 采样） | — | **395MB** | baseline 393MB，持平 | — |

76-stock：308 variant rows 全在、零 traceback/KeyError、pooled 94,760 OOS、四种 variant 齐全；**全部 variant 行与 baseline 逐行 diff 为空**。

## 4. PIT 安全（缓存正确性论证与回归）

本阶段引入的两类缓存：

1. **尾部截窗（`911178c`）**——cache key 即"最后 lookback+2 行全部 filter-proof"这一探针条件：窗口行全部数值有效 ⇒ 无过滤器可删除窗口行 ⇒ 过滤后序列的尾部与全历史逐位一致；探针不满足即整体回退全历史输入。窗口外的行只可能影响诊断字段 `metadata["observation_count"]`（无任何管道消费者，LocalFactorRow 只保留 value/admissible）。
2. **`normalize_time` lru_cache（`9b28bda`）**——纯 string→string 映射，cache key = 完整输入串，命中必等价于重新解析；offset-exactness 有测试锁定（`08:00+08:00`→`00:00Z` 不与 `Z`/naive 形式坍缩）。

回归覆盖（映射到交接 §6 要求）：

| 要求 | 覆盖 |
|---|---|
| late revision（available 晚于当日 decision） | `test_late_revision_is_excluded_until_its_available_time`（d3c0bc0）+ `test_later_revision_does_not_hide_original_at_1600` + 等价性测试的 same-day 18:00 修订 |
| same event_time, different revision | 等价性测试的重复修订行；admission 调度的 max-revision 语义 |
| different available_time（跨日延迟） | 等价性测试的 next-day available 记录 |
| decision boundary（16:00 整点两侧） | `test_provider_pit_status_distinguishes_boundary_conditions`（现存）+ 上述 18:00 用例 |
| **新增强 PIT regression** | `test_windowed_fast_path_matches_full_rescan_reference`——把优化前的全量重扫算法作为可执行规格，在对抗数据（早期/窗口内/窗口外的病态 close/volume、同日晚到修订、跨日可用性）上要求**逐位一致** |

## 5. 等价性与可复现性（全部真实运行）

| 检查 | 结果 |
|---|---|
| 000001 golden factor rows（1612 行逐字节） | `cmp` 通过（baseline vs P0 vs P2 三个阶段全部一致） |
| 000001 metrics（baseline 指标 + industry_5/20/5_20） | 与 P13-M golden 逐位一致 |
| 10-stock variant 行 | 与 baseline/P13-M 逐行 diff 为空 |
| 76-stock variant 行（308 行） | 与 baseline/P13-M 逐行 diff 为空 |
| pooled == single（76 context 导出后精确比对） | 前 10 只 **10/10 PASS** + 全 universe 抽样（NR%7）**11/11 PASS**（含 000017 边界股） |
| repeated 76-stock run | context JSON **byte-identical**（diff 为空）；stdout 除 `--context-out` 路径回显外逐行一致 |

## 6. 全量测试

- 本地 `python -m pytest -q`：**179 passed / 0 failed**（baseline 时点 177，新增 2 个回归测试：窗口等价性、normalize_time 缓存语义）。
- 未删除或弱化任何既有测试。

## 7. GitHub Actions（最终 CI 门槛）

- push：`d3c0bc0..d370149 → main`
- run 36510332898（commit `d370149`）：**p13m succeeded（29s）**；**分支徽章 passing**（tests workflow 聚合 = pytest 与 p13m 双 job 均通过）。

## 8. Known limitations

- 单股 5s 中约 3.5s 是进程启动 + membership 解析 + pooled 单股 context；纯 factor-row 构建已降至亚秒级（cProfile 2.31s 含 walk-forward 0.7s）。
- `pstdev`（statistics.exact-Fraction）是当前 factor 构建的最大剩余项；任何替换都会改变浮点语义，按约束不做。
- `metadata["observation_count"]` 在截窗快路径下反映窗口长度而非全历史长度——诊断字段，无消费者；已在提交信息与本报告中声明。
- 76-stock 剩余耗时主要在 76× walk-forward 评估与每股启动开销，属协议层，不在本阶段范围。

## 9. Next-phase recommendation

1. ChatGPT 复核本报告（所有数字可由 `docs/P13N_PERFORMANCE_BASELINE.md` 的产物文件与 `data/industry/p13n_*` 本地运行记录重放）。
2. 评估把 `--context-out` + `verify_p13m_pooled_single.py` + 等价性测试纳入 CI（防止未来优化破坏 pooled==single 契约）。
3. 若需进一步压缩 76 股 wall time，下一步是 walk-forward 批量化（多股共享窗口矩阵），但必须保持逐股等价——建议作为 P13-O 的独立目标。
4. 因子有效性研究（P13-M 报告遗留）仍是最有价值的方向性工作。

## 10. Definition of Done 对照

```text
[x] 000001 optimized（8s → 5s）
[x] 10-stock optimized（91s → 58.3s）
[x] 76-stock optimized（591s → 323s）
[x] factor results unchanged（golden 逐字节 + 全部 variant 行逐行一致）
[x] PIT regression passed（等价性规格测试 + 晚到修订边界测试）
[x] pooled == single（21 只精确相等）
[x] repeated run identical（context JSON 逐字节）
[x] full pytest green（179 passed / 0 failed）
[x] GitHub Actions pytest green（run 36510332898，badge passing）
[x] GitHub Actions p13m green（29s succeeded）
[x] P13N_ACCEPTANCE.md committed（本文档）
[x] 所有关键性能数字有真实运行依据（data/industry/p13n_* 本地产物）
```
