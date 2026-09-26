# -*- coding: utf-8 -*-
"""fetch_latest.py v2.0 — 持仓池实时行情快照

改用 data_layer 接口(新浪全市场+分时兜底+日K)，不再直连 akshare。
标的列表从 auto_target_pool.json 动态读取。

输出: database/latest_stock_data.json
用法: python fetch_latest.py [--pool CODE1,CODE2,...]
"""
import sys
import os
import json
import argparse
from datetime import datetime

# 确保能 import data_layer
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

import data_layer as dl

DB_DIR = os.path.join(SKILL_DIR, "database")

DEFAULT_CODES = [
    "603986", "300502", "002371", "002896",
    "300476", "601088", "000977", "600176",
]


def load_pool_codes():
    """从 auto_target_pool.json 读取标的列表"""
    pool_path = os.path.join(DB_DIR, "auto_target_pool.json")
    if not os.path.exists(pool_path):
        print(f"  [WARN] \u672a\u627e\u5230 {pool_path}\uff0c\u4f7f\u7528\u9ed8\u8ba4\u6807\u7684\u5217\u8868")
        return DEFAULT_CODES

    with open(pool_path, encoding="utf-8") as f:
        pool = json.load(f)

    codes = []
    items = pool if isinstance(pool, list) else pool.get("stocks", pool.get("items", []))
    for item in items:
        c = item.get("code") or item.get("ticker", "")
        if c and c not in codes:
            codes.append(c)

    return codes if codes else DEFAULT_CODES


def fetch_one(code: str) -> dict:
    """获取单只标的: 实时行情 + 日K(MA/LR)"""
    # 1) 实时行情 (新浪全市场 -> 分时 -> 日K 三级兜底)
    rt = dl.get_stock_realtime(code)
    if not rt.get("ok"):
        return {
            "code": code,
            "ok": False,
            "error": rt.get("error", "\u5b9e\u65f6\u884c\u60c5\u83b7\u53d6\u5931\u8d25"),
        }

    result = {
        "code": code,
        "ok": True,
        "name": rt.get("name", ""),
        "price": rt.get("price"),
        "pct": rt.get("pct"),
        "open": rt.get("open"),
        "high": rt.get("high"),
        "low": rt.get("low"),
        "volume": rt.get("volume"),
        "prev_close": rt.get("prev_close"),
        "turnover": rt.get("turnover"),
        "volume_ratio": rt.get("volume_ratio"),
        "source": rt.get("source", "unknown"),
    }

    # 2) 日K -> MA + LR
    hist = dl.get_stock_hist(code, days=60)
    if hist.get("ok"):
        result.update({
            "ma5": hist.get("ma5"),
            "ma10": hist.get("ma10"),
            "ma20": hist.get("ma20"),
            "ma60": hist.get("ma60"),
            "lr": hist.get("lr"),
            "vol_ma20": hist.get("vol_ma20"),
            "latest_date": hist.get("latest_date"),
        })
    else:
        result["_hist_error"] = hist.get("error", "\u65e5K\u83b7\u53d6\u5931\u8d25")

    return result


def main():
    parser = argparse.ArgumentParser(description="\u6301\u4ed3\u6c60\u5b9e\u65f6\u884c\u60c5\u5feb\u7167 v2.0")
    parser.add_argument(
        "--pool", type=str, default="",
        help="\u6307\u5b9a\u6807\u7684\u4ee3\u7801(\u9017\u53f7\u5206\u9694)\uff0c\u4e0d\u6307\u5b9a\u5219\u4ece auto_target_pool.json \u8bfb\u53d6",
    )
    args = parser.parse_args()

    # 确定标的列表
    if args.pool:
        codes = [c.strip() for c in args.pool.split(",") if c.strip()]
        print(f"[fetch_latest] \u624b\u52a8\u6307\u5b9a {len(codes)} \u53ea\u6807\u7684")
    else:
        codes = load_pool_codes()
        print(f"[fetch_latest] \u4ece auto_target_pool.json \u8bfb\u53d6 {len(codes)} \u53ea\u6807\u7684")

    print(f"  \u6807\u7684: {', '.join(codes)}")
    print()

    # 逐只获取
    result = []
    success = 0
    for code in codes:
        row = fetch_one(code)
        if row.get("ok"):
            name = row.get("name", "")
            price = row.get("price", "?")
            pct = row.get("pct", "?")
            ma20 = row.get("ma20", "?")
            lr = row.get("lr", "?")
            print(f"  [OK] {name}({code}) \u4ef7={price} \u6da8\u8dcc={pct}% MA20={ma20} LR={lr}")
            success += 1
        else:
            print(f"  [FAIL] {code}: {row.get('error', '')}")
        result.append(row)

    # 输出到 database/
    out_path = os.path.join(DB_DIR, "latest_stock_data.json")
    payload = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "count": success,
        "total": len(result),
        "stocks": result,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] \u5df2\u4fdd\u5b58: {out_path}")
    print(f"   \u6210\u529f {success}/{len(result)}\uff0c\u65f6\u95f4 {payload['as_of']}")


if __name__ == "__main__":
    main()
