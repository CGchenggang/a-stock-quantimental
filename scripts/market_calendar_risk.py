# -*- coding: utf-8 -*-
"""market_calendar_risk.py — 市场日历风险评估（重建版）
静态日历规则：股指期货交割日、期权交割日、长假前后、月末/季末资金面、重大会议窗口。
输出未来 N 天的风险日历与综合提示。
"""
from datetime import datetime, timedelta

RISK_EVENTS = []


def third_friday(year, month):
    """股指期货交割日：当月第三个周五"""
    d = datetime(year, month, 1)
    offset = (4 - d.weekday()) % 7  # 周五=4
    return d + timedelta(days=offset + 14)


def build_calendar(window_days=14, today=None):
    today = today or datetime.now().date()
    events = []
    for i in range(-1, 2):
        y, m = (today + timedelta(days=30 * i)).year, (today + timedelta(days=30 * i)).month
        try:
            tf = third_friday(y, m)
            days = (tf.date() - today).days if hasattr(tf, "date") else (tf - today).days
            if 0 <= days <= window_days:
                events.append({"date": str(tf.date()), "event": "股指期货/期权交割日", "risk": "中",
                               "in_days": days, "note": "交割周波动放大，尾盘异动常见"})
        except Exception:
            continue
    # 长假前：春节/国庆前最后交易日附近（近似：10-01 与 02-10±7 前两天）
    for month, day, name in [(10, 1, "国庆长假"), (2, 10, "春节长假"), (1, 1, "元旦")]:
        try:
            hd = datetime(today.year, month, day).date()
            if hd < today:
                hd = datetime(today.year + 1, month, day).date()
            days = (hd - today).days
            if 0 <= days <= window_days:
                events.append({"date": str(hd), "event": name + "前", "risk": "中",
                               "in_days": days, "note": "节前避险情绪+缩量，节后方向待确认"})
        except ValueError:
            continue
    # 月末资金面
    if today.day >= 26:
        events.append({"date": str(today), "event": "月末资金面偏紧窗口", "risk": "低",
                       "in_days": 0, "note": "逆回购利率易翘尾，注意杠杆资金"})
    return sorted(events, key=lambda e: e["in_days"])


def risk_summary(window_days=14, today=None):
    events = build_calendar(window_days, today)
    high = sum(1 for e in events if e["risk"] == "高")
    mid = sum(1 for e in events if e["risk"] == "中")
    level = "高" if high else ("中" if mid >= 2 else ("低" if not events else "中低"))
    return {"window_days": window_days, "level": level, "events": events}


if __name__ == "__main__":
    import json
    print(json.dumps(risk_summary(), ensure_ascii=False, indent=2))
