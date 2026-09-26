# -*- coding: utf-8 -*-
"""intraday_reversal_detector.py — 日内反转探测器（重建版, v3.86 规格）
8项评分体系(满分13分):
  ① 昨日极端情绪 ② 低开量缩 ③ 跌幅收窄 ④ 权重稳健 ⑤ ETF放量
  ⑥ 北向代理 ⑦ 底背离 ⑧ VWAP突破
HIGH/MEDIUM 反转信号 → 飞书推送；shock≥2 时反转阈值自动提高至10分。
数据缺失的项按0分处理并记录到 notes。
"""
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ITEMS = [
    ("extreme_sentiment_yesterday", 2),
    ("low_open_volume_shrink", 2),
    ("decline_narrowing", 2),
    ("weights_stable", 2),
    ("etf_volume_surge", 1),
    ("northbound_proxy", 1),
    ("bottom_divergence", 2),
    ("vwap_breakout", 1),
]


def detect(prev_state=None, intraday=None, shock=0, **kwargs):
    """输入昨日状态与盘中快照 dict，输出反转评分结果。
    prev_state/intraday 缺失项计0分（保守）。"""
    scores = {}
    total = 0
    notes = []
    features = {
        "extreme_sentiment_yesterday": (prev_state or {}).get("extreme_sentiment"),
        "low_open_volume_shrink": (intraday or {}).get("low_open_vol_shrink"),
        "decline_narrowing": (intraday or {}).get("decline_narrowing"),
        "weights_stable": (intraday or {}).get("weights_stable"),
        "etf_volume_surge": (intraday or {}).get("etf_vol_ratio"),
        "northbound_proxy": (intraday or {}).get("northbound_chg"),
        "bottom_divergence": (intraday or {}).get("bottom_divergence"),
        "vwap_breakout": (intraday or {}).get("vwap_break"),
    }
    for key, weight in ITEMS:
        v = features.get(key)
        got = bool(v) and v is not False
        scores[key] = weight if got else 0
        total += scores[key]
        if v is None:
            notes.append(key + ":数据缺失按0分")
    threshold = 10 if (shock or 0) >= 2 else 7
    if total >= threshold:
        level = "HIGH"
    elif total >= threshold - 2:
        level = "MEDIUM"
    else:
        level = "LOW"
    return {"total_score": total, "full_score": 13, "level": level,
            "threshold": threshold, "item_scores": scores, "notes": notes}


if __name__ == "__main__":
    print(detect(shock=1))
