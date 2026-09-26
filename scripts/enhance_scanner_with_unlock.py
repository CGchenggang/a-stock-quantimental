#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强候选股报告 - 添加解禁风险信息（重建版）

v0.86 新增：在半月筛选生成的 scanner_report.json 基础上，
为每个候选股添加解禁风险信息（unlock_risk 字段）。

使用方式：
    python scripts/enhance_scanner_with_unlock.py
    或在 supply-chain-screener-a 生成 scanner_report.json 后自动调用
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unlock_calendar

SCRIPT_DIR = Path(__file__).resolve().parent
DATABASE_DIR = SCRIPT_DIR.parent / "database"


def enhance_scanner_report():
    """读取 scanner_report.json，为每个候选股添加解禁风险信息"""
    report_path = DATABASE_DIR / "scanner_report.json"
    if not report_path.exists():
        print("[WARN] %s 不存在，请先运行 supply-chain-screener-a 生成候选报告" % report_path)
        return None
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    # 兼容 list 或 {"candidates": [...]} 两种结构
    if isinstance(report, dict):
        items = report.get("candidates") or report.get("stocks") or []
    else:
        items = report

    enhanced = 0
    for item in items:
        ticker = item.get("ticker") or item.get("code")
        if not ticker:
            continue
        try:
            item["unlock_risk"] = unlock_calendar.unlock_risk(ticker)
            enhanced += 1
        except Exception as e:
            item["unlock_risk"] = {"has_unlock": None, "risk_level": "未知",
                                   "detail": "查询失败:%s" % str(e)[:50]}

    out = report_path  # 就地增强
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("[%s] 已为 %d/%d 个候选股增强解禁风险信息" % (datetime.now(), enhanced, len(items)))
    return report


if __name__ == "__main__":
    enhance_scanner_report()
