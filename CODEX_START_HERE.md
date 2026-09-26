# A-Stock Quantimental 2.0 — Codex 开工说明

这是一个专门交给 Codex / Code Agent 执行的工程包。

## 你要把它交给 Codex 的内容

至少把整个目录作为工作区，并让 Codex 首先阅读：

1. `CODEX_START_HERE.md`
2. `CODEX_IMPLEMENTATION_PLAN.md`
3. `AGENT_RULES.md`
4. `MIGRATION_MAP.md`
5. `CODE_AGENT_TASK.md`
6. `docs/architecture.md`
7. `docs/factor_spec.md`
8. `docs/backtest_protocol.md`
9. `docs/agent-contract.md`
10. 当前 `src/astock_v2/` 全部代码
11. `tests/` 全部测试

如果你把本工程包放进现有 `CGchenggang/a-stock-quantimental` 仓库中，则还必须阅读旧版 `scripts/`、`auto_main.py`、`SKILL.md`、README 和所有旧测试。

---

## Codex 第一轮不要直接写代码

第一轮只做：

- 盘点现有项目；
- 盘点 V2 scaffold；
- 建立旧版 → V2 的迁移映射；
- 找出已有功能、缺失功能、假实现、mock、数据源风险；
- 检查测试；
- 给出 P0 实施计划；
- 不得宣称尚未实现的功能已经完成。

完成分析后，才开始 P0。

---

## 严格实施顺序

```text
P0 数据基础设施
 ↓
P1 数据源与适配器
 ↓
P2 因子系统
 ↓
P3 A股市场状态 Regime
 ↓
P4 概率/收益/风险模型
 ↓
P5 Walk-forward 回测
 ↓
P6 AI Research Agent
 ↓
P7 Recommendation Ledger
 ↓
P8 旧项目迁移
```

不得跳过阶段。

每个阶段必须：

1. 编码；
2. 单元测试；
3. 集成测试；
4. 更新文档；
5. 生成 `docs/progress/Px.md`；
6. 明确“已完成 / 未完成 / 风险 / 下一阶段”；
7. 通过本阶段验收后才能进入下一阶段。

---

## 最重要的原则

这个项目不是“让大模型猜股票”。

正确架构是：

```text
多源数据
  ↓
Point-in-Time 数据层
  ↓
数据质量
  ↓
因子
  ↓
因子去相关/标准化
  ↓
A股 Market Regime
  ↓
概率模型
  ↓
风险模型
  ↓
Walk-forward / OOS 验证
  ↓
Recommendation Ledger
  ↓
AI Research Agent
  ↓
研究报告 / 风险解释 / 证据整理
```

LLM 负责：

- 信息理解；
- 公告/新闻事件分类；
- 证据整理；
- 矛盾证据识别；
- 研究报告；
- 风险解释；
- 复盘总结。

LLM 不负责：

- 修改概率；
- 私自修改因子权重；
- 虚构实时行情；
- 生成不存在的数据；
- 把主观判断伪装成量化结果。

---

## 完成后的核心验收

至少通过：

```bash
pytest -q
python -m astock_v2.cli init
python -m astock_v2.cli demo 000001
python -m astock_v2.cli backtest --csv data/sample_ohlcv.csv
```

如果某项因为真实数据源、API key 或外部服务暂时无法执行，必须明确标记：

```text
NOT_IMPLEMENTED
BLOCKED_EXTERNAL_DEPENDENCY
SCAFFOLD_ONLY
```

不能用假数据把状态伪装成 `IMPLEMENTED`。

---

## 最终目标

最终系统应该能够把一个股票研究请求转化为结构化流程：

```text
用户：
“分析 000001”

Agent：
  ↓
data-health
  ↓
market-snapshot
  ↓
stock-research
  ↓
event-research
  ↓
quant model
  ↓
risk
  ↓
decision-review
  ↓
Recommendation Ledger
```

输出必须区分：

- 数据事实；
- 模型输出；
- AI 解释；
- 支持证据；
- 反向证据；
- 缺失信息；
- 风险；
- 失效条件。

不得把研究结果包装成确定性收益承诺。
