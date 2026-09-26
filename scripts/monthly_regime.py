# -*- coding: utf-8 -*-
"""monthly_regime.py — 月历偏置模块（重建版）
规则（来自 auto_main v3.0 说明）:
  月末自动收紧止损；事件密集期（数据由 monthly_events.json 配置）调整仓位上限。
"""
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS = os.path.join(SCRIPT_DIR, os.pardir, "database", "monthly_events.json")


def monthly_bias(today=None):
    today = today or datetime.now()
    bias = {"month_end_tighten": False, "event_dense": False, "stop_tighten_pct": 0.0,
            "position_cap_adj": 0}
    if today.day >= 25:
        bias["month_end_tighten"] = True
        bias["stop_tighten_pct"] = 1.0  # 止损收紧1个百分点
    if os.path.exists(EVENTS):
        import json
        try:
            ev = json.load(open(EVENTS, encoding="utf-8"))
            for e in ev.get(str(today.month), []):
                if abs(int(e.get("day", 0)) - today.day) <= 2:
                    bias["event_dense"] = True
                    bias["position_cap_adj"] = -10
        except Exception:
            pass
    return bias


if __name__ == "__main__":
    print(monthly_bias())
