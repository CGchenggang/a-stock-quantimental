# -*- coding: utf-8 -*-
"""unlock_calendar.py — A股限售解禁日历模块（重建版）
数据源: akshare 解禁接口（尽力拉取，失败降级）。
接口:
  get_upcoming_unlocks(ticker, window_days=30) -> [{"date","shares_wan","pct_of_total","market_value_yi"}]
  unlock_risk(ticker, window_days=30) -> {"has_unlock": bool, "risk_level": "高/中/低", "detail": ...}
"""
from datetime import datetime

WINDOW_DEFAULT = 30


def _try_ak_detail(ticker):
    import akshare as ak
    frames = []
    for fn in ("stock_restricted_release_detail_em", "stock_restricted_release_detail_sina"):
        try:
            f = getattr(ak, fn, None)
            if f is None:
                continue
            df = f(symbol=ticker)
            frames.append(df)
        except Exception:
            continue
    return frames


def get_upcoming_unlocks(ticker: str, window_days: int = WINDOW_DEFAULT) -> list:
    today = datetime.now().date()
    out = []
    for df in _try_ak_detail(ticker):
        try:
            date_col = None
            for c in df.columns:
                s = str(c)
                if ("解禁" in s and "时间" in s) or "日期" in s:
                    date_col = c
                    break
            if date_col is None:
                continue
            for _, row in df.iterrows():
                try:
                    d = datetime.strptime(str(row[date_col])[:10], "%Y-%m-%d").date()
                except Exception:
                    continue
                days = (d - today).days
                if 0 <= days <= window_days:
                    item = {"date": d.isoformat(), "in_days": days}
                    for c in df.columns:
                        s = str(c)
                        if "数量" in s or "股数" in s:
                            item["shares_wan"] = row[c]
                        if "占总股本" in s or "比例" in s:
                            item["pct_of_total"] = row[c]
                        if "市值" in s:
                            item["market_value_yi"] = row[c]
                    out.append(item)
        except Exception:
            continue
    out.sort(key=lambda x: x["in_days"])
    return out


def unlock_risk(ticker: str, window_days: int = WINDOW_DEFAULT) -> dict:
    """解禁风险评级：14天内大额解禁=高；30天内=中；无=低"""
    ups = get_upcoming_unlocks(ticker, window_days)
    if not ups:
        return {"has_unlock": False, "risk_level": "低", "detail": "窗口内无解禁"}
    first = ups[0]
    pct = first.get("pct_of_total")
    risk = "中"
    try:
        if first["in_days"] <= 14 and pct is not None and float(str(pct).replace("%", "")) >= 3:
            risk = "高"
    except Exception:
        pass
    return {"has_unlock": True, "risk_level": risk, "detail": first, "all": ups}


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "603986"
    print(unlock_risk(code))
