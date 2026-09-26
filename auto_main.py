# -*- coding: utf-8 -*-
"""AutoHunter 影子系统 (auto_main.py) v3.86

v3.86 升级（日内反转探测器）：
1. 新增 intraday_reversal_detector 模块：8项评分体系(满分13分)
   ① 昨日极端情绪 ② 低开量缩 ③ 跌幅收窄 ④ 权重稳健 ⑤ ETF放量
   ⑥ 北向代理 ⑦ 底背离 ⑧ VWAP突破
2. 每轮巡航调用反转探测器，结果写入 quant_report.json → intraday_reversal_detector
3. HIGH/MEDIUM 反转信号 → 飞书推送
4. shock≥2 时反转阈值自动提高至10分

v3.85 升级（8项改进）：
1. LR分级：回踩建仓LR≥0.8 / 突破建仓LR≥1.2，写入SKILL.md
2. calc_key_levels增强：黄金分割(0.382/0.5/0.618)、MA60、布林带(±2σ)、60日高低、整数关口
3. calc_trade_prices新增：回踩/突破两套方案+R:R自动计算
4. 买入推荐卡(8维度)：价格位/日线量价/分时量价/板块联动/资金/宏观/时机/不追高
5. 价格自动校准：buy_price/sell_price变化>2%自动更新，stop_loss铁律只收紧不放松
6. 信号生命周期追踪：first_seen/cycles/last_change记录在last_state.json
7. data_layer增强：get_stock_hist返回closes60/highs60/lows60
8. auto_target_pool.json _meta拆分readonly/ai_editable字段

v3.84 升级（v0.84 四项盘中新规）：
1. composite_shock 盘中实时更新：每25分钟用A股盘面数据(指数涨跌/成交进度/跌停家数)
   修正外部shock，产出 intraday_shock（可升可降），解决7/9"KOSPI暴跌shock=3
   但A股创业板涨4.5%始终不更新"的结构性缺陷
2. 板块催化剂检测：同板块≥2只涨>5% + 均量比>1.2 + 无跌停 → 标记"板块启动"
3. MA20 边界预警：恢复比例=(现价-低点)/(MA20-低点)≥70%(强共振60%) + 重心上移
   + 板块启动 → 允许1手观察仓试探
4. 覆盖机制准则3：初始shock≥2 + 盘中shock降级 + 板块启动 → MA20下方允许建仓
   （止损铁律/不追涨停/仓位上限/情绪熔断不可覆盖）

v3.0 升级（第二批改造）：
1. 整合 stock_diagoser 的8维诊断，每轮巡航输出操作建议（持有/加仓/减仓/止损）
2. 状态变化才推送飞书，避免每30分钟刷屏（解决原版"预警刷屏"问题）
3. 叠加月历偏置：月末自动收紧止损，事件密集期调整仓位上限
4. 保留原版 MA20生命线/止损/买卖价预警逻辑作为兜底硬规则

双模式：
- 常驻巡航：python auto_main.py            （每25分钟循环，交易时段才工作）
- 单次诊断：python auto_main.py --once      （跑一次即退出，用于调试/定时任务）

状态持久化：database/last_state.json 记录每只标的上次操作建议，跳变才推送。
"""
import time
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# ---- UTF-8 防御（防御层3：脚本内显式修复 stdout 编码）----
# 根因：英文 Windows locale=cp1252，print 中文时 UnicodeEncodeError。
# sitecustomize.py 提供全局根治，这里作为脚本级兜底。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==========================================================
# 路径与导入
# ==========================================================
# auto_main.py 位于 skill 根目录，BASE_DIR 即 skill 根
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DATABASE_DIR = BASE_DIR / "database"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import feishu_pusher
import data_layer as dl
import stock_diagoser
import monthly_regime
import earnings_calendar
from md_renderer import render_diagnosis
import market_regime_check as mrc  # Top-Down 天气前置审计
import intraday_reversal_detector as reversal_det  # v3.86: 日内反转探测器

# ================== 主体（重建版 v3.86-body） ==================
POOL_PATH = BASE_DIR / "database" / "auto_target_pool.json"
STATE_PATH = BASE_DIR / "database" / "last_state.json"
CYCLE_PATH = BASE_DIR / "database" / "auto_main_cycle.json"
MACRO_PATH = BASE_DIR / "database" / "macro_cache" / "macro_report_latest.json"
CYCLE_MINUTES = 25
PUSH_COOLDOWN = 0  # 状态跳变才推，无额外冷却

MA20_IRON_RULE = "MA20下方+LR>1.2 → 减仓（兜底硬规则，不可被覆盖）"


def is_trading_hours(now=None):
    now = now or datetime.now()
    if now.weekday() >= 5:
        return False
    hm = now.hour * 60 + now.minute
    return (570 <= hm <= 690) or (780 <= hm <= 900)  # 9:30-11:30, 13:00-15:00


def load_pool():
    """返回 (meta, stocks)：_meta 与个股条目分离"""
    meta, stocks = {}, []
    if POOL_PATH.exists():
        data = json.load(open(POOL_PATH, encoding="utf-8"))
        for item in data:
            if isinstance(item, dict):
                if "_meta" in item:
                    meta = item["_meta"]
                else:
                    stocks.append(item)
    return meta, stocks


def load_state():
    if STATE_PATH.exists():
        try:
            return json.load(open(STATE_PATH, encoding="utf-8"))
        except Exception:
            pass
    return {"states": {}}


