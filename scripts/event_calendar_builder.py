# -*- coding: utf-8 -*-
"""event_calendar_builder.py — 事件日历自动构建器 v0.2

改进:
  v0.2: 空数据保护 + 回溯已完成事件 + 直接读取 earnings_calendar.json
  v0.1: 初始版本

合并 earnings_calendar / unlock_calendar / AkShare 分红送转股东大会 数据，
产出 event_calendar.json（双文件策略：归档 + 最新快照）。

用法:
  python event_calendar_builder.py                     # 默认扫描 sectors + auto_target_pool 并集
  python event_calendar_builder.py --tickers 603986,300502   # 指定标的（测试用）
  python event_calendar_builder.py --force               # 强制覆盖（即使结果为空）
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime, timedelta

# ── 路径 ──────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, os.pardir, "database")
DB_DIR = os.path.normpath(DB_DIR)

SECTORS_PATH = os.path.join(DB_DIR, "sectors.json")
POOL_PATH = os.path.join(DB_DIR, "auto_target_pool.json")
EARNINGS_CAL_PATH = os.path.join(DB_DIR, "earnings_calendar.json")
CAL_OUT = os.path.join(DB_DIR, "event_calendar.json")

# 扫描窗口
SCAN_DAYS = 15       # 未来15天
LOOKBACK_DAYS = 14   # 回溯14天（捕获近期已完成的财报等）


# ── 工具函数 ──────────────────────────────────────────
def now_cn():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] 读取 {path} 失败: {e}")
        return None

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已写入 {path}")


# ── 标的池合并 ────────────────────────────────────────
def load_tickers(cli_tickers=None):
    """合并 sectors.holdings + auto_target_pool（排除已清仓），返回 [{ticker, name}]"""
    result = {}

    if cli_tickers:
        for t in cli_tickers:
            result[t] = t
        return [{"ticker": t, "name": result[t]} for t in result]

    sectors = load_json(SECTORS_PATH)
    if sectors and "holdings" in sectors:
        for h in sectors["holdings"]:
            tk = h.get("ticker")
            if tk:
                result[tk] = h.get("name", tk)

    pool = load_json(POOL_PATH)
    if isinstance(pool, list):
        for item in pool:
            if not isinstance(item, dict):
                continue
            if item.get("status") == "已清仓":
                continue
            tk = item.get("ticker")
            if tk and tk not in result:
                result[tk] = item.get("name", tk)

    return [{"ticker": tk, "name": nm} for tk, nm in result.items()]


# ── 数据源1: 财报日历（直接读 JSON + 函数调用）──────
def fetch_earnings(tickers):
    """
    直接从 earnings_calendar.json 读取，支持：
    - 未来 SCAN_DAYS 天内的 upcoming 事件
    - 过去 LOOKBACK_DAYS 天内的 completed 事件
    """
    events = []
    errors = []
    today = datetime.now().date()
    start_date = today - timedelta(days=LOOKBACK_DAYS)
    end_date = today + timedelta(days=SCAN_DAYS)

    cal = load_json(EARNINGS_CAL_PATH)
    if not cal or not isinstance(cal, list):
        errors.append(f"earnings_calendar.json 不存在或格式错误")
        return events, errors

    ticker_set = {t["ticker"] for t in tickers}
    name_map = {t["ticker"]: t["name"] for t in tickers}

    for e in cal:
        tk = e.get("ticker", "")
        if tk not in ticker_set:
            continue
        try:
            d = datetime.strptime(e["report_date"], "%Y-%m-%d").date()
        except Exception:
            continue

        # 财报用宽松窗口：过去60天 + 未来SCAN_DAYS天
        # （因为财报季后需要保留近期已披露的财报作为上下文）
        earnings_lookback = 60
        earnings_start = today - timedelta(days=earnings_lookback)
        earnings_end = today + timedelta(days=SCAN_DAYS + 30)  # 多给30天覆盖三季报

        if not (earnings_start <= d <= earnings_end):
            continue

        days = (d - today).days
        is_past = days < 0
        report_type = e.get("type", "财报")
        note = e.get("note", "")

        if is_past:
            detail = f"{report_type}已披露({abs(days)}天前)"
            if note:
                detail += f"。{note}"
            status = "completed"
        else:
            detail = f"{report_type}预计披露(距今{days}天)"
            if note:
                detail += f"。{note}"
            status = "upcoming"

        events.append({
            "ticker": tk,
            "name": name_map.get(tk, tk),
            "event_type": "earnings",
            "event_date": e["report_date"],
            "detail": detail,
            "status": status,
            "impact": "HIGH" if abs(days) <= 7 else "MEDIUM",
            "note": f"来源: earnings_calendar.json"
        })

    return events, errors


# ── 数据源2: 解禁日历 ────────────────────────────────
def fetch_unlocks(tickers):
    """调用 unlock_calendar.unlock_risk"""
    events = []
    errors = []
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from unlock_calendar import unlock_risk
    except Exception as e:
        errors.append(f"导入 unlock_calendar 失败: {e}")
        return events, errors

    for t in tickers:
        try:
            info = unlock_risk(t["ticker"], window_days=SCAN_DAYS)
            if info.get("has_unlock"):
                detail = info.get("detail", {})
                d_str = detail.get("date", "")
                pct = detail.get("pct_of_total", "")
                mv = detail.get("market_value_yi", "")
                desc = f"解禁风险:{info.get('risk_level','?')}"
                if pct:
                    desc += f" 占总股本{pct}"
                if mv:
                    desc += f" 市值{mv}亿"
                events.append({
                    "ticker": t["ticker"],
                    "name": t["name"],
                    "event_type": "unlock",
                    "event_date": d_str,
                    "detail": desc,
                    "status": "upcoming",
                    "impact": "HIGH" if info.get("risk_level") == "高" else "MEDIUM",
                    "note": "来源: unlock_calendar"
                })
        except Exception as e:
            errors.append(f"{t['ticker']} 解禁查询失败: {e}")

    return events, errors


# ── 数据源3: AkShare 分红/送转/股东大会 ──────────────
def fetch_akshare_events(tickers):
    """尝试通过 akshare 获取分红送转、股东大会数据"""
    events = []
    errors = []
    ak_ok = False

    try:
        import akshare as ak
    except ImportError:
        errors.append("akshare 未安装，跳过分红/送转/股东大会采集。请 pip install akshare")
        return events, errors, False

    today = datetime.now().date()
    end_date = today + timedelta(days=SCAN_DAYS)

    # --- 3a: 分红送转 ---
    for api_name in ("stock_dividend_cninfo", "stock_dividend"):
        fn = getattr(ak, api_name, None)
        if fn is None:
            continue
        try:
            df = fn()
            if df is None or df.empty:
                continue
            tk_col = None
            for c in df.columns:
                cs = str(c)
                if "代码" in cs or "ticker" in cs.lower():
                    tk_col = c
                    break
            if tk_col is None:
                continue

            for _, row in df.iterrows():
                try:
                    code = str(row[tk_col]).strip()
                    matched = None
                    for t in tickers:
                        if t["ticker"] in code or code in t["ticker"]:
                            matched = t
                            break
                    if not matched:
                        continue

                    date_col = None
                    for c in df.columns:
                        cs = str(c)
                        if ("日期" in cs or "时间" in cs or "date" in cs.lower()) and "除权" not in cs:
                            date_col = c
                            break
                    if date_col is None:
                        continue
                    d_str = str(row[date_col])[:10]
                    try:
                        d = datetime.strptime(d_str, "%Y-%m-%d").date()
                    except Exception:
                        continue
                    if not (today <= d <= end_date):
                        continue

                    desc_parts = []
                    for c in df.columns:
                        cs = str(c)
                        if any(kw in cs for kw in ("送", "转", "派", "分红", "股利")):
                            val = row[c]
                            if val and str(val).strip():
                                desc_parts.append(f"{cs}:{val}")
                    detail = "分红送转 " + "; ".join(desc_parts[:4]) if desc_parts else "分红送转"

                    events.append({
                        "ticker": matched["ticker"],
                        "name": matched["name"],
                        "event_type": "dividend",
                        "event_date": d_str,
                        "detail": detail,
                        "status": "upcoming",
                        "impact": "MEDIUM",
                        "note": f"来源: akshare.{api_name}"
                    })
                except Exception:
                    continue
            ak_ok = True
            break
        except Exception as e:
            errors.append(f"akshare.{api_name} 分红数据失败: {e}")
            continue

    # --- 3b: 股东大会 ---
    for api_name in ("stock_gddh", "stock_shareholder_communication_meeting"):
        fn = getattr(ak, api_name, None)
        if fn is None:
            continue
        try:
            df = fn()
            if df is None or df.empty:
                continue

            tk_col = None
            for c in df.columns:
                cs = str(c)
                if "代码" in cs or "ticker" in cs.lower():
                    tk_col = c
                    break
            if tk_col is None:
                continue

            for _, row in df.iterrows():
                try:
                    code = str(row[tk_col]).strip()
                    matched = None
                    for t in tickers:
                        if t["ticker"] in code or code in t["ticker"]:
                            matched = t
                            break
                    if not matched:
                        continue

                    date_col = None
                    for c in df.columns:
                        cs = str(c)
                        if "日期" in cs or "时间" in cs or "date" in cs.lower():
                            date_col = c
                            break
                    if date_col is None:
                        continue
                    d_str = str(row[date_col])[:10]
                    try:
                        d = datetime.strptime(d_str, "%Y-%m-%d").date()
                    except Exception:
                        continue
                    if not (today <= d <= end_date):
                        continue

                    detail_col = None
                    for c in df.columns:
                        cs = str(c)
                        if "会议" in cs or "名称" in cs or "议案" in cs:
                            detail_col = c
                            break
                    detail = str(row[detail_col])[:80] if detail_col else "股东大会"

                    events.append({
                        "ticker": matched["ticker"],
                        "name": matched["name"],
                        "event_type": "shareholder_meeting",
                        "event_date": d_str,
                        "detail": detail,
                        "status": "upcoming",
                        "impact": "MEDIUM",
                        "note": f"来源: akshare.{api_name}"
                    })
                except Exception:
                    continue
            ak_ok = True
            break
        except Exception as e:
            errors.append(f"akshare.{api_name} 股东大会数据失败: {e}")
            continue

    return events, errors, ak_ok


# ── 去重 ──────────────────────────────────────────────
def dedup(events):
    seen = set()
    out = []
    for e in events:
        key = (e.get("ticker"), e.get("event_type"), e.get("event_date"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


# ── 合并逻辑（保护手动数据）───────────────────────────
AUTO_SOURCE_MARKERS = ["来源: earnings_calendar", "来源: unlock_calendar", "来源: akshare"]

def is_auto_event(event):
    """判断事件是否来自自动采集（note字段含自动来源标记）"""
    note = event.get("note", "")
    return any(m in note for m in AUTO_SOURCE_MARKERS)

def merge_events(old_events, new_auto_events):
    """
    合并策略：
    - 旧文件中的手动事件（无自动来源标记）→ 保留
    - 旧文件中的自动事件 → 用新数据替换
    - 新自动事件 → 追加
    """
    # 保留手动事件
    manual_events = [e for e in old_events if not is_auto_event(e)]
    print(f"[MERGE] 保留 {len(manual_events)} 条手动事件")

    # 新自动事件去重
    new_deduped = dedup(new_auto_events)
    print(f"[MERGE] 新采集 {len(new_deduped)} 条自动事件")

    # 合并
    merged = manual_events + new_deduped
    merged = dedup(merged)  # 最终去重
    merged.sort(key=lambda x: x.get("event_date", ""))
    return merged


# ── 空数据保护 ─────────────────────────────────────────
def check_empty_protection(new_events, old_events, force=False):
    """如果合并后仍为空但旧文件有手动数据，拒绝覆盖"""
    if force:
        return True

    if len(new_events) > 0:
        return True  # 有自动数据，正常写入（会合并）

    # 新自动数据为空
    manual_count = len([e for e in old_events if not is_auto_event(e)]) if old_events else 0
    if manual_count > 0:
        print(f"[PROTECT] ⚠️  新自动采集0条，但有{manual_count}条手动事件。保留手动数据，跳过覆盖。")
        return False

    return True


# ── 主流程 ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="事件日历自动构建器")
    parser.add_argument("--tickers", type=str, default=None,
                        help="指定标的，逗号分隔（测试用）")
    parser.add_argument("--force", action="store_true",
                        help="强制覆盖（即使结果为空）")
    args = parser.parse_args()

    cli_tickers = args.tickers.split(",") if args.tickers else None
    tickers = load_tickers(cli_tickers)
    ticker_names = [t["ticker"] for t in tickers]
    print(f"[{now_cn()}] 开始构建事件日历...")
    print(f"标的池: {len(tickers)} 只 → {ticker_names}")

    # 读取旧数据（用于合并保护手动事件）
    old_data = load_json(CAL_OUT)
    old_events = old_data.get("events", []) if old_data else []
    old_manual = [e for e in old_events if not is_auto_event(e)]
    old_auto = [e for e in old_events if is_auto_event(e)]
    print(f"旧数据: {len(old_events)}条 (手动{len(old_manual)} + 自动{len(old_auto)})")

    all_events = []
    all_errors = []

    # 数据源1: 财报
    ev1, err1 = fetch_earnings(tickers)
    all_events.extend(ev1)
    all_errors.extend(err1)
    print(f"  财报: {len(ev1)} 条 (errors: {len(err1)})")

    # 数据源2: 解禁
    ev2, err2 = fetch_unlocks(tickers)
    all_events.extend(ev2)
    all_errors.extend(err2)
    print(f"  解禁: {len(ev2)} 条 (errors: {len(err2)})")

    # 数据源3: AkShare 分红/股东大会
    ev3, err3, ak_ok = fetch_akshare_events(tickers)
    all_events.extend(ev3)
    all_errors.extend(err3)
    print(f"  分红/股东大会: {len(ev3)} 条 (errors: {len(err3)})")

    # 去重（仅自动事件去重）
    all_events = dedup(all_events)

    # 合并：保留手动事件 + 替换自动事件
    if not args.force and old_manual:
        all_events = merge_events(old_events, all_events)
    else:
        all_events.sort(key=lambda x: x.get("event_date", ""))

    # 高影响事件摘要
    upcoming_high = []
    for e in all_events:
        if e.get("impact") == "HIGH" and e.get("status") == "upcoming":
            upcoming_high.append(f"{e['event_date']} {e.get('name','')} {e.get('detail','')[:50]}")

    # 构建输出
    today = today_str()
    end = (datetime.now() + timedelta(days=SCAN_DAYS)).strftime("%Y-%m-%d")

    source_desc = "自动采集: earnings_calendar + unlock_calendar"
    if ak_ok:
        source_desc += " + akshare"
    if old_manual and not args.force:
        source_desc += f" + 手动维护({len(old_manual)}条保留)"
    if not all_events:
        source_desc += "（全部失败，需AI手动 WebSearch 补充）"

    output = {
        "as_of": now_cn(),
        "scan_range": f"{today} ~ {end}",
        "last_verified": f"{today} 自动采集",
        "events": all_events,
        "upcoming_high_impact": upcoming_high,
        "source": source_desc
    }

    # 空数据保护（传入old_events用于合并判断）
    if not check_empty_protection(all_events, old_events, force=args.force):
        print(f"[DONE] 写入被保护机制阻止，保留旧数据")
        return

    # 写入（双文件策略）
    save_json(CAL_OUT, output)
    archive_path = os.path.join(DB_DIR, f"event_calendar_{today}.json")
    save_json(archive_path, output)

    if all_errors:
        print(f"\n[WARN] 共 {len(all_errors)} 个错误:")
        for err in all_errors:
            print(f"  - {err}")
        if not ak_ok:
            print("建议: AI 使用 WebSearch 手动补充缺失事件")

    print(f"\n[DONE] 共 {len(all_events)} 个事件, {len(upcoming_high)} 个高影响")


if __name__ == "__main__":
    main()
