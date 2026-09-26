# Agent Contract

Agent 输入必须是结构化 ResearchPacket：

- market
- stock
- factors
- events
- model
- risk
- data_quality
- timestamp

Agent 输出：

```json
{
  "summary": "...",
  "evidence": [],
  "contradictions": [],
  "risk_flags": [],
  "decision_class": "WATCH|RESEARCH|PAPER_TEST|NO_ACTION",
  "confidence": 0.0,
  "invalidation": [],
  "missing_data": []
}
```

数据不足时降低决策等级；没有 OOS 验证时不能把模型概率描述为保证性胜率。
