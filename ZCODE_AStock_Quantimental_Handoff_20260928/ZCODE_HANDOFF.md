# A-Stock Quantimental → zcode 工程交接

更新时间：2026-09-28 仓库：`CGchenggang/a-stock-quantimental`
本地目录：`E:\git-ground\a-stock-quantimental`
当前主线：P13-M（申万一级行业历史成员 + PIT-safe 行业相对强弱因子）

## 1. 目标

zcode 接管后续工程推进。用户不再充当反复试错的执行器。

最终目标： 1. 完成 pooled 多股票共享上下文的性能定位与修复。 2. 保证 PIT
语义不被优化破坏。 3. 先 10 股真实验收，再 76 股真实验收。 4.
结果必须有真实输出、退出码、耗时和统计。 5. CI 验证代码回归。 6.
修复当前完整 pytest 中已确认的 P7 `RecommendationLedger` API/test
不一致。 7. 形成 P13-M 最终验收报告。

## 2. 当前 Git

最新提交：

`fe975cf92c39f46fd040efd7aaed62c0e72a931e`

`Fix pooled membership date normalization`

此前关键提交： - `e8a9d448e51606e4df28909fa7ff60d73e1741cb` ---
`P13-M: precompute pooled historical memberships` -
`1237ea877543fffab9d1c4bdaaab45e5829adb0b` ---
`Fix P13-M missing SW1 membership symbols` -
`ad26433931292919aba0decbc60ccd66e602ed9a` ---
`Fix P13-M universe file BOM handling`

## 3. CI 真实状态

最近相关 workflow run：

`36440420036`

### p13m

job `108989138914` `completed / success`

P13-M pooled regression 已通过。

### pytest

job `108989138682` `completed / failure`

失败原因是已经确认的 P7 Ledger API/test mismatch，不是当前 P13-M pooled
修复本身：

问题 A： `RecommendationLedger.append()` 对 `DecisionPacket` 使用：

``` python
row=record.as_dict() if hasattr(record,"as_dict") else dict(record)
```

`DecisionPacket` 没有 `as_dict()`，`dict(record)` 不可用。

问题 B： 测试调用：

``` python
ledger.append(p, "f1")
```

而实现是：

``` python
append(self, record, *, feature_version="unknown", input_snapshot=None)
```

第二个参数为 keyword-only。

zcode 应检查所有调用方后决定兼容层还是统一 API，不能只改测试骗绿。

## 4. P13-M 数据

官方申万一级行业历史成员 XLS：

`data\industry\StockClassifyUse_stock.xls`

已确认： - Sheet1 - 12925 x 4 - 股票代码 / 计入日期 / 行业代码 /
更新日期 - 约 5930 股票 - 38 个申万一级行业

导入： - `data\industry\sw_official_sw1_membership_all.csv` -
`data\industry\sw_official_industry_history_raw_all.csv`

## 5. PIT 规则（禁止擅自改变）

-   `effective_from` = 变更/计入日期当天 00:00 +08:00
-   `effective_to` = 下一次变更日期当天 00:00 +08:00
-   `available_time` = 下一自然日 16:00 +08:00

`available_time` 是项目保守的 PIT 安全约定，不声称是真实源数据发布时间。

规则： 1. 第一条历史行业记录之前不得向前推断行业。 2.
不得用当前行业向历史回填。 3. 历史 peer return 必须按当时可用
membership。 4. 性能优化不得改变最新有效行业成员的选择语义。

## 6. 76 股票验证集

文件： `data\industry\validation_universe_76.txt`

共 76 个，唯一，无重复。

之前排除严重不完整文件：
`000005 000018 000023 000038 000413 000416 000585 000780`

部分股票有价格但没有官方 SW1 历史，例如 `000017`。 此前 pooled
代码直接索引：

``` python
target_membership = current_membership[symbol]
```

导致： `KeyError: '000017'`

已修复为 `.get(symbol)`，没有 PIT-safe membership 时跳过。

## 7. 已确认性能事实

### 单股票

`000001` 已成功，约 13 秒量级，1340 OOS predictions。

因此： `build_stock_industry_relative_context_map()` 基本正常。

### pooled

主要问题集中在： `build_universe_industry_relative_context_maps()`

历史上出现： - 数十分钟无输出 - 内存约 10 GB - 用户中断 - 优化后 pooled
与 single 语义不一致 - BOM 导致"2.9 秒"假成功 - 缺 membership 股票
KeyError

因此绝对不能把"几秒"直接视为成功，必须检查 exit code 和输出。

## 8. 最新 pooled 优化

`e8a9d448`： 在 pooled 路径预计算历史 membership，减少热循环中重复：

``` python
scheduled(symbol, return_day)
```

`fe975cf9`： 修复 CI 中 `effective_from` 可能为 `datetime`：

``` python
effective_days = tuple(
    item.effective_from.date().isoformat()
    if hasattr(item.effective_from, "date")
    else item.effective_from[:10]
    for item in ordered
)
```

P13-M CI regression 已通过。

## 9. 第一阶段：10 股真实验收

先不要跑 76 股。

