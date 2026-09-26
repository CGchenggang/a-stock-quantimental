from dataclasses import dataclass

@dataclass
class RiskResult:
    flags: list[str]
    allowed: bool
    max_loss_proxy: float

class RiskEngine:
    def evaluate(self, data_quality, expected_volatility, expected_drawdown, liquidity_ok=True):
        flags=[]
        if data_quality < 0.75: flags.append("LOW_DATA_QUALITY")
        if expected_volatility > 0.06: flags.append("HIGH_VOLATILITY")
        if expected_drawdown < -0.12: flags.append("HIGH_DRAWDOWN_RISK")
        if not liquidity_ok: flags.append("LOW_LIQUIDITY")
        return RiskResult(flags, not any(x in flags for x in ["LOW_DATA_QUALITY","LOW_LIQUIDITY"]),
                          expected_drawdown)
