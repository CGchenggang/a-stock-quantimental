# -*- coding: utf-8 -*-
"""
global_liquidity_radar.py — 全球流动性雷达模块 (v0.87 重建版)
======================================================
监测全球流动性风险，核心关注日元套利交易(carry trade)风险。

监测维度:
  1. fx_carry_risk - 日元套利交易风险（核心）
  2. usd_stress - 美元流动性压力
  3. cross_asset_anomaly - 跨资产异常信号
  4. historical_pattern - 历史危机模式匹配（简化规则）

评级输出:
  🟢 GREEN (0) - 正常交易
  🟡 YELLOW (1) - 注意但不减仓
  🟠 ORANGE (2) - 成长股仓位-10%，止损收紧1%
  🔴 RED (3) - 总仓位-20%，禁止追高，9:30-10:00观察窗口

用法:
  python scripts/global_liquidity_radar.py
  python scripts/global_liquidity_radar.py --push  # 推送飞书（需 feishu_pusher）
"""
import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
SKILL_DB = os.path.join(SKILL_ROOT, "database")

sys.path.insert(0, SCRIPT_DIR)
try:
    from data_layer import get_us_treasury, get_usd_cny
except ImportError as e:
    print("[ERROR] data_layer 导入失败: %s" % e)
    sys.exit(1)

LEVELS = {0: "🟢 GREEN", 1: "🟡 YELLOW", 2: "🟠 ORANGE", 3: "🔴 RED"}
ACTIONS = {
    0: "正常交易",
    1: "注意但不减仓",
    2: "成长股仓位-10%，止损收紧1%",
    3: "总仓位-20%，禁止追高，9:30-10:00观察窗口",
}


def _pct_change_last(df, col="close"):
    try:
        a = float(df.iloc[-1][col])
        b = float(df.iloc[-2][col])
        return round((a / b - 1) * 100, 2)
    except Exception:
        return None


def fetch_sources():
    """14 项数据源尽力拉取，失败的记入 gaps"""
    data, gaps = {}, []
    ak = None
    try:
        import akshare as _ak
        ak = _ak
    except Exception as e:
        gaps.append("akshare不可用:%s" % str(e)[:40])

    # ① 汇率：USD/CNY 用 data_layer；USD/JPY、DXY 尽力
    try:
        usdcny = get_usd_cny() or {}
        data["USD_CNY"] = usdcny.get("rate") or usdcny.get("price")
    except Exception as e:
        gaps.append("USD_CNY:%s" % str(e)[:30])
    if ak is not None:
        for fn, sym, name in [(ak.forex_hist_em, "USDJPY", "USD_JPY"), (ak.index_global_hist_em, "美元指数", "DXY")]:
            try:
                df = fn(symbol=sym)
                chg = _pct_change_last(df, "收盘")
                if chg is not None:
                    data[name.replace("/", "_")] = chg
            except Exception as e:
                gaps.append("%s:%s" % (name, str(e)[:30]))

    # ② 利率
    try:
        tr = get_us_treasury() or {}
        data["US10Y"] = tr.get("y10") or tr.get("US10Y") or tr.get("us_10y")
        data["US30Y"] = tr.get("y30") or tr.get("US30Y") or tr.get("us_30y")
    except Exception as e:
        gaps.append("美债:%s" % str(e)[:30])

    # ③ 商品（COMEX黄金/WTI原油/COMEX铜，尽力）
    if ak is not None:
        for sym, name in [("COMEX黄金", "GOLD"), ("WTI原油", "WTI"), ("COMEX铜", "COPPER")]:
            try:
                df = ak.futures_foreign_hist(symbol=sym)
                chg = _pct_change_last(df, "收盘")
                if chg is not None:
                    data[name] = chg
            except Exception as e:
                gaps.append("%s:%s" % (name, str(e)[:30]))

    # ④ 股指/ETF（日经ETF 513520、韩国ETF、VXX 尽力 via 基金行情）
    if ak is not None:
        for code, name in [("513520", "日经ETF"), ("513180", "韩 国ETF"), ("159985", "VXX代理")]:
            try:
                df = ak.fund_etf_hist_em(symbol=code, period="daily", adjust="")
                chg = _pct_change_last(df, "收盘")
                if chg is not None:
                    data[name] = chg
            except Exception as e:
                gaps.append("%s:%s" % (name, str(e)[:30]))

    return data, gaps


