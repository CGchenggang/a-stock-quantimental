# -*- coding: utf-8 -*-
"""统一数据采集层 (data_layer.py)

所有 AkShare / yfinance 调用的唯一入口。设计原则：
1. 每个函数 try-except 包裹，失败返回带 error 字段的结构，永不抛异常中断主流程。
2. 实时类数据带本地缓存（TTL），避免高频拉取被封。
3. 被限流接口(_em 实时行情)自动降级到新浪接口。
4. v0.84 新增熔断器(Circuit Breaker)：连续失败3次自动隔离该源，15分钟后试探恢复，
   避免已知故障源反复超时浪费盘前流水线耗时。状态持久化到 cache/circuit_breaker.json。

可用接口（已验证 v1.18.64）：
- stock_zh_a_spot        新浪全市场实时行情(5527只,~40s) ★主实时源
- stock_zh_a_hist        个股日K(算MA) ★稳定
- stock_zh_index_daily   指数日K(沪深300/创业板) ★稳定
- stock_sector_spot      新浪行业板块涨跌排名 ★稳定
- stock_intraday_em      分时(不稳定,需重试) ★分时源
- stock_us_daily         美股日K(NVDA/AMD/TSLA) ★稳定
- bond_zh_us_rate        中美国债收益率 ★稳定
- currency_boc_sina      央行汇率 ★稳定
- tool_trade_date_hist_sina  交易日历 ★稳定

被限流接口（不可依赖）：所有 _em 后缀实时接口、资金流接口、个股信息接口
"""
from __future__ import annotations

import json
import os
import time
import warnings
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Optional

warnings.filterwarnings("ignore")

# ---- 路径 ----
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATABASE_DIR = SKILL_DIR / "database"
CACHE_DIR = DATABASE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 缓存机制
# =========================================================
def _cache_path(key: str) -> Path:
    safe = key.replace("/", "_").replace("\\", "_").replace(":", "_")
    return CACHE_DIR / f"{safe}.json"


def _cache_get(key: str, ttl_seconds: int = None, max_age: int = None) -> Optional[Any]:
    """读缓存。过期或不存在返回 None。兼容旧版 max_age 参数名。"""
    if ttl_seconds is None:
        ttl_seconds = max_age if max_age is not None else 3600
    p = _cache_path(key)
    if not p.exists():
        return None
    try:
        meta = json.loads(p.read_text(encoding="utf-8"))
        age = time.time() - meta.get("ts", 0)
        if age > ttl_seconds:
            return None
        return meta.get("data")
    except Exception:
        return None


