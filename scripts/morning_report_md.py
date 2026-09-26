# -*- coding: utf-8 -*-
"""morning_report_md.py — 汇总所有阶段产出为一份可读的 Markdown 总览
读取: index_trend / macro_report_latest / global_liquidity_report / morning_data / pre_market_今日
输出: database/MorningReport.md（批处理结束自动打开）
"""
import json
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "database")


def load(name):
    p = os.path.join(DB, name)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8")), p
        except Exception:
            pass
    return None, p


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    md = ["# 盘前数据与阶段分析总览", ""]
    gaps_all = []

    # ① 指数趋势四维
    it, _ = load("index_trend.json")
    md.append("## ① 指数趋势监控（股指期货四维）")
    if it:
        md.append("**市场状态: %s (总分 %d)**" % (it.get("market_state"), it.get("total_score", 0)))
        for k, v in (it.get("dimensions") or {}).items():
            md.append("- **%s** (评分 %d): %s" % (k, v.get("score", 0), v.get("detail", "")[:200]))
        if it.get("style"):
            md.append("- style: %s" % json.dumps(it["style"], ensure_ascii=False)[:120])
    else:
        md.append("index_trend.json 未生成")
    md.append("")

    # ② 宏观冲击
    mc, _ = load(os.path.join("macro_cache", "macro_report_latest.json"))
    md.append("## ② 宏观冲击审计")
    if mc:
        md.append("**composite_shock = %d %s**  动作: %s" % (
            mc.get("composite_shock", 0), mc.get("level", ""), mc.get("action", "")))
        md.append("**触发因子**: %s" % ("; ".join(mc.get("triggers", [])) or "无"))
        for l in mc.get("layers", []):
            md.append("- %s (得分 %d)" % (l.get("layer"), l.get("score", 0)))
    else:
        md.append("未生成")
    md.append("")

    # ③ 流动性雷达
    gl, _ = load("global_liquidity_report.json")
    md.append("## ③ 全球流动性雷达")
    if gl:
        md.append("**%s**  动作: %s" % (gl.get("level", ""), gl.get("action", "")))
        md.append("```")
        for k, v in (gl.get("sources") or {}).items():
            if v is not None:
                md.append("  %s = %s" % (k, v))
        md.append("```")
        gaps = gl.get("gaps", [])
        gaps_all += ["radar: " + g[:60] for g in gaps]
        md.append("数据缺口 %d 项" % len(gaps))
    else:
        md.append("未生成")
    md.append("")

    # ④ 晨间采集
    mdata, _ = load("morning_data.json")
    md.append("## ④ 晨间持仓采集")
    if mdata:
        dq = mdata.get("data_quality") or {}
        md.append("完整度 %s%%，警告: %s" % (dq.get("completeness", 0) * 100, "; ".join(dq.get("cautions", [])) or "无"))
        rows = []
        for s in mdata.get("stocks", []):
            rows.append([s.get("ticker"), s.get("name"), s.get("role"), s.get("close"),
                         s.get("MA20"), s.get("ma20_dist_pct"), s.get("LR"),
                         s.get("trend_health"), s.get("stop_loss")])
        md.append(table(["代码", "名称", "角色", "收盘", "MA20", "距MA20%", "LR", "健康", "止损"], rows))
        md.append("")
        md.append("**板块资金流（前5强/后5弱）**")
        sf = mdata.get("sector_flow") or []
        for r in (sf[:5] + sf[-5:]):
            md.append("- %s: 涨跌 %s%%" % (r.get("name"), r.get("pct")))
        md.append("")
        md.append("**隔夜环境**: 美债 %s | 汇率 %s | 美股 %s" % (
            json.dumps(mdata.get("us_treasury"), ensure_ascii=False)[:100],
            json.dumps(mdata.get("usd_cny"), ensure_ascii=False)[:80],
            json.dumps(mdata.get("us_market"), ensure_ascii=False)[:150]))
    else:
        md.append("未生成")
    md.append("")

    # ⑤ 盘前预案要点
    pm, pmp = load("pre_market_%s.json" % today)
    md.append("## ⑤ 盘前预案要点")
    if pm:
        md.append("生成于 %s" % pm.get("as_of"))
        for r in pm.get("portfolio_checkup", []):
            adv = (r.get("advice") or {}).get("action", "?")
            md.append("- %s %s: 建议 **%s**" % (r.get("name") or r.get("ticker"), r.get("ticker"), adv))
        ra = pm.get("risk_assessment") or {}
        md.append("- 风险评估: %s" % json.dumps(ra, ensure_ascii=False)[:200])
        gaps_all += ["pre_market: " + str(g)[:60] for g in (pm.get("data_quality") or {}).get("gaps", [])]
        md.append("")
        md.append("> 报告全文: %s" % pmp)
    else:
        md.append("今日未生成")
    md.append("")

    # 数据缺口汇总（去重：多次运行append同缺口只显示一次）
    uniq = list(dict.fromkeys(gaps_all))
    md.append("## 数据缺口汇总（%d 项，去重后）" % len(uniq))
    for g in uniq:
        md.append("- %s" % g)

    out = os.path.join(DB, "MorningReport.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    # 每日归档：当日数据快照 -> database/archive/YYYY-MM-DD/
    import shutil
    archive = os.path.join(DB, "archive", today)
    os.makedirs(archive, exist_ok=True)
    for name in ["morning_data.json", "global_liquidity_report.json", "index_trend.json",
                 os.path.join("macro_cache", "macro_report_latest.json"),
                 "pre_market_%s.json" % today]:
        src = os.path.join(DB, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(archive, os.path.basename(name)))
    print("归档: " + archive)


if __name__ == "__main__":
    main()
