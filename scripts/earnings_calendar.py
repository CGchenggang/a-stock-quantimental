# -*- coding: utf-8 -*-
"""earnings_calendar.py — 财报日历检查（重建版）
数据源: database/earnings_calendar.json（用户/流水线维护），结构:
  [{"ticker": "603986", "report_date": "2026-10-28", "type": "三季报"}]
"""
import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.join(SCRIPT_DIR, os.pardir, "database", "earnings_calendar.json")


def upcoming_earnings(ticker, window_days=14, today=None):
    today = today or datetime.now().date()
    if not os.path.exists(CAL):
        return []
    try:
        cal = json.load(open(CAL, encoding="utf-8"))
    except Exception:
        return []
    out = []
    for e in cal:
        if e.get("ticker") != ticker:
            continue
        try:
            d = datetime.strptime(e["report_date"], "%Y-%m-%d").date()
        except Exception:
            continue
        days = (d - today).days
        if 0 <= days <= window_days:
            out.append({"date": e["report_date"], "type": e.get("type", ""), "in_days": days})
    return out


if __name__ == "__main__":
    print(upcoming_earnings("603986"))
