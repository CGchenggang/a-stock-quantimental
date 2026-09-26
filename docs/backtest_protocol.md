# Backtest Protocol

必须防止：
- look-ahead bias
- survivorship bias
- revised-data leakage
- impossible fills
- suspension omission
- limit-up/down omission
- T+1 violation
- test-set tuning

必须使用 walk-forward：

train 2019-2022 -> test 2023
train 2020-2023 -> test 2024
train 2021-2024 -> test 2025
train 2022-2025 -> test 2026

指标：
hit rate、average/median return、profit factor、Sharpe、Sortino、
max drawdown、turnover、Brier score、calibration、regime breakdown。

每次 recommendation 保存 input snapshot、model version、feature version、
decision time、probability、expected return、risk、evidence、invalidation，
并自动追踪 T+1/T+3/T+5/T+10。
