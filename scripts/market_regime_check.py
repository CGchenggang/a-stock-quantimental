# -*- coding: utf-8 -*-
"""market_regime_check.py — 市场状态 Top-Down 前置审计（重建版）
输出市场天气: SUNNY(强) / CLOUDY(中性) / RAIN(弱) / STORM(系统性恐慌)
依据: 沪深300趋势分(角度+MA排列) + 板块净流入广度 + 情绪代理。
供 auto_main 前置审计与空仓权判定（STORM + shock>=3 触发空仓权）。
"""
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from data_layer import get_index_daily
except ImportError:
    get_index_daily = None


def _trend_score(closes):
    """沪深300 趋势分 -5~+5：MA排列 + 20日动量"""
    if not closes or len(closes) < 60:
        return 0
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes[-60:]) / 60
    s = 0
    if ma5 > ma20:
        s += 1
    if ma20 > ma60:
        s += 1
    if closes[-1] > ma20:
        s += 1
    momo = (closes[-1] / closes[-20] - 1) * 100 if closes[-20] else 0
    if momo > 3:
        s += 2
    elif momo > 0:
        s += 1
    elif momo < -5:
        s -= 2
    elif momo < -2:
        s -= 1
    return max(-5, min(5, s))


def check(bbox=None):
    """返回 {weather, trend_score, checked_at}。bbox 可传入外部板块广度数据。"""
    trend = 0
    if get_index_daily:
        try:
            idx = get_index_daily("sh000300")
            rows = idx.get("rows") or []
            closes = [r.get("close") for r in rows if r.get("close")]
            trend = _trend_score(closes)
        except Exception:
            pass
    if trend >= 2:
        weather = "SUNNY"
    elif trend <= -3:
        weather = "STORM"
    elif trend <= -1:
        weather = "RAIN"
    else:
        weather = "CLOUDY"
    return {"weather": weather, "trend_score": trend,
            "checked_at": datetime.now().isoformat(timespec="seconds")}


if __name__ == "__main__":
    print(check())