def save_state(state):
    json.dump(state, open(STATE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def external_shock():
    if MACRO_PATH.exists():
        try:
            rep = json.load(open(MACRO_PATH, encoding="utf-8"))
            return int(rep.get("composite_shock", 0))
        except Exception:
            pass
    return 0


def intraday_shock_adjust(external):
    """v3.84: 用A股盘面修正外部shock——指数涨跌可升可降"""
    adj = external
    basis = []
    try:
        idx = dl.get_index_realtime() or {}
        for k in ("hs300", "cyb"):
            pct = (idx.get(k) or {}).get("pct")
            if pct is not None:
                basis.append((k, pct))
        hs = next((p for k, p in basis if k == "hs300"), None)
        cyb = next((p for k, p in basis if k == "cyb"), None)
        if hs is not None and hs > 1.5 and cyb is not None and cyb > 1.5:
            adj = max(0, external - 1)
            basis.append(("调整", "大盘走强 shock降级"))
        elif hs is not None and hs < -1.5:
            adj = min(3, external + 1)
            basis.append(("调整", "大盘走弱 shock升级"))
    except Exception as e:
        basis.append(("error", str(e)[:40]))
    return max(0, min(3, adj)), basis


def sector_catalyst(results):
    """同板块>=2只涨>5% → 板块启动标记"""
    by_sector = {}
    for r in results:
        if (r.get("pct") or 0) > 5:
            by_sector.setdefault(r.get("sector") or "?", []).append(r.get("ticker"))
    return {s: ts for s, ts in by_sector.items() if len(ts) >= 2}


def ma20_iron_rule(r):
    """兜底硬规则：收盘在MA20下方且 LR>1.2 → 强制减仓"""
    close, ma20, lr = r.get("close"), r.get("ma20"), r.get("lr")
    if close and ma20 and lr and close < ma20 and lr > 1.2:
        r["advice"] = {"action": "⚠️ 减仓（MA20铁律）", "reason": MA20_IRON_RULE}
        r["ma20_iron_rule"] = True
    return r


def run_cycle(cycle_no, push=True, limit=None):
    meta, stocks = load_pool()
    if limit:
        stocks = stocks[:limit]
    regime = mrc.check()
    ext = external_shock()
    shock, shock_basis = intraday_shock_adjust(ext)

    results = []
    for entry in stocks:
        t = entry.get("ticker")
        try:
            r = stock_diagoser.diagnose(t, pool_meta=entry)
        except Exception as e:
            r = {"ticker": t, "name": entry.get("name"), "error": str(e)[:80]}
        r["ticker"] = t
        r["sector"] = entry.get("sector", "")
        r["role"] = entry.get("role", "")
        r = ma20_iron_rule(r)
        results.append(r)

    catalyst = sector_catalyst(results)
    rev = reversal_det.detect(shock=shock)

    # 状态跳变检测 + 推送
    state = load_state()
    states = state.setdefault("states", {})
    pushes = []
    now_ts = time.time()
    for r in results:
        t = r["ticker"]
        action = (r.get("advice") or {}).get("action") or r.get("action") or "?"
        prev = states.get(t)
        if prev is None or prev.get("action") != action:
            states[t] = {"action": action, "score": r.get("score"),
                         "price": r.get("price"), "ts": now_ts,
                         "signal_first_seen": (prev or {}).get("signal_first_seen", now_ts),
                         "signal_cycles": ((prev or {}).get("signal_cycles", 0)) + 1,
                         "signal_last_change": now_ts if prev else now_ts}
            if prev is not None and push:
                pushes.append("%s %s: %s → %s" % (t, r.get("name", ""), prev.get("action"), action))
        else:
            prev["ts"] = now_ts
            prev["signal_cycles"] = (prev or {}).get("signal_cycles", 0) + 1
    save_state(state)

    for p in pushes:
        print("[PUSH] " + p)
        if push:
            feishu_pusher.push_text("AI工作台·状态跳变\n" + p)
    if rev.get("level") in ("HIGH", "MEDIUM") and push:
        feishu_pusher.push_text("日内反转信号 %s: 得分 %s/%s" % (
            rev.get("level"), rev.get("total_score"), rev.get("full_score")))

    snapshot = {
        "cycle": cycle_no,
        "at": datetime.now().isoformat(timespec="seconds"),
        "external_shock": ext,
        "intraday_shock": shock,
        "shock_basis": shock_basis,
        "market_weather": regime.get("weather"),
        "trend_score": regime.get("trend_score"),
        "sector_catalyst": catalyst,
        "reversal": {"level": rev.get("level"), "score": rev.get("total_score")},
        "pushes": pushes,
        "stocks": [{"ticker": r.get("ticker"), "name": r.get("name"),
                    "close": r.get("price") or r.get("close"), "action": (r.get("advice") or {}).get("action"),
                    "score": r.get("score")} for r in results],
    }
    json.dump(snapshot, open(CYCLE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[cycle %d] shock=%d(ext %d) 天气=%s 反转=%s 推送=%d"
          % (cycle_no, shock, ext, regime.get("weather"), rev.get("level"), len(pushes)))
    return snapshot


def main():
    once = "--once" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    push = "--no-push" not in sys.argv
    cycle = 1
    while True:
        if is_trading_hours() or once:
            print("=== 巡航 cycle %d @ %s ===" % (cycle, datetime.now().isoformat(timespec="seconds")))
            try:
                run_cycle(cycle, push=push, limit=limit)
            except Exception as e:
                print("[ERROR] cycle异常: %s" % str(e)[:120])
        else:
            print("[%s] 非交易时段，等待" % datetime.now().strftime("%H:%M:%S"))
        if once:
            break
        time.sleep(CYCLE_MINUTES * 60)
        cycle += 1


if __name__ == "__main__":
    main()
