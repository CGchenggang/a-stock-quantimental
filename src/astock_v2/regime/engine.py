from __future__ import annotations
import numpy as np

REGIMES=("TREND_UP","TREND_DOWN","RANGE","HIGH_VOL","RISK_OFF","UNKNOWN")

class RegimeEngine:
    """Multi-signal regime classifier; no single-index shortcut."""

    def classify(self, index_df, breadth=None, turnover_z: float=0.0,
                 sector_dispersion: float=0.0, liquidity_score: float=0.5):
        breadth=breadth or {}
        close=index_df["close"].astype(float)
        if len(close)<60:
            return "UNKNOWN"
        ma20=close.rolling(20).mean().iloc[-1]
        ma60=close.rolling(60).mean().iloc[-1]
        ret20=close.pct_change(20).iloc[-1]
        vol20=close.pct_change().rolling(20).std().iloc[-1]
        adv=float(breadth.get("advance_ratio",0.5))
        limit_stress=float(breadth.get("limit_down_ratio",0.0)-breadth.get("limit_up_ratio",0.0))
        if any(np.isnan(x) for x in (ma20,ma60,ret20,vol20)):
            return "UNKNOWN"
        if limit_stress>0.10 or (adv<0.35 and liquidity_score<0.35):
            return "RISK_OFF"
        if vol20>0.025 or abs(sector_dispersion)>0.08:
            return "HIGH_VOL"
        if close.iloc[-1]>ma20>ma60 and ret20>0 and adv>=0.50:
            return "TREND_UP"
        if close.iloc[-1]<ma20<ma60 and ret20<0 and adv<=0.50:
            return "TREND_DOWN"
        return "RANGE"
