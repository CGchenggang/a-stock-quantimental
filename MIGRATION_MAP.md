# Legacy → V2 Migration Map

## 原则

V1 不删除。

V2 不通过复制粘贴形成第二套互相独立的系统。

最终应该：

```text
V1 legacy
   ↓
compatibility adapters
   ↓
V2 canonical engine
```

---

## 映射表

| V1 功能 | V2 目标 | 处理 |
|---|---|---|
| auto_main.py | agent/orchestrator.py + cli.py | 逐步拆分 |
| scripts/行情 | data/providers.py + adapters | 迁移 |
| intraday_reversal_detector | data/intraday.py + factors/technical.py | 核验真实 intraday |
| fundflow | data/flow.py + factors/flow.py | 核验是否真正进入 decision |
| realtime index | data/realtime.py | 核验 freshness |
| 单指数市场判断 | regime/engine.py | 升级多指数 |
| 规则评分 | model/probability.py | 逐步替换 |
| 旧缓存 | data/quality.py + provider cache policy | 按数据类型重构 |
| 旧报告 | agent + skills | 结构化 |
| 旧推荐 | ledger.py | PIT + versioned |

---

## Codex 必须先回答的问题

### Q1

V1 的 intraday 数据究竟来自哪里？

### Q2

数据是否包含真实时间戳？

### Q3

fundflow 是事实数据还是平台定义的 proxy？

### Q4

realtime 是实时接口还是缓存？

### Q5

V1 是否存在 future leakage？

### Q6

V1 是否使用当前修订后的财务数据回测历史？

### Q7

V1 是否存在 survivorship bias？

### Q8

V1 的 score 是否重复计算高度相关因子？

---

## 迁移策略

### Stage A

V1 保持运行。

### Stage B

V2 提供 compatibility layer。

### Stage C

新研究流程优先使用 V2。

### Stage D

V1 仅作为 legacy fallback。

### Stage E

经过充分验证后再删除重复实现。

禁止一次性删除旧系统。