def _cache_set(key: str, data: Any) -> None:
    p = _cache_path(key)
    try:
        p.write_text(
            json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


# =========================================================
# 熔断器（Circuit Breaker）
# =========================================================
# 模块级状态：追踪每个数据源的连续失败次数，连续失败达阈值后自动隔离，
# 到期后试探恢复。避免已知故障源反复超时浪费盘前流水线耗时。
CB_PATH = CACHE_DIR / "circuit_breaker.json"
CB_FAILURE_THRESHOLD = 3       # 连续失败次数触发熔断
CB_RECOVERY_TIMEOUT = 900      # 15分钟后试探恢复（秒）
_cb_state: dict = {}


def _cb_load():
    """从文件加载熔断器状态（进程重启后恢复）。"""
    global _cb_state
    if not _cb_state and CB_PATH.exists():
        try:
            _cb_state = json.loads(CB_PATH.read_text(encoding="utf-8"))
        except Exception:
            _cb_state = {}


def _cb_save():
    """持久化熔断器状态到文件。"""
    try:
        CB_PATH.write_text(
            json.dumps(_cb_state, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def _cb_is_open(source: str) -> bool:
    """检查数据源是否处于熔断状态。True=熔断中，应跳过该源。"""
    _cb_load()
    cb = _cb_state.get(source)
    if not cb or cb.get("failures", 0) < CB_FAILURE_THRESHOLD:
        return False
    elapsed = time.time() - cb.get("opened_at", 0)
    if elapsed > CB_RECOVERY_TIMEOUT:
        # 超时，允许一次试探
        return False
    return True


def _cb_record_success(source: str):
    """数据源调用成功：重置失败计数。"""
    _cb_load()
    if source in _cb_state and _cb_state[source].get("failures", 0) > 0:
        print(f"[CB] {source} 恢复，重置计数")
    _cb_state[source] = {"failures": 0, "opened_at": 0}
    _cb_save()


def _cb_record_failure(source: str):
    """数据源调用失败：计数+1，达阈值则开路熔断。"""
    _cb_load()
    cb = _cb_state.get(source, {"failures": 0, "opened_at": 0})
    cb["failures"] = cb.get("failures", 0) + 1
    if cb["failures"] >= CB_FAILURE_THRESHOLD and cb.get("opened_at", 0) == 0:
        cb["opened_at"] = time.time()
        print(f"[CB] {source} 熔断！连续失败{cb['failures']}次，{CB_RECOVERY_TIMEOUT//60}分钟后试探")
    _cb_state[source] = cb
    _cb_save()


def _safe_call(name: str, fn):
    """安全调用：捕获异常，返回 (ok, data, error)。"""
    try:
        return True, fn(), ""
    except Exception as e:
        return False, None, f"{type(e).__name__}: {str(e)[:120]}"


def _ak():
    """惰性导入 akshare，失败时给出明确错误。"""
    import akshare as ak
    return ak


# =========================================================
# 1. A股实时行情（新浪全市场，主实时源）
# =========================================================
_REALTIME_TTL = 300  # 5分钟缓存


def get_realtime_quotes(force_refresh: bool = False) -> dict:
    """新浪全市场实时行情。返回 {code: row_dict, ...}。

    shape ~5527只，约40秒。缓存5分钟。
    字段：代码/名称/最新价/涨跌幅/换手率/量比/成交额 等
    """
    if not force_refresh:
        cached = _cache_get("realtime_all", _REALTIME_TTL)
        if cached is not None:
            return cached

    ak = _ak()
    # 熔断检查：新浪全市场行情
    if _cb_is_open("sina_spot"):
        ok, df, err = False, None, "circuit_open: sina_spot"
    else:
        ok, df, err = _safe_call("stock_zh_a_spot", ak.stock_zh_a_spot)
        _cb_record_success("sina_spot") if ok else _cb_record_failure("sina_spot")
    if not ok or df is None or df.empty:
        # 降级：尝试东方财富(可能被限流)
        if _cb_is_open("stock_zh_a_spot_em"):
            ok2, df2, err2 = False, None, "circuit_open: stock_zh_a_spot_em"
        else:
            ok2, df2, err2 = _safe_call("stock_zh_a_spot_em", ak.stock_zh_a_spot_em)
            _cb_record_success("stock_zh_a_spot_em") if ok2 else _cb_record_failure("stock_zh_a_spot_em")
        if not ok2 or df2 is None or df2.empty:
            return {"ok": False, "error": f"sina:{err} | em:{err2}", "quotes": {}}
        df = df2

    quotes = {}
    for _, row in df.iterrows():
        raw_code = str(row.get("代码", "")).strip()
        if not raw_code:
            continue
        # 新浪返回带前缀(sz300502)，同时存纯数字键(300502)方便按数字代码查询
        digits = _clean_code(raw_code)
        entry = {
            "code": digits,
            "raw_code": raw_code,
            "name": str(row.get("名称", "")),
            "price": _f(row.get("最新价")),
            "pct": _f(row.get("涨跌幅")),
            "change": _f(row.get("涨跌额")),
            "prev_close": _f(row.get("昨收")),
            "open": _f(row.get("今开")),
            "high": _f(row.get("最高")),
            "low": _f(row.get("最低")),
            "volume": _f(row.get("成交量")),
            "amount": _f(row.get("成交额")),
            "turnover": _f(row.get("换手率")),
            "volume_ratio": _f(row.get("量比")),  # 量比
        }
        quotes[digits] = entry  # 主键用纯数字
        quotes[raw_code] = entry  # 兼容带前缀查询
    result = {"ok": True, "error": "", "count": len(quotes), "quotes": quotes, "ts": datetime.now().isoformat(timespec="seconds")}
    _cache_set("realtime_all", result)
    return result


def get_stock_realtime(code: str) -> dict:
    """单股实时行情。三级兜底：
    1) 新浪全市场缓存(秒级,盘中最准) → 2) 分时接口 → 3) 日K收盘价(盘后/兜底)

    特殊处理：新浪全市场在非交易时段(9:00前/15:30后)实时价返回0，
    此时自动用昨收价兜底并标注 source，避免下游显示0元误判。
    """
    code = _clean_code(code)
    # 1) 全市场缓存
    all_q = get_realtime_quotes()
    if all_q.get("ok") and code in all_q["quotes"]:
        q = dict(all_q["quotes"][code])
        q["ok"] = True
        # 检测实时价为0(非交易时段新浪返回0)，用昨收兜底
        if not q.get("price") or q.get("price") == 0:
            prev = q.get("prev_close")
            if prev and prev > 0:
                q["price"] = prev
                # 盘前/盘后兜底：用上一个交易日的实际涨跌幅（而非0.0）
                # 避免诊断时所有股票pct=0与指数比较后全部显示"显著弱于大盘"
                fallback_pct = 0.0
                try:
                    _hist = get_stock_hist(code, 5)
                    if _hist.get("ok") and _hist.get("latest", {}).get("pct") is not None:
                        fallback_pct = _hist["latest"]["pct"]
                except Exception:
                    pass
                q["pct"] = fallback_pct
                q["source"] = "prev_close_fallback"
                q["_note"] = f"非交易时段实时价为0，已用昨收{prev}兜底，pct取自上一交易日"
            else:
                q["source"] = "sina_spot_zero"
                q["_note"] = "非交易时段，实时价为0且无昨收，数据待开盘后更新"
        else:
            q["source"] = "sina_spot"
        return q

    # 2) 分时接口兜底
    intra = get_intraday(code)
    if intra.get("ok") and intra.get("ticks"):
        last = intra["ticks"][-1]
        if last.get("price") and last.get("price") > 0:
            return {
                "ok": True,
                "code": code,
                "price": last.get("price"),
                "vwap": intra.get("vwap"),
                "source": "intraday_fallback",
            }

    # 3) 日K收盘价兜底（最稳定，但仅反映上一交易日收盘）
    hist = get_stock_hist(code, 60)
    if hist.get("ok"):
        return {
            "ok": True,
            "code": code,
            "name": "",
            "price": hist["latest"]["close"],
            "pct": hist["latest"]["pct"],
            "source": "daily_close_fallback",
            "_note": "实时行情接口不可用，使用上一交易日收盘价",
        }
    return {"code": code, "ok": False, "error": "all realtime sources failed"}


# =========================================================
# 2. 个股日K + 均线 + 量能
# =========================================================
def get_stock_hist(code: str, days: int = 120) -> dict:
    """个股日K，并计算 MA5/10/20/60、量能比LR。

    主通道：新浪 stock_zh_a_daily（需 sz/sh 前缀，英文列名，稳定）。
    备用：东方财富 stock_zh_a_hist（中文列名，常被限流）。

    返回 {ok, code, latest_date, latest{}, ma5/ma10/ma20/ma60, vol_ma20, lr,
          recent_high20, recent_low20, closes_tail, kline_count, error}
    """
    code = _clean_code(code)
    cache_key = f"hist_{code}_{days}"
    cached = _cache_get(cache_key, 3600)  # 日K缓存1小时
    if cached is not None:
        return cached

    ak = _ak()
    # 加 sz/sh 前缀（新浪要求）：6开头沪市，其余深市
    sina_symbol = ("sh" if code.startswith("6") else "sz") + code

    df = None
    err = ""
    # 熔断检查：新浪日K
    sina_open = _cb_is_open("stock_zh_a_daily")
    # 主通道：新浪日K（英文列名 date/open/high/low/close/volume/amount）
    for attempt in range(3):
        if sina_open:
            err = "circuit_open: stock_zh_a_daily"
            break
        ok, d, err = _safe_call("stock_zh_a_daily", lambda: ak.stock_zh_a_daily(symbol=sina_symbol, adjust="qfq"))
        if ok and d is not None and not d.empty:
            _cb_record_success("stock_zh_a_daily")
            df = d
            break
        _cb_record_failure("stock_zh_a_daily")
        time.sleep(1.5)

    # 备用：东方财富（中文列名 日期/开盘/收盘...）——常被限流，仅兜底
    if df is None:
        if _cb_is_open("stock_zh_a_hist"):
            err2 = "circuit_open: stock_zh_a_hist"
        else:
            ok2, df2, err2 = _safe_call("stock_zh_a_hist", lambda: ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq"))
            _cb_record_success("stock_zh_a_hist") if (ok2 and df2 is not None and not df2.empty) else _cb_record_failure("stock_zh_a_hist")
            if ok2 and df2 is not None and not df2.empty:
                df = df2

    if df is None or df.empty:
        return {"ok": False, "error": f"sina:{err} | em:fallback_failed", "code": code}

    # 统一列名（兼容新浪英文 / 东方财富中文）
    colmap = {"date": "date", "日期": "date", "open": "open", "开盘": "open",
              "close": "close", "收盘": "close", "high": "high", "最高": "high",
              "low": "low", "最低": "low", "volume": "volume", "成交量": "volume",
              "amount": "amount", "成交额": "amount"}
    df = df.rename(columns={k: v for k, v in colmap.items() if k in df.columns})
    df = df.sort_values("date").reset_index(drop=True)

    # 【当日数据修正】检查最后一条日期是否是今天，如果不是则用实时行情覆盖
    today_str = datetime.now().strftime("%Y-%m-%d")
    last_date = str(df.iloc[-1]["date"])[:10]  # 取前10字符（YYYY-MM-DD）
    
    if last_date != today_str:
        # 日K数据不是今天，尝试从实时行情获取今日收盘数据
        realtime = get_realtime_quotes()
        if realtime.get("ok") and code in realtime["quotes"]:
            q = realtime["quotes"][code]
            if q.get("price") and q["price"] > 0:  # 有有效价格
                # 追加今日数据
                import pandas as pd
                today_row = pd.DataFrame([{
                    "date": today_str,
                    "open": q.get("open") or q["price"],
                    "high": q.get("high") or q["price"],
                    "low": q.get("low") or q["price"],
                    "close": q["price"],
                    "volume": q.get("volume") or 0,
                }])
                df = pd.concat([df, today_row], ignore_index=True)

    closes = df["close"].astype(float).tolist()
    highs = df["high"].astype(float).tolist()
    lows = df["low"].astype(float).tolist()
    vols = df["volume"].astype(float).tolist()

    def ma(arr, n):
        return round(sum(arr[-n:]) / n, 2) if len(arr) >= n else None

    vol_ma20 = sum(vols[-20:]) / 20 if len(vols) >= 20 else None
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None
    # 新浪无涨跌幅字段，自行计算
    pct = round((latest["close"] - prev["close"]) / prev["close"] * 100, 2) if prev is not None else None

    result = {
        "ok": True,
        "code": code,
        "latest_date": str(latest["date"]),
        "latest": {
            "open": _f(latest["open"]),
            "close": _f(latest["close"]),
            "high": _f(latest["high"]),
            "low": _f(latest["low"]),
            "pct": pct,
            "volume": int(latest["volume"]) if latest["volume"] == latest["volume"] else 0,
            "amount": _f(latest.get("amount")),
            "turnover": None,  # 新浪无换手率，留空
        },
        "prev_close": _f(prev["close"]) if prev is not None else None,
        "ma5": ma(closes, 5),
        "ma10": ma(closes, 10),
        "ma20": ma(closes, 20),
        "ma60": ma(closes, 60),
        "vol_ma20": vol_ma20,
        "lr": round(vols[-1] / vol_ma20, 2) if vol_ma20 and vol_ma20 > 0 else None,  # 量能火控
        "recent_high20": max(highs[-20:]) if len(highs) >= 20 else None,
        "recent_low20": min(lows[-20:]) if len(lows) >= 20 else None,
        "closes_tail": [round(c, 2) for c in closes[-5:]],  # 近5日收盘
        "closes60": [round(c, 2) for c in closes[-60:]],  # 近60日收盘（布林带/黄金分割）
        "highs60": [round(h, 2) for h in highs[-60:]],  # 近60日最高
        "lows60": [round(l, 2) for l in lows[-60:]],  # 近60日最低
        "kline_count": len(df),
        # 新增：趋势股判断（解决均线回归偏见）
        "trend_analysis": is_trend_stock(closes, highs, vols),
    }
    _cache_set(cache_key, result)
    return result


# =========================================================
# 3. 分时数据 + VWAP(分时均线/黄线)
# =========================================================
def get_intraday(code: str) -> dict:
    """个股分时数据。计算今日 VWAP(分时均线/黄线)。

    stock_intraday_em 不稳定，重试2次。
    v0.93 新增：盘中缓存4小时，盘后可复用当天最后有效数据。
    """
    code = _clean_code(code)
    cache_key = f"intraday_{code}"

    # 盘中缓存策略：交易时段缓存4小时，盘后缓存到次日开盘
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    is_trading_hours = (9, 30) <= (hour, minute) <= (15, 0) and now.weekday() < 5

    # 尝试读缓存
    cached = _cache_get(cache_key, max_age=14400 if is_trading_hours else 86400)  # 盘中4h，盘后24h
    if cached is not None:
        return cached

    ak = _ak()
    df = None
    err = ""
    intraday_open = _cb_is_open("stock_intraday_em")
    for attempt in range(2):
        if intraday_open:
            err = "circuit_open: stock_intraday_em"
            break
        ok, d, err = _safe_call("stock_intraday_em", lambda: ak.stock_intraday_em(symbol=code))
        if ok and d is not None and not d.empty:
            _cb_record_success("stock_intraday_em")
            df = d
            break
        _cb_record_failure("stock_intraday_em")
        time.sleep(1)
    if df is None or df.empty:
        return {"ok": False, "error": err, "code": code}

    # 列名：时间/成交价/手数/买卖盘性质
    prices = df["成交价"].astype(float).tolist()
    hands = df["手数"].astype(float).tolist()
    total_hand = sum(hands) if hands else 0
    vwap = sum(p * h for p, h in zip(prices, hands)) / total_hand if total_hand else None

    # 解析买卖盘性质（"买入"/"卖出"/"中性"）
    buy_vol, sell_vol, neutral_vol = 0, 0, 0
    bs_col = "买卖盘性质" if "买卖盘性质" in df.columns else None
    bs_values = df[bs_col].astype(str).tolist() if bs_col else [""] * len(df)

    ticks = []
    for i, (t, p, h) in enumerate(zip(df["时间"], prices, hands)):
        bs_raw = bs_values[i].strip() if i < len(bs_values) else ""
        h_int = int(h)
        # 归类买卖方向
        if "买" in bs_raw:
            buy_vol += h_int
            bs = "B"
        elif "卖" in bs_raw:
            sell_vol += h_int
            bs = "S"
        else:
            neutral_vol += h_int
            bs = "N"
        ticks.append({"time": str(t), "price": _f(p), "hands": h_int, "bs": bs})

    result = {
        "ok": True,
        "code": code,
        "vwap": round(vwap, 2) if vwap else None,
        "last_price": prices[-1] if prices else None,
        "last_time": str(df["时间"].iloc[-1]) if len(df) else None,
        "ticks_count": len(ticks),
        "ticks": ticks[-30:],  # 只保留末30条避免过大
        # v0.85 新增：买卖盘统计（用于筹码收集/派发分析）
        "buy_vol": buy_vol,
        "sell_vol": sell_vol,
        "neutral_vol": neutral_vol,
        "has_bs_data": bs_col is not None,
    }

    # v0.93: 缓存分时数据，盘后可复用
    _cache_set(cache_key, result)

    return result


# =========================================================
# 3.5 分时K线（新浪5分钟/1分钟K线）
# =========================================================
def get_minute_kline(code: str, scale: int = 5, datalen: int = 20) -> dict:
    """新浪分时K线数据（5分钟/1分钟）。

    Args:
        code: 股票代码（6位数字）
        scale: K线周期，5=5分钟，1=1分钟，15=15分钟，30=30分钟，60=60分钟
        datalen: 获取条数（最后N条）

    Returns:
        {ok, code, scale, klines: [{time, open, high, low, close, volume}, ...]}

    数据源：新浪财经API，稳定可靠。
    """
    code = _clean_code(code)
    cache_key = f"min_kline_{code}_{scale}_{datalen}"
    cached = _cache_get(cache_key, 60)  # 缓存1分钟
    if cached is not None:
        return cached

    # 构造新浪API URL
    prefix = "sh" if code.startswith("6") else "sz"
    symbol = f"{prefix}{code}"
    url = (
        f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        f"CN_MarketData.getKLineData?symbol={symbol}&scale={scale}&ma=no&datalen={datalen}"
    )

    try:
        import requests
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://finance.sina.com.cn/"
        })
        if resp.status_code != 200:
            return {"ok": False, "error": f"HTTP {resp.status_code}", "code": code}

        # 新浪返回的是JS格式，需要解析
        text = resp.text.strip()
        if not text or text == "null":
            return {"ok": False, "error": "Empty response", "code": code}

        # 解析JSON
        import json as json_mod
        data = json_mod.loads(text)
        if not data:
            return {"ok": False, "error": "No data", "code": code}

        # 转换格式
        klines = []
        for row in data:
            klines.append({
                "time": row.get("day", ""),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("volume", 0)),
            })

        result = {
            "ok": True,
            "code": code,
            "scale": scale,
            "klines": klines,
            "count": len(klines),
        }
        _cache_set(cache_key, result)
        return result

    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:100]}", "code": code}