def analyze(data, gaps):
    dims = {}

    # 1. fx_carry_risk：USD/JPY 大幅波动 + USD_CNY 贬值 = carry unwind 风险
    fx_score, fx_notes = 0, []
    usdjpy = data.get("USD_JPY")
    if usdjpy is not None and abs(usdjpy) > 1.5:
        fx_score += 2
        fx_notes.append("USD/JPY 单日 %+.2f%%，套利交易剧烈平仓风险" % usdjpy)
    elif usdjpy is not None and abs(usdjpy) > 0.8:
        fx_score += 1
        fx_notes.append("USD/JPY 单日 %+.2f%%，关注套利头寸" % usdjpy)
    usdcny_chg = data.get("USD_CNY")
    if isinstance(usdcny_chg, (int, float)) and usdcny_chg > 0.3:
        fx_score += 1
        fx_notes.append("人民币贬值压力 %+.2f%%" % usdcny_chg)
    dims["fx_carry_risk"] = {"score": min(fx_score, 3), "notes": fx_notes}

    # 2. usd_stress：美债收益率水平
    us_score, us_notes = 0, []
    y30 = data.get("US30Y")
    try:
        if y30 and float(y30) > 5.0:
            us_score += 2
            us_notes.append("US30Y=%s%% > 5%% 熔断线" % y30)
        elif y30 and float(y30) > 4.7:
            us_score += 1
            us_notes.append("US30Y=%s%% 逼近熔断线" % y30)
    except (TypeError, ValueError):
        pass
    dims["usd_stress"] = {"score": min(us_score, 3), "notes": us_notes}

    # 3. cross_asset_anomaly：黄金涨+股票跌 = 避险模式
    ca_score, ca_notes = 0, []
    gold = data.get("GOLD")
    nikkei = data.get("日经ETF")
    if gold is not None and gold > 1.0:
        ca_score += 1
        ca_notes.append("黄金 %+.2f%% 避险买入" % gold)
    if nikkei is not None and nikkei < -2:
        ca_score += 1
        ca_notes.append("日经ETF %+.2f%%，亚太风险偏好恶化" % nikkei)
    dims["cross_asset_anomaly"] = {"score": min(ca_score, 3), "notes": ca_notes}

    # 4. historical_pattern：简化规则匹配（2019.8 / 2024.8 carry unwind 形态）
    hp_score, hp_notes = 0, []
    if usdjpy is not None and usdjpy < -1.5 and (nikkei is not None and nikkei < -2):
        hp_score += 2
        hp_notes.append("形态匹配: 日元急升+日经急跌 (2024.8 carry unwind 模式)")
    dims["historical_pattern"] = {"score": min(hp_score, 3), "notes": hp_notes}

    total = sum(d["score"] for d in dims.values())
    radar = max(0, min(3, 1 if total >= 2 else 0, total // 2 + (1 if total >= 5 else 0)))
    if total >= 6:
        radar = 3
    elif total >= 4:
        radar = 2
    elif total >= 2:
        radar = 1
    else:
        radar = 0
    return dims, radar, gaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="推送飞书（需 feishu_pusher.py）")
    args = ap.parse_args()

    data, gaps = fetch_sources()
    dims, radar, gaps2 = analyze(data, gaps)
    gaps += gaps2

    rep = {
        "version": "0.87-rebuild",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "radar": radar,
        "level": LEVELS[radar],
        "action": ACTIONS[radar],
        "dimensions": dims,
        "sources": data,
        "gaps": gaps,
    }
    os.makedirs(SKILL_DB, exist_ok=True)
    out_path = os.path.join(SKILL_DB, "global_liquidity_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    print("%s %s" % (LEVELS[radar], ACTIONS[radar]))
    for k, d in dims.items():
        if d["notes"]:
            print("  [%s] %s" % (k, "; ".join(d["notes"])))
    if gaps:
        print("数据缺口: %d 项" % len(gaps))
    print("已写入 %s" % out_path)

    if args.push:
        try:
            from feishu_pusher import push_text
            push_text("全球流动性雷达 %s: %s" % (LEVELS[radar], ACTIONS[radar]))
        except Exception as e:
            print("[WARN] 飞书推送失败: %s" % str(e)[:80])


if __name__ == "__main__":
    main()
