# P13-N Performance Baseline

- 日期：2026-09-29
- 基线 commit：`ddd8259`（P13-N: restore undefined hot-path pieces left by prior optimization）
- 机器/环境：本地 Windows（Git Bash），Python 3.11.5，与 P13-M 验收同一环境
- 数据：`data/clean/cn_stock_daily`（91 只）、`validation_universe_76.txt`、SW1 membership CSV —— 与 P13-M 完全相同

## 0. 基线前必须说明的正确性修复

交接所指的 4 个 P13-N 提交（`bd1eab7..d3c0bc0`）**在本地是坏的**：

- `cee172f` 删除了 `typing.Mapping/Sequence` import，但 `factors/__init__.py` 的运行时 `isinstance` 检查仍在引用 → 每次因子调用 `NameError`（9 个测试失败）。
- `bd1eab7` 调用了从未定义的 `_prepare_pit_updates` → 每次 factor-row 构建 `NameError`（2 个测试失败）。

`ddd8259` 恢复两者：`_rows` 改用 `collections.abc`（运行时语义与 typing 别名完全一致），`_prepare_pit_updates` 按逐日 `admissible_at` 的语义物化为一次性的 availability 排序调度。修复后全量 pytest **177 passed**，且 000001/10-stock/76-stock 输出与 P13-M golden **逐行一致**（下表）。因此本 baseline 是修复后、进一步优化前的真实状态。

## 1. Baseline 数字（wall time 为 clean 运行，非 cProfile）

| 运行 | exit | wall | factor rows | windows | OOS predictions | variants |
|---|---|---|---|---|---|---|
| 000001 single | 0 | **8s** | 1612 | 67 | 1340 | 4 |
| 10-stock | 0 | **91s** | 47 行输出（10×4 variant） | — | pooled 12,940 | 4 |
| 76-stock | 0 | **591s** | 311 行输出（76×4 variant） | — | pooled 94,760 | 4 |

- peak RSS（外部 2s 轮询，覆盖 10+76 两次运行）：**393MB**
- 参照：P13-M 末期同一环境 000001=16s、10-stock=133s、76-stock=1101s —— `bd1eab7` 的增量 admission 已把整体从 1101s 降到 591s。
- 输出等价性：10-stock/76-stock 全部 variant 行与 P13-M golden 逐行 diff 为空；000001 metrics 与 P13-M golden 逐位一致（0.445522 / 0.528358 / 0.249821 …）。

## 2. cProfile（000001 factor rows + walk-forward，13.17s @ cProfile）

| 函数 | calls | tottime | 说明 |
|---|---|---|---|
| `factors/__init__.py:19 _number` | 5,329,272 | 2.09s | 每行每因子每天一次数值提取 |
| `builtins.isinstance` | 5,399,793 | 1.43s | 主要来自 `_rows` 的 per-row `isinstance(row, Mapping)` |
| `_rows` listcomp | 6,448 | 1.12s | 4 因子 × 1612 天 |
| `abc.__instancecheck__` + `_abc_instancecheck` | 5,350,228×2 | 1.77s | Mapping ABC 检查 |
| `fit_predict`（numpy walk-forward） | 67 | 0.74s | 模型训练，非热点 |
| `build_local_factor_rows` 自身 | 1 | 0.29s | 逐日调度 |

**结构性根因**：`ProviderResult.data` 每天携带**全量 admitted 历史**（第 i 天约 i 行），而四个因子只消费最后 `lookback+1/2` 行（`closes[-lookback-1:]` 等）。总行扫描 = Σ len(admitted) × 4 ≈ 1.3M 行/股，其中 >98% 是无用功。次级热点：per-factor 重复的 `_rows`/`gate_factor_inputs`（每日 4 次，含重复的 `datetime.fromisoformat`），以及 `admitted_by_event[:index+1]` 的 O(N²) 切片与 `None in` 扫描。

## 3. Baseline 产物（本地，data/industry/，gitignore）

- `p13n_golden_000001_factor_rows.json` —— 000001 全量 factor rows golden（1612 行，后续等价性对照）
- `p13n_baseline_000001.txt` / `p13n_baseline_10stock.txt` / `p13n_baseline_76stock.txt`
- Peak RSS 轮询记录：393MB

## 4. 优化约束（重申）

不改变 PIT 语义、因子数学定义、label 定义、walk-forward 协议、gap、decision time、available_time、revision 语义。每次优化独立 commit + 独立 benchmark + 独立 regression test。
