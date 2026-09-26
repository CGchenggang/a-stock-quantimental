# Factor Specification

因子族：
1. trend
2. momentum
3. liquidity
4. flow_proxy
5. quality
6. valuation
7. earnings_revision
8. event
9. sentiment
10. macro

处理顺序：

winsorize -> normalize -> missing handling -> industry/size neutralization
-> correlation clustering -> model fitting -> out-of-sample validation

不要把 MA20、MA60、价格/MA20、60 日位置等高度相关变量当成完全独立证据。
权重由统计模型和 walk-forward 验证产生，不由 LLM 主观指定。
