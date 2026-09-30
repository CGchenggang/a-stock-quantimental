# ZCODE_EXECUTION_PLAN

## 主路线

P13-M-0 数据基线 → P13-M-1 单股票正确性 → P13-M-2 pooled 正确性 →
P13-M-3 pooled 性能 → P13-M-4 10 股票真实验收 → P13-M-5 76 股票真实验收
→ P13-M-6 P7 pytest 修复 → P13-M-7 全 CI 绿色 → P13-M-8 Acceptance
Report

## Gate 0：同步

``` powershell
cd E:\git-ground\a-stock-quantimental
git status
git pull --ff-only origin main
git log -5 --oneline
```

目标 HEAD： `fe975cf92c39f46fd040efd7aaed62c0e72a931e`

## Gate 1：CI 基线

run `36440420036`

-   p13m job `108989138914`：success
-   pytest job `108989138682`：failure（P7 Ledger API/test mismatch）

## Gate 2：10 股票

前 10 个 validation symbols。

必须记录： - exit code - wall time - output size - factor rows - OOS
predictions - pooled metrics - stderr / traceback

成功文件： `data/industry/p13m_10stock_real_run.txt`

## Gate 3：性能

如果 10 股票明显异常慢，停止扩大规模。

对 `build_universe_industry_relative_context_maps()` 做
instrumentation：

-   decision day
-   active targets
-   industry codes
-   candidate days
-   membership lookup
-   peer lookup
-   aggregation
-   memory

不要凭感觉优化。

## Gate 4：正确性

每次优化必须保持：

``` text
pooled(symbol) == single(symbol)
pooled(run1) == pooled(run2)
```

## Gate 5：76 股票

仅在 10 股票通过后执行。

成功： - exit 0 - non-empty output - all variants - pooled metrics - no
traceback - no KeyError - reproducible

## Gate 6：P7

统一 `RecommendationLedger.append()` 与 `DecisionPacket` 的真实 API。

不要只改测试让 CI 变绿。

## Gate 7：完整 CI

必须： - p13m success - pytest success - pooled regression success -
不因 pytest 前置失败跳过 P13-M

## Gate 8：验收文档

创建： `docs/P13M_ACCEPTANCE.md`

## Stop Conditions

以下任一发生就停止扩大规模： - output empty - non-zero exit -
traceback - memory runaway - 10 stock performance abnormal - pooled !=
single - CI regression failure

## Definition of Done

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
