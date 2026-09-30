# ZCODE_HANDOFF_PROMPT

你现在接管 `CGchenggang/a-stock-quantimental` 的 P13-M 后续工程。

不要从头设计，也不要重复盲跑。

第一步：

``` powershell
cd E:\git-ground\a-stock-quantimental
git status
git pull --ff-only origin main
git log -5 --oneline
```

确认最新 HEAD： `fe975cf92c39f46fd040efd7aaed62c0e72a931e`

然后阅读交接文件。

你的职责： 1. 验证当前代码事实。 2. 不直接跑 76 股。 3. 先完成 10 股真实
pooled benchmark。 4. 如果 10 股仍慢，立即 profiling。 5. 修复 pooled
性能时保持 PIT 语义。 6. 每次优化通过 pooled-vs-single regression。 7.
GitHub CI 验证。 8. 10 股通过后再 76 股。 9. 修复 P7
RecommendationLedger / DecisionPacket API mismatch。 10. 最终让完整
pytest 与 P13-M CI 全绿。 11. 创建 `docs/P13M_ACCEPTANCE.md`。

当前事实： - 单股票 000001 已正常，约 13 秒量级。 - pooled
是主要未知瓶颈。 - 76 股票真实完整运行尚未成功验收。 -
曾出现几秒但实际上 KeyError/BOM 提前退出的假成功。 - `000017`
等股票可能没有官方 SW1 membership。 - 最新 P13-M CI regression
已通过。 - 完整 pytest 当前因 P7 Ledger API/test mismatch 失败。

绝对不要： - 把空输出当成功。 - 把 process exited 当成功。 - 把单股票当
76 股票。 - 把 p13m green 当 full CI green。 - 为了绿 CI 降低 regression
标准。 - 未测量就连续猜性能优化点。

最终必须报告： 最新 commit、10-stock benchmark、76-stock
benchmark、pooled vs single、CI、P7 pytest、remaining risks、next
phase。

目标是可复现、可审计、可继续开发的工程闭环。
