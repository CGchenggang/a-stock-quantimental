#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9:15 盘前自动报告流水线 (pre_market_pipeline.py) — 重建版

核心交付。每日 08:30 定时跑，09:00 前生成完整盘前预案并推送飞书。

6段合成：
① 隔夜美股(NVDA/AMD/TSLA)  ② 先行指标(美债/汇率)  ③ 昨日盘后(大盘/板块)
④ 今日事件(交易日历/财报检查)  ⑤ 持仓体检(调stock_diagoser)  ⑥ 综合结论

用法：
    python pre_market_pipeline.py            # 生成报告+保存
    python pre_market_pipeline.py --push     # 生成+推送飞书
    python pre_market_pipeline.py --push --no-save
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATABASE_DIR = SKILL_DIR / "database"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import feishu_pusher
import data_layer as dl
import stock_diagoser
import monthly_regime
import earnings_calendar
from md_renderer import render_diagnosis
import market_regime_check as mrc


def overnight_us():
    try:
        return dl.get_us_market(["NVDA", "AMD", "TSLA"]) or {}
    except Exception as e:
        return {"error": str(e)[:60]}


def leading_indicators():
    tr, fx = {}, {}
    try:
        tr = dl.get_us_treasury() or {}
    except Exception as e:
        tr = {"error": str(e)[:60]}
    try:
        fx = dl.get_usd_cny() or {}
    except Exception as e:
        fx = {"error": str(e)[:60]}
    return {"us_treasury": tr, "usd_cny": fx}


def yesterday_close():
    idx, sectors = {}, []
    try:
        idx = dl.get_index_realtime() or {}
    except Exception as e:
        idx = {"error": str(e)[:60]}
    try:
        sb = dl.get_sector_board() or {}
        rows = sb.get("sectors") or []
        rows = [r for r in rows if r]
        rows.sort(key=lambda r: -(r.get("net_yi") or 0))
        sectors = rows[:5] + rows[-5:]
    except Exception as e:
        sectors = [{"error": str(e)[:60]}]
    return {"index": idx, "sector_flow_top_bottom": sectors}


def today_events(holdings):
    today = datetime.now().date()
    events = {"trading_calendar": (dl.get_trade_calendar() or {}), "earnings": []}
    for h in holdings:
        t = h.get("ticker")
        ups = earnings_calendar.upcoming_earnings(t, window_days=14, today=today)
        for u in ups:
            events["earnings"].append({"ticker": t, "name": h.get("name"), **u})
    return events


def portfolio_checkup(holdings):
    results, gaps_all = [], []
    for h in holdings:
        t = h.get("ticker")
        try:
            r = stock_diagoser.diagnose(t, pool_meta=h)
        except Exception as e:
            r = {"ticker": t, "name": h.get("name"), "error": str(e)[:80]}
        results.append(r)
        gaps_all += [str(g) for g in (r.get("data_gaps") or [])]
    return results, gaps_all


def build_report():
    pool_path = DATABASE_DIR / "sectors.json"
    pool = {}
    if pool_path.exists():
        pool = json.load(open(pool_path, encoding="utf-8"))
    holdings = pool.get("holdings", [])

    rep = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "data_source": "data_layer + stock_diagoser + macro/liquidity 模块 (rebuild pipeline)",
        "portfolio": {"holdings": holdings},
        "overnight_us": overnight_us(),
        "leading_indicators": leading_indicators(),
        "yesterday_close": yesterday_close(),
        "events": today_events(holdings),
    }
    results, gaps = portfolio_checkup(holdings)
    rep["portfolio_checkup"] = [r for r in results]
    rep["data_quality"] = {"gaps": gaps[:10], "n_gaps": len(gaps)}
    rep["monthly_bias"] = monthly_regime.monthly_bias()

    # 宏观/流动性（若当日已由定时任务生成则复用）
    macro_path = DATABASE_DIR / "macro_cache" / "macro_report_latest.json"
    liq_path = DATABASE_DIR / "global_liquidity_report.json"
    rep["macro_shock_audit"] = json.load(open(macro_path, encoding="utf-8")) if macro_path.exists() else {"note": "未运行"}
    rep["global_liquidity"] = json.load(open(liq_path, encoding="utf-8")) if liq_path.exists() else {"note": "未运行"}

    # 综合结论（规则合成，AI 解读交给下游提示词）
    reg = mrc.check()
    shock = rep.get("macro_shock_audit", {}).get("composite_shock", 0)
    rep["risk_assessment"] = {
        "market_weather": reg.get("weather"),
        "trend_score": reg.get("trend_score"),
        "composite_shock": shock,
        "monthly_bias": rep["monthly_bias"],
        "verdict_rule": "STORM+shock>=3 => 空仓权；shock>=2 => 总仓位-20%并禁止追高",
    }
    rep["news_digest"] = {"note": "rebuild版：新闻摘要由下游提示词 AI 补充"}
    return rep


def to_markdown(rep):
    lines = ["# 盘前预案 %s" % rep["as_of"], ""]
    us = rep.get("overnight_us") or {}
    lines.append("## ① 隔夜美股")
    lines.append("```json\n%s\n```" % json.dumps(us, ensure_ascii=False)[:600])
    li = rep.get("leading_indicators") or {}
    lines.append("## ② 先行指标")
    lines.append("美债: %s | 汇率: %s" % (json.dumps(li.get("us_treasury"), ensure_ascii=False)[:200],
                                       json.dumps(li.get("usd_cny"), ensure_ascii=False)[:120]))
    yc = rep.get("yesterday_close") or {}
    lines.append("## ③ 昨日盘后")
    lines.append("指数: %s" % json.dumps(yc.get("index"), ensure_ascii=False)[:300])
    lines.append("## ④ 今日事件")
    lines.append(json.dumps(rep.get("events", {}).get("earnings", []), ensure_ascii=False)[:400])
    lines.append("## ⑤ 持仓体检")
    for r in rep.get("portfolio_checkup", []):
        lines.append(render_diagnosis(r))
    ra = rep.get("risk_assessment") or {}
    lines.append("## ⑥ 综合结论")
    lines.append("市场天气=%s 趋势分=%s composite_shock=%s 月历偏置=%s" % (
        ra.get("market_weather"), ra.get("trend_score"), ra.get("composite_shock"),
        json.dumps(ra.get("monthly_bias"), ensure_ascii=False)))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    rep = build_report()
    md = to_markdown(rep)

    if not args.no_save:
        date_tag = datetime.now().strftime("%Y-%m-%d")
        out = DATABASE_DIR / ("pre_market_%s.json" % date_tag)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        print("报告已存 %s" % out)

    if args.push:
        ok = feishu_pusher.send_md("盘前预案 %s" % rep["as_of"][:10], md)
        print("飞书推送:", ok)
    print(md[:1500])


if __name__ == "__main__":
    main()
