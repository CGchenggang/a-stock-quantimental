# -*- coding: utf-8 -*-
"""股民情绪分析 — 多源融合版（雪球 + 东方财富）。重建版 v2.0

数据源策略:
  1. 东方财富股吧 (默认主力): 无需 Cookie、无 WAF，requests 直连，速度快
  2. 雪球 (Playwright 增强源): 需安装 Playwright，用真浏览器穿透 WAF

两源帖子合并去重后统一送 jieba + 金融情感词典打分。

用法:
  持仓池批量(默认): python scripts/xueqiu_sentiment.py
  单股分析:         python scripts/xueqiu_sentiment.py 002371
  仅东财:           python scripts/xueqiu_sentiment.py --source eastmoney
  保存报告:         python scripts/xueqiu_sentiment.py --save-report
  调试模式:         python scripts/xueqiu_sentiment.py --debug

不指定代码时自动读取 database/auto_target_pool.json 中全部股票，
静默采集后仅输出每只股票的情绪分类统计汇总表。

输出: database/sentiment/{code}_sentiment_{date}.json
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ---- 路径 ----
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
if not (SKILL_DIR / "database").is_dir():
    FALLBACK = Path(r"F:\软件-图书仓库\skills\a-stock-quantimental")
    if (FALLBACK / "database").is_dir():
        SKILL_DIR = FALLBACK
sys.path.insert(0, str(SCRIPT_DIR))
OUTPUT_DIR = SKILL_DIR / "database" / "sentiment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---- 金融情感词典（内置精简版，可扩库）----
POS_WORDS = ["利好", "涨停", "大涨", "暴涨", "放量上攻", "流入", "增持", "回购", "超预期",
             "突破", "新高", "龙头", "业绩预增", "订单", "中标", "涨价", "反弹", "企稳",
             "主力进入", "北向加仓", "机构调研", "积极", "看多", "买入", "强烈推荐"]
NEG_WORDS = ["利空", "跌停", "大跌", "暴跌", "杀跌", "流出", "减持", "质押", "爆雷", "暴雷",
             "跌破", "新低", "套牢", "割肉", "止损", "业绩预减", "亏损", "退市", "立案",
             "调查", "警示", "看空", "卖出", "逃命", "踩踏", "崩", "杀多", "不乐观"]

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def score_text(text: str) -> int:
    """单条帖子打分: -2~+2"""
    s = 0
    for w in POS_WORDS:
        if w in text:
            s += 1
            break
    for w in POS_WORDS:
        s += min(text.count(w), 2)
    for w in NEG_WORDS:
        if w in text:
            s -= 1
            break
    for w in NEG_WORDS:
        s -= min(text.count(w), 2)
    return max(-2, min(2, s))


def fetch_eastmoney(code: str, count: int, debug: bool = False) -> list:
    """东方财富股吧帖子列表（标题级），尽力拉取"""
    if not HAS_REQUESTS:
        return []
    url = "https://guba.eastmoney.com/list,%s.html" % code
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
        # 股吧帖子标题出现在 multiple 属性位；放宽长度并去导航项
        titles = re.findall(r'title="([^"]{8,120})"', r.text)
        titles = [t for t in titles if not re.search(r"股吧|首页|排行|广场|客户端|直播|帮助|反馈", t)]
        if debug:
            print("  [eastmoney] %s 取得 %d 条" % (code, len(titles)))
        return [{"source": "eastmoney", "text": t} for t in titles[:count]]
    except Exception as e:
        if debug:
            print("  [eastmoney] %s 失败: %s" % (code, str(e)[:60]))
        return []


def fetch_xueqiu_playwright(code: str, count: int, debug: bool = False) -> list:
    """雪球增强源：需 Playwright，未安装则跳过"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if debug:
            print("  [xueqiu] Playwright 未安装，跳过")
        return []
    posts = []
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(headless=True)
            page = b.new_page()
            page.goto("https://xueqiu.com/S/%s" % code, timeout=20000)
            page.wait_for_timeout(3000)
            nodes = page.query_selector_all(".timeline__item .content")
            for n in nodes[:count]:
                txt = n.inner_text()
                if txt:
                    posts.append({"source": "xueqiu", "text": txt[:200]})
            b.close()
    except Exception as e:
        if debug:
            print("  [xueqiu] %s 失败: %s" % (code, str(e)[:60]))
    return posts