# =========================================================
# 4. 大盘指数
# =========================================================
def get_index_daily(symbol: str = "sh000300") -> dict:
    """指数日K，并提供历史收益率/波动率观测供V2 regime使用."""
    cache_key = f"idx_{symbol}"
    cached = _cache_get(cache_key, 3600)
    if cached is not None:
        return cached

    ak = _ak()
    if _cb_is_open("stock_zh_index_daily"):
        return {"ok": False, "error": "circuit_open: stock_zh_index_daily", "symbol": symbol}
    ok, df, err = _safe_call("stock_zh_index_daily", lambda: ak.stock_zh_index_daily(symbol=symbol))
    _cb_record_success("stock_zh_index_daily") if ok else _cb_record_failure("stock_zh_index_daily")
    if not ok or df is None or df.empty:
        return {"ok": False, "error": err, "symbol": symbol}

    df = df.sort_values("date").reset_index(drop=True)
    closes = df["close"].astype(float).tolist()
    ma20 = round(sum(closes[-20:]) / 20, 2) if len(closes) >= 20 else None
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None
    pct = round((latest["close"] - prev["close"]) / prev["close"] * 100, 2) if prev is not None else None

    returns = [
        (closes[k] / closes[k - 1] - 1.0) * 100
        for k in range(1, len(closes))
        if closes[k - 1] > 0
    ]

    def _stdev(values):
        if len(values) < 2:
            return None
        mean = sum(values) / len(values)
        return (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

    vol20 = _stdev(returns[-20:]) if len(returns) >= 20 else None
    rolling_vols = [
        _stdev(returns[k - 20:k])
        for k in range(20, len(returns) + 1)
    ]
    rolling_vols = [v for v in rolling_vols if v is not None]
    vol_z = None
    if vol20 is not None and len(rolling_vols) >= 10:
        baseline = rolling_vols[:-1]
        baseline_std = _stdev(baseline)
        if baseline and baseline_std and baseline_std > 0:
            vol_z = round((vol20 - sum(baseline) / len(baseline)) / baseline_std, 4)

    result = {
        "ok": True,
        "symbol": symbol,
        "latest_date": str(latest["date"]),
        "latest_close": _f(latest["close"]),
        "pct": pct,
        "ma20": ma20,
        "above_ma20": bool(latest["close"] > ma20) if ma20 else None,
        "volatility20": round(vol20, 6) if vol20 is not None else None,
        "volatility_z": vol_z,
        "return_count": len(returns),
    }
    _cache_set(cache_key, result)
    return result


def get_market_turnover_snapshot() -> dict:
    """Aggregate A-share turnover from the full-market quote snapshot.

    The z-score is only produced after enough dated local observations have
    accumulated. It is explicitly a runtime observation series, not a
    backtest-ready historical feed.
    """
    current = get_realtime_quotes()
    if not current.get("ok"):
        return {"ok": False, "error": current.get("error", "realtime unavailable")}

    quotes = current.get("quotes", {})
    amount = sum(
        float(row.get("amount") or 0)
        for key, row in quotes.items()
        if str(key).isdigit() and isinstance(row, dict)
    )
    date_key = datetime.now().strftime("%Y-%m-%d")
    history_key = "market_turnover_history"
    history = _cache_get(history_key, 90 * 86400) or []
    by_date = {str(row.get("date")): float(row.get("amount") or 0) for row in history}
    by_date[date_key] = amount
    history = [
        {"date": d, "amount": by_date[d]}
        for d in sorted(by_date)[-60:]
    ]
    _cache_set(history_key, history)

    values = [float(row["amount"]) for row in history if float(row["amount"]) > 0]
    z = None
    if len(values) >= 20:
        baseline = values[:-1]
        mean = sum(baseline) / len(baseline)
        sd = _stdev_numeric(baseline)
        if sd and sd > 0:
            z = round((amount - mean) / sd, 4)

    return {
        "ok": True,
        "date": date_key,
        "amount": amount,
        "turnover_z": z,
        "observation_count": len(values),
        "source": current.get("source", "legacy_realtime"),
        "pit_ready": False,
        "warning": "local observation history; not backtest-ready until a dated historical source is migrated",
    }


def _stdev_numeric(values):
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

def get_index_realtime() -> dict:
    """主要指数实时涨跌（从全市场行情缓存提取，或用指数日K兜底）。

    由于指数实时接口被封，这里用日K最新收盘 + 全市场行情里的大盘字段推算。
    """
    # 沪深300/创业板/上证 日K
    hs300 = get_index_daily("sh000300")
    cyb = get_index_daily("sz399006")
    sh = get_index_daily("sh000001")
    return {
        "hs300": hs300,
        "cyb": cyb,
        "sh": sh,
    }


# =========================================================
# 5. 行业板块（新浪）
# =========================================================
def get_sector_board() -> dict:
    """新浪行业板块涨跌排名。返回 {ok, sectors[{name,pct,amount,...}], error}。

    用于：(a)个股相对强弱 vs 所属板块 (b)板块联动判断
    """
    cached = _cache_get("sector_board", 300)
    if cached is not None:
        return cached

    ak = _ak()
    if _cb_is_open("stock_sector_spot"):
        return {"ok": False, "error": "circuit_open: stock_sector_spot", "sectors": []}
    ok, df, err = _safe_call("stock_sector_spot", lambda: ak.stock_sector_spot(indicator="新浪行业"))
    _cb_record_success("stock_sector_spot") if ok else _cb_record_failure("stock_sector_spot")
    if not ok or df is None or df.empty:
        return {"ok": False, "error": err, "sectors": []}

    sectors = []
    for _, row in df.iterrows():
        sectors.append({
            "name": str(row.get("板块", "")),
            "pct": _f(row.get("涨跌幅")),
            "amount": _f(row.get("总成交额")),
            "count": _f(row.get("公司家数")),
            "top_stock_pct": _f(row.get("个股-涨跌幅")),
        })
    sectors.sort(key=lambda x: x["pct"] if x["pct"] is not None else -999, reverse=True)
    result = {"ok": True, "sectors": sectors, "ts": datetime.now().isoformat(timespec="seconds")}
    _cache_set("sector_board", result)
    return result


def find_sector_of(code: str, pool_meta: dict | None = None) -> str | None:
    """查找个股所属板块。优先用持仓池里手工标注的 sector，否则无法自动获取(接口被封)。"""
    if pool_meta and pool_meta.get("sector"):
        return pool_meta["sector"]
    return None


# 新浪行业板块别名映射：把配置里的常用 sector 名 → 新浪板块表里的实际名
# 新浪板块表是固定49个，名称较粗（如"电子器件"），需要把细分行业归并
# 新浪49个板块完整列表：玻璃行业/化纤行业/电子器件/次新股/化工行业/陶瓷行业/发电设备/
# 家具行业/塑料制品/飞机制造/船舶制造/机械行业/电子信息/仪器仪表/家电行业/有色金属/
# 公路桥梁/交通运输/电力行业/其它行业/供水供气/建筑建材/水泥行业/摩托车/电器行业/
# 金融行业/开发区/房地产/汽车制造/商业百货/纺织行业/食品行业/煤炭行业/钢铁行业/
# 服装鞋类/生物制药/酿酒行业/环保行业/物资外贸/医疗器械/印刷包装/综合行业/传媒娱乐/
# 农药化肥/农林牧渔/石油行业/造纸行业/酒店旅游/纺织机械
SECTOR_ALIASES = {
    # rebuild: 持仓池 compound 板块 -> 新浪板块表映射
    "半导体/设备": "电子器件",
    "半导体/封测": "电子器件",
    "电子/面板": "电子器件",
    "面板": "电子器件",
    "新材料/玻纤": "玻璃行业",
    "玻纤": "玻璃行业",
    "新材料": "化工行业",

    # ===== 电子/半导体相关 → 电子器件 =====
    "通信设备": "电子器件", "光模块": "电子器件", "CPO": "电子器件", "算力": "电子器件",
    "半导体": "电子器件", "芯片": "电子器件", "集成电路": "电子器件", "PCB": "电子器件",
    "印制电路板": "电子器件", "电子器件": "电子器件", "消费电子": "电子器件", "存储": "电子器件",

    # ===== 软件/数字相关 → 电子信息 =====
    "软件": "电子信息", "信创": "电子信息", "计算机": "电子信息", "人工智能": "电子信息",
    "AI": "电子信息", "数据要素": "电子信息", "数字经济": "电子信息", "云计算": "电子信息",
    "电子信息": "电子信息", "大数据": "电子信息", "网络安全": "电子信息",

    # ===== 医药相关 → 生物制药/医疗器械 =====
    "创新药": "生物制药", "CXO": "生物制药", "医药": "生物制药", "生物制药": "生物制药",
    "医疗器械": "医疗器械", "医疗": "医疗器械", "基因": "生物制药",

    # ===== 机械/机器人/低空经济 → 机械行业/飞机制造 =====
    "机械": "机械行业", "机器人": "机械行业", "减速器": "机械行业", "工程机械": "机械行业",
    "机械行业": "机械行业", "机床": "机械行业",
    # 低空经济/eVTOL → 飞机制造（新浪有专门板块）
    "低空经济": "飞机制造", "eVTOL": "飞机制造", "无人机": "飞机制造", "飞行汽车": "飞机制造",
    "航空": "飞机制造", "飞机制造": "飞机制造",

    # ===== 船舶/交通 → 船舶制造/交通运输/公路桥梁 =====
    "船舶": "船舶制造", "造船": "船舶制造", "航运": "交通运输", "物流": "交通运输",
    "交通运输": "交通运输", "高速公路": "公路桥梁", "公路桥梁": "公路桥梁",

    # ===== 汽车/新能源车 → 汽车制造/电器行业 =====
    "汽车": "汽车制造", "新能源车": "汽车制造", "汽车零部件": "汽车制造", "整车": "汽车制造",
    "汽车制造": "汽车制造",
    # 锂电池/光伏/风电/储能 → 电器行业（发电设备更准确）
    "锂电池": "电器行业", "光伏": "发电设备", "风电": "发电设备", "储能": "电器行业",
    "电器行业": "电器行业", "电机": "电器行业",

    # ===== 食品/白酒/消费 → 酿酒/食品/家电/百货 =====
    "白酒": "酿酒行业", "食品饮料": "食品行业", "酿酒": "酿酒行业", "食品": "食品行业",
    "酿酒行业": "酿酒行业", "食品行业": "食品行业",
    "家电": "家电行业", "家电行业": "家电行业", "白色家电": "家电行业",
    "旅游": "酒店旅游", "酒店": "酒店旅游", "免税": "酒店旅游", "酒店旅游": "酒店旅游",
    "百货": "商业百货", "零售": "商业百货", "商业百货": "商业百货",
    "服装": "服装鞋类", "纺织": "纺织行业", "服装鞋类": "服装鞋类",

    # ===== 金融 → 金融行业（新浪统称，含银行/保险/券商）=====
    "银行": "金融行业", "券商": "金融行业", "保险": "金融行业", "金融": "金融行业",
    "金融行业": "金融行业", "信托": "金融行业",

    # ===== 房地产/建筑 =====
    "房地产": "房地产", "地产": "房地产", "房企": "房地产",
    "建筑": "建筑建材", "建材": "建筑建材", "建筑建材": "建筑建材",
    "水泥": "水泥行业", "水泥行业": "水泥行业",
    "环保": "环保行业", "环保行业": "环保行业",

    # ===== 周期资源品 → 煤炭/有色/钢铁/化工/石油 =====
    "煤炭": "煤炭行业", "煤炭行业": "煤炭行业",
    "有色": "有色金属", "有色金属": "有色金属", "铜": "有色金属", "铝": "有色金属", "锂": "有色金属",
    "钢铁": "钢铁行业", "钢铁行业": "钢铁行业",
    "化工": "化工行业", "化学": "化工行业", "化工行业": "化工行业", "化纤": "化纤行业",
    "石油": "石油行业", "石油行业": "石油行业", "油气": "石油行业",

    # ===== 农业 → 农林牧渔/农药化肥 =====
    "农业": "农林牧渔", "种业": "农药化肥", "养殖": "农林牧渔", "农林牧渔": "农林牧渔",
    "农药化肥": "农药化肥", "化肥": "农药化肥",

    # ===== 电力/公用事业 → 电力行业/供水供气 =====
    "电力": "电力行业", "电力行业": "电力行业", "火电": "电力行业", "水电": "电力行业",
    "核电": "电力行业", "绿电": "电力行业",
    "供水供气": "供水供气", "燃气": "供水供气", "水务": "供水供气",

    # ===== 传媒/教育 =====
    "传媒": "传媒娱乐", "影视": "传媒娱乐", "游戏": "传媒娱乐", "教育": "传媒娱乐",
    "传媒娱乐": "传媒娱乐",

    # ===== 其他 =====
    "摩托车": "摩托车", "家具": "家具行业", "玻璃": "玻璃行业", "陶瓷": "陶瓷行业",
    "塑料": "塑料制品", "印刷": "印刷包装", "造纸": "造纸行业",
}


def match_sector_in_board(config_sector: str, board_sectors: list[dict]) -> dict | None:
    """把配置的 sector 名匹配到新浪板块表里的实际板块。

    匹配优先级：1)别名精确映射 2)名称包含 3)返回None
    返回匹配到的板块 dict（含 name/pct/rank），未匹配返回 None。
    """
    if not config_sector or not board_sectors:
        return None

    # 1) 别名映射
    mapped = SECTOR_ALIASES.get(config_sector, config_sector)

    names = [s.get("name", "") for s in board_sectors]

    # 2) 精确匹配映射后的名字
    for s in board_sectors:
        if s.get("name") == mapped:
            return s

    # 3) 模糊包含匹配（任一方向）
    for s in board_sectors:
        n = s.get("name", "")
        if n and (mapped in n or n in mapped):
            return s

    # 4) 关键词分词匹配（把config_sector拆词去板块名里找）
    for kw in [config_sector[:2], config_sector[-2:]]:
        for s in board_sectors:
            n = s.get("name", "")
            if n and kw in n:
                return s

    return None


# =========================================================
# 6. 美股 + 美债 + 汇率（AkShare 主通道，yfinance 仅可选增强）
# =========================================================
def _expected_us_trading_date() -> date:
    """计算当前北京时间下，最近一个已收盘的美股交易日。

    核心逻辑：将北京时间转为美东时间，判断美股当天是否已收盘(16:00 EDT)。
    已收盘 → 预期日期 = 当天(美东)；未收盘 → 预期日期 = 前一交易日。
    跳过周末，不处理美国节假日(节假日数据仍会由 fallback 兜底)。
    """
    beijing_now = datetime.now()
    # 北京时间 UTC+8 → 美东 UTC-4 (EDT, 3月第二个周日~11月第一个周日)
    utc_now = beijing_now - timedelta(hours=8)
    # 简化处理：4~11月用EDT(UTC-4)，其余用EST(UTC-5)
    us_east_offset = 4 if 3 <= beijing_now.month <= 10 else 5
    us_east_now = utc_now + timedelta(hours=12 - us_east_offset)

    us_date = us_east_now.date()
    us_hour = us_east_now.hour

    if us_hour >= 16:
        # 美股已收盘，最新完整交易日是今天(美东)
        expected = us_date
    else:
        # 美股尚未收盘(或还没开盘)，最新完整交易日是前一交易日
        expected = us_date - timedelta(days=1)

    # 跳过周末
    while expected.weekday() >= 5:  # 5=Sat, 6=Sun
        expected -= timedelta(days=1)

    return expected


def _fetch_us_stock_tencent(symbol: str) -> Optional[dict]:
    """腾讯财经 fallback：获取美股最新行情+前收盘价，计算涨跌幅。

    使用 web.ifzq.gtimg.cn/appstock/app/fqkline 接口(与美债 fallback 同源)。
    qt 字段格式: [name, code, current_price, prev_close, open, volume, ..., date]
    返回 {close, pct, date} 或 None(失败时)。
    """
    import requests as _req
    url = (
        f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param=us{symbol},day,,,3,"
    )
    try:
        resp = _req.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        if resp.status_code != 200:
            return None
        data = resp.json()
        inner = data.get("data", {}).get(f"us{symbol}", {})

        # 优先从 qt 字段提取：qt 包含精确的 current_price 和 prev_close
        qt = inner.get("qt", {})
        qt_data = qt.get(f"us{symbol}", [])
        if qt_data and len(qt_data) >= 5:
            # qt 格式: ['real', 'name', 'ticker', current_price, prev_close, open, ...]
            try:
                current = float(qt_data[3])
                prev_close = float(qt_data[4])
                if current > 0 and prev_close > 0:
                    pct = round((current - prev_close) / prev_close * 100, 2)
                    # 从 day 字段获取日期
                    day_data = inner.get("day") or inner.get("qfqday") or []
                    date_str = day_data[-1][0] if day_data else str(date.today())
                    return {"close": current, "pct": pct, "date": date_str}
            except (ValueError, IndexError):
                pass

        # qt 不可用时，从 day 字段计算(需要足够多的连续交易日数据)
        days = inner.get("qfqday") or inner.get("day") or []
        if len(days) >= 2:
            # 确保最后两条是连续交易日(排除腾讯返回"首日+末日"的情况)
            try:
                d1 = datetime.strptime(days[-1][0], "%Y-%m-%d").date()
                d2 = datetime.strptime(days[-2][0], "%Y-%m-%d").date()
                if (d1 - d2).days <= 4:  # 连续交易日(含周末)
                    latest = days[-1]
                    prev = days[-2]
                    close = float(latest[2])
                    prev_close = float(prev[2])
                    pct = round((close - prev_close) / prev_close * 100, 2) if prev_close else None
                    return {"close": close, "pct": pct, "date": latest[0]}
            except (ValueError, IndexError):
                pass

        return None
    except Exception:
        return None


def get_us_market(symbols: list[str] | None = None) -> dict:
    """隔夜美股日K。默认拉 NVDA/AMD/TSLA。

    v0.86 修复：
    1. 日期校验：检查 AkShare 返回数据的日期是否为最近已收盘的美股交易日
    2. 自动 Fallback：数据过期(>2天偏差)时自动切换腾讯财经 API
    3. 新鲜度标注：返回结果增加 is_stale 字段，供下游判断数据可靠性
    4. 预期日期计算：基于北京时间→美东时间转换，判断美股是否已收盘

    返回 {symbol: {close, pct, date, is_stale, source?}, ...}
    """
    if symbols is None:
        symbols = ["NVDA", "AMD", "TSLA"]

    expected_date = _expected_us_trading_date()
    out = {}
    ak = _ak()

    for sym in symbols:
        cache_key = f"us_{sym}"
        cached = _cache_get(cache_key, 3600)
        if cached is not None:
            out[sym] = cached
            continue

        if _cb_is_open("stock_us_daily"):
            # AkShare 熔断时直接用腾讯 fallback
            tx = _fetch_us_stock_tencent(sym)
            if tx:
                tx["is_stale"] = False
                tx["source"] = "tencent_fallback"
                out[sym] = tx
                _cache_set(cache_key, tx)
            else:
                out[sym] = {"ok": False, "error": "circuit_open: stock_us_daily + tencent_failed"}
            continue

        ok, df, err = _safe_call(
            "stock_us_daily",
            lambda s=sym: ak.stock_us_daily(symbol=s, adjust="qfq")
        )
        _cb_record_success("stock_us_daily") if ok else _cb_record_failure("stock_us_daily")

        if ok and df is not None and not df.empty:
            df = df.sort_values("date")
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else None

            # === v0.86 新增：数据新鲜度校验 ===
            try:
                data_date = pd.Timestamp(str(latest["date"])).date() if hasattr(pd, 'Timestamp') else \
                    datetime.strptime(str(latest["date"])[:10], "%Y-%m-%d").date()
            except Exception:
                try:
                    data_date = datetime.strptime(str(latest["date"])[:10], "%Y-%m-%d").date()
                except Exception:
                    data_date = expected_date  # 无法解析则假设新鲜

            # 预期日期 = 最近已收盘的美股交易日(见 _expected_us_trading_date)。
            # days_stale=0 → 数据日期 = 预期日期，完全新鲜
            # days_stale=1 → 数据是前一交易日的，属于 T+1 延迟(今天最常见的场景)
            # days_stale≥2 → 明显过期，AkShare 后端可能故障
            # 策略：days_stale ≥ 1 即触发 fallback，因为我们的 _expected_us_trading_date
            # 已经将"未收盘"的情况回退到了前一交易日，所以 days_stale=1 意味着数据确实落后了。
            days_stale = (expected_date - data_date).days
            is_stale = days_stale >= 1

            if is_stale:
                print(f"[STALE] {sym}: 数据日期={data_date}, 预期={expected_date}, "
                      f"偏差{days_stale}天 → 尝试腾讯财经 fallback")
                tx = _fetch_us_stock_tencent(sym)
                if tx:
                    print(f"[FRESH] {sym}: 腾讯 fallback 成功 → {tx['date']}")
                    tx["is_stale"] = False
                    tx["source"] = "tencent_fallback"
                    out[sym] = tx
                    _cache_set(cache_key, tx)
                    continue
                else:
                    print(f"[WARN] {sym}: 腾讯 fallback 也失败，返回 stale 数据")
                    # Fallback 失败：返回 stale 数据但明确标注
                    pct = round(
                        (latest["close"] - prev["close"]) / prev["close"] * 100, 2
                    ) if prev is not None else None
                    rec = {
                        "close": _f(latest["close"]),
                        "pct": pct,
                        "date": str(latest["date"]),
                        "is_stale": True,
                        "stale_days": days_stale,
                        "expected_date": str(expected_date),
                        "warning": f"AkShare数据过期{days_stale}天且腾讯fallback失败，请WebSearch验证",
                        "source": "akshare_stale",
                    }
                    out[sym] = rec
                    _cache_set(cache_key, rec)  # 缓存但缩短有效时间(已在cache中)
                    continue

            # === 数据新鲜，正常返回 ===
            pct = round(
                (latest["close"] - prev["close"]) / prev["close"] * 100, 2
            ) if prev is not None else None
            rec = {
                "close": _f(latest["close"]),
                "pct": pct,
                "date": str(latest["date"]),
                "is_stale": False,
            }
            out[sym] = rec
            _cache_set(cache_key, rec)
        else:
            # AkShare 调用失败：尝试腾讯 fallback
            tx = _fetch_us_stock_tencent(sym)
            if tx:
                print(f"[FALLBACK] {sym}: AkShare失败，腾讯fallback成功")
                tx["is_stale"] = False
                tx["source"] = "tencent_fallback"
                out[sym] = tx
                _cache_set(cache_key, tx)
            else:
                out[sym] = {"ok": False, "error": err}

    return {"ok": True, "data": out}


def last_valid_row(df, key_cols=None):
    """v0.88 防护：取最后一个关键字段非NaN的行，跳过"当天未结算完"的半成品NaN行。

    用于修复美债/汇率/商品等延迟更新日线 iloc[-1] 取到整行NaN 的问题
    (如 bond_zh_us_rate 最新一行常是当天日期但美债列尚未结算，全为NaN)。
    - key_cols: str 或 list[str]，要求这些列非NaN；None 时退化为最后一个非全NaN行。
    返回 pandas Series(一行)；df 为空返回 None。
    """
    if df is None or len(df) == 0:
        return None
    if key_cols:
        cols = [c for c in (key_cols if isinstance(key_cols, (list, tuple)) else [key_cols]) if c in df.columns]
        if cols:
            valid = df.dropna(subset=cols)
            if len(valid) > 0:
                return valid.iloc[-1]
    valid_any = df.dropna(how="all")
    return valid_any.iloc[-1] if len(valid_any) > 0 else df.iloc[-1]


def get_us_treasury() -> dict:
    """中美国债收益率。返回最新一行的美债10Y/30Y/2Y。"""
    cached = _cache_get("us_treasury", 3600)
    if cached is not None:
        return cached
    ak = _ak()
    if _cb_is_open("bond_zh_us_rate"):
        return {"ok": False, "error": "circuit_open: bond_zh_us_rate"}
    ok, df, err = _safe_call("bond_zh_us_rate", lambda: ak.bond_zh_us_rate(start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d")))
    _cb_record_success("bond_zh_us_rate") if ok else _cb_record_failure("bond_zh_us_rate")
    if not ok or df is None or df.empty:
        return {"ok": False, "error": err}
    df = df.sort_values("日期")
    last = last_valid_row(df, "美国国债收益率30年")  # v0.88: 跳过当天未结算完的NaN半成品行(美债熔断关键)
    rec = {
        "ok": True,
        "date": str(last["日期"]),
        "us_10y": _f(last.get("美国国债收益率10年")),
        "us_30y": _f(last.get("美国国债收益率30年")),
        "us_2y": _f(last.get("美国国债收益率2年")),
        "cn_10y": _f(last.get("中国国债收益率10年")),
        "yield_breakout_5pct": _f(last.get("美国国债收益率10年"), 0) >= 5.0,  # STRATEGY_DEPOSIT 策略B触发
    }
    _cache_set("us_treasury", rec)
    return rec


def get_usd_cny() -> dict:
    """央行汇率(USD/CNY)。返回最新中间价/中行折算价。"""
    cached = _cache_get("usd_cny", 3600)
    if cached is not None:
        return cached
    ak = _ak()
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
    if _cb_is_open("currency_boc_sina"):
        return {"ok": False, "error": "circuit_open: currency_boc_sina"}
    ok, df, err = _safe_call("currency_boc_sina", lambda: ak.currency_boc_sina(symbol="美元", start_date=start, end_date=end))
    _cb_record_success("currency_boc_sina") if ok else _cb_record_failure("currency_boc_sina")
    if not ok or df is None or df.empty:
        return {"ok": False, "error": err}
    df = df.sort_values("日期")
    last = last_valid_row(df, "中行折算价")  # v0.88: 跳过当天未结算完的NaN行
    rec = {
        "ok": True,
        "date": str(last["日期"]),
        "mid_price": _f(last.get("央行中间价")),
        "boc_rate": _f(last.get("中行折算价")),
        "buy": _f(last.get("中行汇买价")),
        "sell": _f(last.get("中行钞卖价/汇卖价")),
    }
    _cache_set("usd_cny", rec)
    return rec


# =========================================================
# 7. 交易日历
# =========================================================
def get_trade_calendar() -> dict:
    """交易日历。返回 {ok, dates:set, is_trading_today, next_trade_date}"""
    cached = _cache_get("trade_cal", 86400)  # 缓存1天
    if cached is not None:
        return cached
    ak = _ak()
    ok, df, err = _safe_call("tool_trade_date_hist_sina", ak.tool_trade_date_hist_sina)
    if not ok or df is None or df.empty:
        return {"ok": False, "error": err}
    dates = set()
    for d in df["trade_date"].tolist():
        dates.add(str(d).replace("-", "")[:8])
    today = datetime.now().strftime("%Y%m%d")
    is_today = today in dates
    nxt = None
    for i in range(1, 15):
        cand = (datetime.now() + timedelta(days=i)).strftime("%Y%m%d")
        if cand in dates:
            nxt = cand
            break
    rec = {"ok": True, "count": len(dates), "is_trading_today": is_today, "next_trade_date": nxt, "dates_sample": sorted(dates)[-10:]}
    _cache_set("trade_cal", rec)
    return rec


# =========================================================
# 趋势股判断（解决均线回归偏见）
# =========================================================
def is_trend_stock(closes: list, highs: list, vols: list) -> dict:
    """
    判断是否为趋势股（解决均线回归偏见）
    
    问题背景：
    - 原有逻辑用"等回调到MA20"策略，在趋势市中导致踏空
    - 趋势股沿着MA5上涨，不会回到MA20
    - 例如：兆易创新一周涨40%，但MA20只涨11%，系统一直建议等回调，导致完全踏空
    
    解决方案：
    - 震荡股：用"回调买入"（等回调到MA20）
    - 趋势股：用"突破买入"（突破MA5且放量→买入）
    
    趋势股判断标准：
    1. 连续3天收盘在MA5之上
    2. 最近3天有2天创新高
    3. 量比(LR)>1.2
    
    Args:
        closes: 收盘价列表（至少5天）
        highs: 最高价列表（至少5天）
        vols: 成交量列表（至少20天）
    
    Returns:
        {
            "is_trend": bool,  # 是否为趋势股
            "strategy": str,   # 推荐策略："趋势跟踪" / "均值回归"
            "buy_signal": str, # 买入信号描述
            "stop_loss_ref": str, # 止损参考："MA5" / "MA20"
            "reasons": list    # 判断理由
        }
    """
    if len(closes) < 5 or len(highs) < 5 or len(vols) < 20:
        return {
            "is_trend": False,
            "strategy": "均值回归",
            "buy_signal": "数据不足，默认用均值回归",
            "stop_loss_ref": "MA20",
            "reasons": ["数据不足"]
        }
    
    ma5 = sum(closes[-5:]) / 5
    reasons = []
    
    # 条件1：连续3天收盘在MA5之上
    above_ma5_count = sum(1 for c in closes[-3:] if c > ma5)
    above_ma5 = above_ma5_count == 3
    reasons.append(f"连续3天在MA5之上: {above_ma5_count}/3 {'✅' if above_ma5 else '❌'}")
    
    # 条件2：最近3天有2天创新高
    new_highs_count = sum(1 for i in range(-3, 0) if highs[i] > highs[i-1])
    new_highs = new_highs_count >= 2
    reasons.append(f"最近3天创新高: {new_highs_count}/3 {'✅' if new_highs else '❌'}")
    
    # 条件3：量比>1.2
    vol_ma20 = sum(vols[-20:]) / 20
    lr = vols[-1] / vol_ma20 if vol_ma20 > 0 else 0
    lr_ok = lr > 1.2
    reasons.append(f"量比LR={lr:.2f} {'✅' if lr_ok else '❌'}")
    
    is_trend = above_ma5 and new_highs and lr_ok
    
    if is_trend:
        return {
            "is_trend": True,
            "strategy": "趋势跟踪",
            "buy_signal": f"突破MA5({ma5:.2f})且放量→买入（不等回调）",
            "stop_loss_ref": "MA5",
            "reasons": reasons
        }
    else:
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
        return {
            "is_trend": False,
            "strategy": "均值回归",
            "buy_signal": f"等回调到MA20({ma20:.2f})",
            "stop_loss_ref": "MA20",
            "reasons": reasons
        }


# =========================================================
# 辅助函数
# =========================================================
def _clean_code(code: str) -> str:
    """清理代码：去掉 sz/sh 前缀，只留6位数字。"""
    return "".join(c for c in str(code) if c.isdigit())


def _f(val, default=None) -> Optional[float]:
    """安全转 float。NaN/None/异常返回 default。"""
    if val is None:
        return default
    try:
        f = float(val)
        if f != f:  # NaN
            return default
        return round(f, 4) if abs(f) < 1e9 else f
    except (ValueError, TypeError):
        return default


# =========================================================
# 自测
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("data_layer 自测")
    print("=" * 60)

    print("\n[1] 个股日K + 均线 (300502)")
    h = get_stock_hist("300502", 120)
    if h.get("ok"):
        print(f"  最新日期={h['latest_date']} 收盘={h['latest']['close']} 涨跌={h['latest']['pct']}%")
        print(f"  MA5={h['ma5']} MA10={h['ma10']} MA20={h['ma20']} MA60={h['ma60']}")
        print(f"  量能LR={h['lr']} 近20日高={h['recent_high20']} 低={h['recent_low20']}")
    else:
        print(f"  ERR: {h.get('error')}")

    print("\n[2] 大盘指数 沪深300/创业板")
    for sym, name in [("sh000300", "沪深300"), ("sz399006", "创业板")]:
        idx = get_index_daily(sym)
        if idx.get("ok"):
            print(f"  {name}: 收盘={idx['latest_close']} 涨跌={idx['pct']}% MA20={idx['ma20']} 站上MA20={idx['above_ma20']}")
        else:
            print(f"  {name} ERR: {idx.get('error')}")

    print("\n[3] 行业板块涨跌(前5/后5)")
    sb = get_sector_board()
    if sb.get("ok"):
        ss = sb["sectors"]
        for s in ss[:5]:
            print(f"  ↑ {s['name']} {s['pct']}%")
        print("  ...")
        for s in ss[-5:]:
            print(f"  ↓ {s['name']} {s['pct']}%")

    print("\n[4] 隔夜美股 NVDA/AMD/TSLA")
    us = get_us_market()
    for sym, d in us.get("data", {}).items():
        if d.get("close"):
            print(f"  {sym}: 收盘={d['close']} 涨跌={d.get('pct')}% 日期={d.get('date')}")

    print("\n[5] 美债10Y/30Y + USD/CNY")
    tr = get_us_treasury()
    if tr.get("ok"):
        print(f"  美10Y={tr['us_10y']}% 美30Y={tr['us_30y']}% 突破5%生死线={tr['yield_breakout_5pct']}")
    fx = get_usd_cny()
    if fx.get("ok"):
        print(f"  USD/CNY 中间价={fx['mid_price']} 中行折算={fx.get('boc_rate')}")

    print("\n[6] 交易日历")
    tc = get_trade_calendar()
    print(f"  今日是否交易日={tc.get('is_trading_today')} 下一交易日={tc.get('next_trade_date')}")

    print("\n[7] 单股实时(优先缓存)")
    rt = get_stock_realtime("300502")
    print(f"  300502: {rt.get('name')} 价={rt.get('price')} 涨跌={rt.get('pct')}% 量比={rt.get('volume_ratio')} 源={rt.get('source')}")

    print("\n" + "=" * 60)
    print("data_layer 自测完成")
