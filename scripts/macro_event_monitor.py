# -*- coding: utf-8 -*-
"""
macro_event_monitor.py — 宏观事件监控模块 (v0.2 重建版)
==================================================
5层宏观事件采集与风险评级，输出 composite_shock (0-3)。

  Layer 1: Fed 议息/发言日历（内置日历表，可手工维护 fed_calendar.json）
  Layer 2: 利率预期代理（美债10Y/30Y、美元指数代理）
  Layer 3: 关键词风险捕捉（可配置关键词表，命中即计分）
  Layer 4: 亚太联动（日经/KOSPI/恒生盘认尽力拉取）
  Layer 5: 大行研报信号（人工维护 research_signals.json，可选）

评级：
  0 🟢 无宏观冲击
  1 🟡 注意（单一风险因子）
  2 🟠 警戒（多重因子或收益率逼近熔断线）
  3 🔴 冲击（加息预期+美债破5%等多因子共振）

输出：
  database/macro_cache/macro_report_latest.json
  --format markdown 时同时打印 Markdown 报告

用法：
  python scripts/macro_event_monitor.py
  python scripts/macro_event_monitor.py --format markdown
"""
import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
SKILL_DB = os.path.join(SKILL_ROOT, "database")
MACRO_CACHE = os.path.join(SKILL_DB, "macro_cache")

sys.path.insert(0, SCRIPT_DIR)
try:
    from data_layer import get_us_treasury, get_usd_cny
except ImportError as e:
    print("[ERROR] data_layer 导入失败: %s" % e)
    sys.exit(1)

# US30Y 熔断线：>5.0% 触发外部红色熔断（按 STRATEGY_DEPOSIT 规则）
US30Y_BREAKER = 5.0
# 关键词风险表：命中计 1 分，权重越大分越高
RISK_KEYWORDS = {
    "加息": 2, "鹰派": 2, "higher for longer": 2, "缩表": 1,
    "降息": -1, "鸽派": -1, "量化宽松": -1,
    "关税": 1, "地缘": 1, "制裁": 1, "违约": 2, "危机": 2,
}
# Fed 日历（示例条目，用户可维护 macro_cache/fed_calendar.json 覆盖）
DEFAULT_FED_CAL = [
    {"date": "2026-09-16", "event": "FOMC 议息决议"},
    {"date": "2026-10-28", "event": "FOMC 议息决议"},
    {"date": "2026-11-04", "event": "美国大选"},
]


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def fed_calendar_layer(today):
    cal = load_json(os.path.join(MACRO_CACHE, "fed_calendar.json"), DEFAULT_FED_CAL)
    upcoming = []
    for ev in cal:
        try:
            d = datetime.strptime(ev["date"], "%Y-%m-%d")
            days = (d - today).days
            if 0 <= days <= 14:
                upcoming.append({"date": ev["date"], "event": ev["event"], "in_days": days})
        except Exception:
            continue
    score = 0
    for u in upcoming:
        if "FOMC" in u["event"] or "议息" in u["event"]:
            score = max(score, 1 if u["in_days"] > 3 else 2)
        else:
            score = max(score, 1)
    return {"layer": "fed_calendar", "score": score, "events": upcoming}


def rate_expectation_layer():
    tr = get_us_treasury() or {}
    y10 = tr.get("y10") or tr.get("US10Y") or tr.get("us_10y")
    y30 = tr.get("y30") or tr.get("US30Y") or tr.get("us_30y")
    score, triggers = 0, []
    try:
        if y30 and float(y30) > US30Y_BREAKER:
            score += 2
            triggers.append("US30Y=%s%% > %s%% 熔断线" % (y30, US30Y_BREAKER))
        elif y30 and float(y30) > US30Y_BREAKER - 0.3:
            score += 1
            triggers.append("US30Y=%s%% 逼近熔断线" % y30)
        if y10 and float(y10) and float(y10) > 4.5:
            score += 1
            triggers.append("US10Y=%s%% 高位" % y10)
    except (TypeError, ValueError):
        triggers.append("收益率数据不可用")
    return {"layer": "rate_expectation", "score": min(score, 3), "triggers": triggers,
            "treasury": tr}