``` powershell
cd E:\git-ground-stock-quantimental

$symbols = Get-Content data\industryalidation_universe_76.txt |
    Select-Object -First 10

$pyArgs = @(
    "scriptsun_local_industry_relative_oos.py"
    "--universe-file"
    "data\industryalidation_universe_76.txt"
    "--membership"
    "data\industry\sw_official_sw1_membership_all.csv"
    "--root"
    "data"
)

foreach ($symbol in $symbols) {
    $pyArgs += "--symbol"
    $pyArgs += $symbol
}

Remove-Item data\industry\p13m_10stock_real_run.txt -ErrorAction SilentlyContinue

Measure-Command {
    python @pyArgs `
      2>&1 | Tee-Object -FilePath data\industry\p13m_10stock_real_run.txt
}
```

然后：

``` powershell
$LASTEXITCODE
Get-Content data\industry\p13m_10stock_real_run.txt -Tail 40
Get-Item data\industry\p13m_10stock_real_run.txt |
    Select-Object Length,LastWriteTime
```

10 股成功必须： - exit code 0 - 输出非空 - baseline / industry_5 /
industry_20 / industry_5_20 都出现 - pooled 统计存在 - 无 traceback /
KeyError - 记录耗时

## 10. 如果 10 股仍慢

不要让用户继续等待。

直接 profiling： `build_universe_industry_relative_context_maps()`

测量： 1. decision day 耗时 2. symbol 耗时 3. active_targets 4.
target_industry_codes 5. candidate return days 6. membership lookup 7.
peer price lookup 8. aggregation 9. memory

允许的优化： - 预计算 - 索引 - 字典 lookup - bisect - cache /
memoization - 按行业裁剪候选股票 - 按日期预聚合

但每次优化必须保持： `pooled(symbol) == independent single(symbol)`

同时保持： `pooled(run1) == pooled(run2)`

## 11. 第二阶段：76 股

只有 10 股通过才运行：

``` powershell
cd E:\git-ground-stock-quantimental

$symbols = Get-Content data\industryalidation_universe_76.txt

$pyArgs = @(
    "scriptsun_local_industry_relative_oos.py"
    "--universe-file"
    "data\industryalidation_universe_76.txt"
    "--membership"
    "data\industry\sw_official_sw1_membership_all.csv"
    "--root"
    "data"
)

foreach ($symbol in $symbols) {
    $pyArgs += "--symbol"
    $pyArgs += $symbol
}

Remove-Item data\industry\p13m_76stock_real_run.txt -ErrorAction SilentlyContinue

Measure-Command {
    python @pyArgs `
      2>&1 | Tee-Object -FilePath data\industry\p13m_76stock_real_run.txt
}
```

检查：

``` powershell
$LASTEXITCODE
Get-Item data\industry\p13m_76stock_real_run.txt |
    Select-Object Length,LastWriteTime
Get-Content data\industry\p13m_76stock_real_run.txt -Tail 60
```

76 股尚未完成真实验收，不能宣称完成。

## 12. P7 pytest

调查： - `RecommendationLedger` - `DecisionPacket` -
`tests/test_agent_ledger.py` - `tests/test_p7_integration.py` - 所有
`ledger.append(...)` 调用

统一真实 API，再完整 pytest。

## 13. 最终 CI

必须同时： - p13m success - pytest success - pooled regression success -
不因 pytest 前置失败而跳过 P13-M

GitHub Actions 可以逐 job/step 查看日志与执行时间，失败时应定位具体失败
step，而不是只看总红灯。

## 14. 最终验收文档

创建： `docs/P13M_ACCEPTANCE.md`

包含： - 数据来源与覆盖 - PIT 规则 - 1/4/10/76 stock 性能 - peak
memory（可测则记录） - pooled vs single - repeated pooled - 四种 factor
variant - Accuracy / Brier / Log Loss - CI commit/job/result -
limitations - next phase

## 15. Definition of Done

``` text
[ ] git synchronized
[ ] 10 stock real run passed
[ ] 76 stock real run passed
[ ] pooled == single
[ ] repeated pooled == identical
[ ] P7 pytest fixed
[ ] full pytest green
[ ] CI green
[ ] P13M_ACCEPTANCE.md committed
```

## 16. 当前结论

已完成： - 官方申万历史数据导入 - 76 股票验证集 - PIT-safe membership -
单股票 P13-M - pooled-vs-single regression - BOM 修复 - 缺 membership
股票修复 - pooled membership 预计算 - 日期类型兼容 - P13-M 独立 CI
regression

尚未完成： - 10 股真实 pooled 完整验收 - 76 股真实 pooled 完整验收 - P7
Ledger pytest 修复 - 全量 pytest 绿色 - P13-M 最终 acceptance report

核心下一目标：

> 先把 pooled 从"CI 逻辑正确但真实 76 股性能未知"推进到"10 股可复现、76
> 股可复现、CI 全绿、结果有验收记录"。

## 17. zcode 第一条任务

``` text
1. git pull --ff-only origin main
2. 确认 HEAD = fe975cf9
3. 阅读本交接文件
4. 阅读 industry_relative.py / runner / P13-M tests / Ledger / DecisionPacket tests
5. 不直接跑 76 股
6. 先 10 stock benchmark
7. 如果 10 stock 仍慢，立即 profiling
8. 修复后 CI
9. CI 通过后 76 stock
10. 最后修 P7 pytest
11. 输出 P13M_ACCEPTANCE.md
```
