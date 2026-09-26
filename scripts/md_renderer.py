# -*- coding: utf-8 -*-
"""md_renderer.py — 诊断结果 Markdown 渲染模块（重建版）
接口按 stock_diagoser 调用点还原：
  render_diagnosis(result: dict) -> str   单标的诊断报告
  render_pool_summary(results: list) -> str  持仓池汇总
result 为 stock_diagoser 的诊断 dict（8维+操作建议），字段缺失时优雅降级。
"""
from datetime import datetime


def _g(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


def render_diagnosis(result):
    """单标的诊断 dict -> Markdown。宽容未知结构。"""
    if not isinstance(result, dict):
        return str(result)
    code = result.get("code") or result.get("ticker") or "?"
    name = result.get("name", "")
    price = result.get("price") or result.get("close")
    action = _g(result, "advice", "action") or result.get("action") or "N/A"
    lines = ["## 诊断 %s %s (%s)" % (name, code, datetime.now().strftime("%m-%d %H:%M")), ""]
    lines.append("**现价**: %s   **操作建议**: **%s**" % (price, action))
    # 8维要点
    dims = result.get("dimensions") or {}
    if isinstance(dims, dict) and dims:
        lines.append("")
        lines.append("| 维度 | 结论 |")
        lines.append("|---|---|")
        for k, v in dims.items():
            gist = v if isinstance(v, str) else json_dump_short(v)
            lines.append("| %s | %s |" % (k, gist[:80]))
    # 关键位
    levels = result.get("levels") or result.get("key_levels") or {}
    if isinstance(levels, dict) and levels:
        lines.append("")
        kv = "  ".join("%s=%s" % (k, v) for k, v in list(levels.items())[:8])
        lines.append("**关键位**: %s" % kv)
    advice = _g(result, "advice") or {}
    if isinstance(advice, dict) and advice.get("reason"):
        lines.append("")
        lines.append("**理由**: %s" % advice["reason"])
    gaps = result.get("data_gaps") or []
    if gaps:
        lines.append("")
        lines.append("> 数据缺口: %s" % "; ".join(map(str, gaps[:5])))
    return "\n".join(lines)


def render_pool_summary(results):
    """多标的诊断 list -> 汇总 Markdown"""
    if not isinstance(results, list):
        results = [results]
    lines = ["## 持仓池诊断汇总 (%s)" % datetime.now().strftime("%m-%d %H:%M"), ""]
    lines.append("| 标的 | 现价 | 建议 | 备注 |")
    lines.append("|---|---|---|---|")
    for r in results:
        if not isinstance(r, dict):
            continue
        code = r.get("code") or r.get("ticker") or "?"
        name = r.get("name", "")
        price = r.get("price") or r.get("close") or "-"
        action = _g(r, "advice", "action") or r.get("action") or "-"
        note = ""
        gaps = r.get("data_gaps") or []
        if gaps:
            note = str(gaps[0])[:30]
        lines.append("| %s %s | %s | %s | %s |" % (name, code, price, action, note))
    okn = sum(1 for r in results if isinstance(r, dict) and not (r.get("data_gaps") or []))
    lines.append("")
    lines.append("> 完整诊断 %d/%d" % (okn, len(results)))
    return "\n".join(lines)


def json_dump_short(v, limit=80):
    import json as _j
    try:
        s = _j.dumps(v, ensure_ascii=False, default=str)
    except Exception:
        s = str(v)
    return s[:limit]


if __name__ == "__main__":
    demo = {"code": "603986", "name": "兆易创新", "price": 371.88,
            "advice": {"action": "减仓", "reason": "空头排列+板块失血"},
            "levels": {"stop_loss": 353.29, "MA20": 401.2},
            "dimensions": {"trend": "空头排列", "fundflow": "净流出"},
            "data_gaps": ["分时不可用"]}
    print(render_diagnosis(demo))
    print()
    print(render_pool_summary([demo, {"code": "600176", "name": "中国巨石", "price": 40.18}]))