def collect_posts(code: str, count: int, sources: list, debug: bool = False) -> list:
    """从多个数据源采集帖子，合并去重"""
    posts = []
    if "eastmoney" in sources:
        posts += fetch_eastmoney(code, count, debug)
    if "xueqiu_playwright" in sources:
        posts += fetch_xueqiu_playwright(code, count, debug)
    # 去重
    seen, uniq = set(), []
    for p in posts:
        k = p["text"][:50]
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq


def analyze_posts(posts: list) -> dict:
    """打分汇总 -> sentiment_score(-100~+100) + 分类"""
    if not posts:
        return {"sentiment_score": 0, "label": "无数据", "n_posts": 0,
                "pos": 0, "neg": 0, "neu": 0}
    scores = [score_text(p["text"]) for p in posts]
    pos = sum(1 for s in scores if s > 0)
    neg = sum(1 for s in scores if s < 0)
    neu = len(scores) - pos - neg
    raw = sum(scores)
    score = max(-100, min(100, int(raw * 100 / max(len(scores), 1))))
    if score >= 40:
        label = "过热"
    elif score >= 15:
        label = "偏热"
    elif score > -15:
        label = "中性"
    elif score > -40:
        label = "偏冷"
    else:
        label = "冰点"
    return {"sentiment_score": score, "label": label, "n_posts": len(posts),
            "pos": pos, "neg": neg, "neu": neu}


def load_pool_codes() -> list:
    pool = SKILL_DIR / "database" / "auto_target_pool.json"
    codes = []
    if pool.exists():
        try:
            d = json.load(open(pool, encoding="utf-8"))
            items = d if isinstance(d, list) else [d[k] for k in d if re.fullmatch(r"\d{6}", str(k))]
            for item in items:
                if isinstance(item, dict):
                    t = str(item.get("ticker") or item.get("code") or "")
                    if re.fullmatch(r"\d{6}", t):
                        codes.append(t)
        except Exception:
            pass
    if not codes:
        sectors = SKILL_DIR / "database" / "sectors.json"
        if sectors.exists():
            try:
                d = json.load(open(sectors, encoding="utf-8"))
                codes = [h.get("ticker") for h in d.get("holdings", []) if h.get("ticker")]
            except Exception:
                pass
    return codes


def main():
    args = sys.argv[1:]
    debug = "--debug" in args
    save = "--save-report" in args
    source = "eastmoney" if "--source" in args else "eastmoney"
    codes = [a for a in args if re.fullmatch(r"\d{6}", a)]
    count = 50
    if not codes:
        codes = load_pool_codes()
    if not codes:
        print("无分析目标（未指定代码且无持仓池）")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    print("情绪分析 %d 只标的, 源=%s" % (len(codes), source))
    summary = []
    for code in codes:
        posts = collect_posts(code, count, [source, "xueqiu_playwright"], debug)
        r = analyze_posts(posts)
        r.update({"ticker": code, "date": today})
        summary.append(r)
        print("  %s score=%4d %-4s (帖%d: 多%d 空%d 中%d)" % (
            code, r["sentiment_score"], r["label"], r["n_posts"], r["pos"], r["neg"], r["neu"]))
        out = OUTPUT_DIR / ("%s_sentiment_%s.json" % (code, today.replace("-", "")))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
        time.sleep(0.5)
    if save:
        rp = SKILL_DIR / "database" / "sentiment_report.md"
        with open(rp, "w", encoding="utf-8") as f:
            f.write("# 情绪汇总 %s\n\n| 代码 | 得分 | 分类 | 帖数 |\n|---|---|---|---|\n" % today)
            for r in summary:
                f.write("| %s | %d | %s | %d |\n" % (r["ticker"], r["sentiment_score"], r["label"], r["n_posts"]))
        print("汇总已存 %s" % rp)


if __name__ == "__main__":
    main()
