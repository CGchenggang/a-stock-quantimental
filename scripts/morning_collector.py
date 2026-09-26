# -*- coding: utf-8 -*-
"""
morning_collector.py — 晨间哨兵数据采集器 (v2.1 重建版)

用途：在 08:30 采集全维度盘前数据，输出结构化 JSON 供 AI 解读
数据来源：
  ① data_layer.py: get_stock_hist(自带MA/LR/趋势分析) / get_realtime_quotes /
     get_sector_board / get_us_treasury / get_usd_cny / get_us_market
  ② sectors.json: 持仓池 + 角色与仓位
用法：
  python scripts/morning_collector.py
  python scripts/morning_collector.py --pool "F:\\...\\sectors.json"
输出：
  database/morning_data.json (覆盖写入) + 控制台摘要
"""
import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
SKILL_DB = os.path.join(SKILL_ROOT, "database")
DEFAULT_POOL = os.path.join(SKILL_DB, "sectors.json")

sys.path.insert(0, SCRIPT_DIR)
try:
    from data_layer import (
        get_stock_hist, get_realtime_quotes, get_sector_board,
        get_us_treasury, get_usd_cny, get_us_market,
    )
except ImportError as e:
    print("[ERROR] data_layer 导入失败: %s" % e)
    sys.exit(1)

ROLE_STOP = {"spear": -0.03, "shield": -0.05, "core": -0.08}


def load_pool(path):
    if not os.path.exists(path):
        return {"holdings": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_stock(code, meta):
    name = meta.get("name", code)
    role = meta.get("role", "core")
    out = {"ticker": code, "name": name, "role": role,
           "sector": meta.get("sector", ""),
           "position_lots": meta.get("position_lots"),
           "entry_price": meta.get("entry_price") or meta.get("entry")}
    try:
        hist = get_stock_hist(code, days=120)
        if not hist.get("ok"):
            out["error"] = str(hist.get("error") or "hist不可用")[:80]
            return out
        latest = hist.get("latest") or {}
        close = latest.get("close")
        out["close"] = close
        out["prev_close"] = hist.get("prev_close")
        out["date"] = hist.get("latest_date")
        for n in (5, 10, 20, 60):
            out["MA%d" % n] = hist.get("ma%d" % n)
        ma20 = hist.get("ma20")
        if close and ma20:
            out["ma20_dist_pct"] = round((close / ma20 - 1) * 100, 2)
        out["LR"] = hist.get("lr")
        out["recent_high20"] = hist.get("recent_high20")
        out["recent_low20"] = hist.get("recent_low20")
        out["trend_analysis"] = hist.get("trend_analysis")
        base = ROLE_STOP.get(role, -0.05)
        if close:
            out["stop_loss"] = round(close * (1 + base), 2)
            out["stop_rule"] = "%s %+.0f%%" % (role, base * 100)
        ta = hist.get("trend_analysis") or {}
        if isinstance(ta, dict) and ta.get("is_trend") is not None:
            checks = ta.get("reasons") or []
            passed = sum(1 for c in checks if "✓" in str(c))
            out["trend_health"] = "%d/%d" % (passed, max(len(checks), 1))
    except Exception as e:
        out["error"] = "hist异常:%s" % str(e)[:80]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default=DEFAULT_POOL)
    ap.add_argument("--date", default=None)
    args = ap.parse_args()

    pool = load_pool(args.pool)
    holdings = pool.get("holdings", [])
    cautions = []
    print("[%s] morning_collector 启动，持仓 %d 只" % (datetime.now(), len(holdings)))

    try:
        get_realtime_quotes()
    except Exception as e:
        cautions.append("实时行情预热失败: %s" % str(e)[:60])

    stocks = [collect_stock(h.get("ticker"), h) for h in holdings]

    sector_flow = []
    try:
        sb = get_sector_board() or {}
        rows = sb.get("sectors") or []
        rows = [r for r in rows if r]
        rows.sort(key=lambda r: -(r.get("pct") or 0))
        sector_flow = rows[:10] + rows[-10:]
    except Exception as e:
        cautions.append("板块资金失败: %s" % str(e)[:60])

    us_market, treasury, usdcny = {}, {}, {}
    try:
        us_market = get_us_market(["NVDA", "AMD", "TSLA"]) or {}
    except Exception as e:
        cautions.append("美股失败: %s" % str(e)[:60])
    try:
        treasury = get_us_treasury() or {}
    except Exception as e:
        cautions.append("美债失败: %s" % str(e)[:60])
    try:
        usdcny = get_usd_cny() or {}
    except Exception as e:
        cautions.append("汇率失败: %s" % str(e)[:60])

    ok_count = sum(1 for s in stocks if s.get("close"))
    completeness = round(ok_count / len(stocks), 2) if stocks else 0.0

    result = {
        "version": "2.1-rebuild",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": args.date or datetime.now().strftime("%Y-%m-%d"),
        "pool_source": args.pool,
        "data_quality": {"completeness": completeness, "cautions": cautions,
                         "note": "rebuild版：结构对齐提示词v0.86检查项"},
        "stocks": stocks,
        "sector_flow": sector_flow,
        "us_market": us_market,
        "us_treasury": treasury,
        "usd_cny": usdcny,
        "market_env": pool.get("market_env", ""),
    }
    os.makedirs(SKILL_DB, exist_ok=True)
    out_path = os.path.join(SKILL_DB, "morning_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("已写入 %s" % out_path)
    for s in stocks:
        if s.get("close"):
            print("  %s %s close=%s MA20=%s(%+.2f%%) LR=%s 止损=%s" % (
                s.get("ticker"), s.get("name"), s.get("close"), s.get("MA20"),
                s.get("ma20_dist_pct") or 0, s.get("LR"), s.get("stop_loss")))
        else:
            print("  %s %s 数据缺失: %s" % (s.get("ticker"), s.get("name"), s.get("error")))


if __name__ == "__main__":
    main()