def keyword_layer():
    notes_path = os.path.join(MACRO_CACHE, "risk_notes.txt")
    score, hits = 0, []
    if os.path.exists(notes_path):
        text = open(notes_path, encoding="utf-8", errors="replace").read().lower()
        for kw, w in RISK_KEYWORDS.items():
            c = text.count(kw.lower())
            if c:
                hits.append({"keyword": kw, "count": c, "weight": w})
                score += w * min(c, 3)
    return {"layer": "keywords", "score": max(0, min(score, 3)), "hits": hits,
            "notes_file": notes_path}


def apac_layer():
    """亚太联动：尽力拉取，失败降级（数据缺失不计分）"""
    idx = {"日经225": "日经225", "韩国KOSPI": "韩国KOSPI", "恒生指数": "恒生指数"}
    status = {}
    score = 0
    try:
        import akshare as ak
        for cn, akkey in idx.items():
            try:
                df = ak.index_global_hist_em(symbol=akkey)
                if df is not None and len(df) >= 2:
                    # 防御式找收盘列：含"收盘"的列，否则退化为首个数值列
                    close_col = next((c for c in df.columns if "收盘" in str(c)),
                                     df.select_dtypes("number").columns[0] if len(df.select_dtypes("number").columns) else None)
                    a = float(df.iloc[-1][close_col])
                    b = float(df.iloc[-2][close_col])
                    chg = (a / b - 1) * 100
                    status[cn] = round(chg, 2)
                    if chg < -2:
                        score += 1
            except Exception as e:
                status[cn] = "不可用:%s" % str(e)[:30]
    except Exception as e:
        status["akshare"] = "不可用:%s" % str(e)[:40]
    return {"layer": "apac", "score": min(score, 2), "changes_pct": status}


def research_layer():
    sig = load_json(os.path.join(MACRO_CACHE, "research_signals.json"), {"signals": []})
    score = 0
    for s in sig.get("signals", []):
        score += s.get("weight", 0)
    return {"layer": "research", "score": max(0, min(score, 2)), "signals": sig.get("signals", [])}


LEVELS = {0: "🟢 GREEN", 1: "🟡 YELLOW", 2: "🟠 ORANGE", 3: "🔴 RED"}
ACTIONS = {
    0: "正常交易",
    1: "注意但不减仓",
    2: "成长股仓位-10%，止损收紧1%",
    3: "总仓位-20%，禁止追高，9:30-10:00观察窗口",
}


def to_markdown(rep):
    lines = ["## 宏观冲击审计 (%s)" % rep["generated_at"], ""]
    lines.append("**composite_shock = %d %s**  建议动作：%s" % (
        rep["composite_shock"], LEVELS[rep["composite_shock"]], rep["action"]))
    lines.append("")
    lines.append("| 层 | 得分 | 要点 |")
    lines.append("|---|---|---|")
    for l in rep["layers"]:
        gist = json.dumps({k: v for k, v in l.items() if k not in ("layer", "score")},
                          ensure_ascii=False)
        lines.append("| %s | %d | %s |" % (l["layer"], l["score"], gist[:120]))
    if rep.get("triggers"):
        lines.append("")
        lines.append("**触发因子**: " + "; ".join(rep["triggers"]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["json", "markdown"], default="json")
    args = ap.parse_args()

    today = datetime.now()
    os.makedirs(MACRO_CACHE, exist_ok=True)

    layers = [
        fed_calendar_layer(today.date()),
        rate_expectation_layer(),
        keyword_layer(),
        apac_layer(),
        research_layer(),
    ]
    total = sum(l["score"] for l in layers)
    composite = max(0, min(3, total // 2 + (1 if total >= 5 else 0)))
    triggers = []
    for l in layers:
        triggers += [t for t in (l.get("triggers") or [])][:3]

    rep = {
        "version": "0.2-rebuild",
        "generated_at": today.isoformat(timespec="seconds"),
        "composite_shock": composite,
        "level": LEVELS[composite],
        "action": ACTIONS[composite],
        "layers": layers,
        "triggers": triggers,
    }
    out_path = os.path.join(MACRO_CACHE, "macro_report_latest.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

    if args.format == "markdown":
        print(to_markdown(rep))
    else:
        print(json.dumps(rep, ensure_ascii=False, indent=2)[:2000])
    print("\n已写入 %s" % out_path)


if __name__ == "__main__":
    main()
