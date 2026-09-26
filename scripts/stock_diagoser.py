# -*- coding: utf-8 -*-
"""盘中个股8维快速诊断 (stock_diagoser.py)

核心交付。输入股票代码，10秒内输出趋势/分时/量价/资金/相对强弱/技术位/板块联动/操作建议。

双模式：
- 按需查询：python stock_diagoser.py 300502
- 自动巡航：python stock_diagoser.py --pool   (诊断 auto_target_pool.json 全部)
- 推送飞书：python stock_diagoser.py 300502 --push

每个维度独立函数，失败降级跳过（记录到 data_gaps），绝不中断主流程。
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

# ── 修复 Git Bash / Windows 控制台 cp1252 编码问题 ─
# 当 stdout 非 UTF-8 时（如 Git Bash 默认 cp1252），强制包装为 UTF-8
# 这样 argparse help / print 中的中文字符就不会 UnicodeEncodeError
if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer') and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    import io as _io
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATABASE_DIR = SKILL_DIR / "database"

# 加入路径以便导入同目录模块
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
# 加入 skill 根目录以便导入 feishu_pusher
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import data_layer as dl  # noqa: E402
import md_renderer  # noqa: E402
import trading_discipline  # noqa: E402


# =========================================================
# 8 维诊断函数
# =========================================================

def calc_bias_rate(price, hist) -> dict:
    """⑧.⑥ 乖离率监控（v0.90新增）。

    计算价格 vs MA5/10/20/60 的乖离率，判断是否过热或超卖。
    乖离率 = (现价 - MA) / MA * 100%

    判定阈值（分层）：
    - MA5/MA10 短期乖离 > 15%: 警觉
    - MA20 中期乖离 > 25%: 强制降仓
    - MA60 长期乖离 > 40%: 极端信号
    - 乖离 < -10%: 超卖关注
    - 乖离 < -20%: 极端超卖
    """
    if not hist.get("ok"):
        return {"ok": False, "biases": {}, "max_bias": 0, "risk": "UNKNOWN", "action": "数据不可用"}

    ma5 = hist.get("ma5")
    ma10 = hist.get("ma10")
    ma20 = hist.get("ma20")
    ma60 = hist.get("ma60")
    p = price if price else hist["latest"]["close"]

    biases = {}
    for name, ma_val in [("ma5", ma5), ("ma10", ma10), ("ma20", ma20), ("ma60", ma60)]:
        if ma_val and ma_val > 0:
            biases[name] = round((p - ma_val) / ma_val * 100, 2)

    if not biases:
        return {"ok": False, "biases": {}, "max_bias": 0, "risk": "UNKNOWN", "action": "均线数据不可用"}

    max_bias = max(biases.values())
    min_bias = min(biases.values())

    # 分层判定：短期(MA5/MA10) 和 中长期(MA20/MA60) 分别评估
    short_bias = max(biases.get("ma5", 0), biases.get("ma10", 0))
    mid_bias = biases.get("ma20", 0)
    long_bias = biases.get("ma60", 0)

    if max_bias > 40 or long_bias > 40:
        risk = "EXTREME_OVERHEAT"
        action = "禁止开新仓，建议减仓至30%以下"
    elif mid_bias > 25 or short_bias > 30:
        risk = "OVERHEAT"
        action = "仓位上限-10%，止损收紧1%，禁止加仓"
    elif short_bias > 15:
        risk = "WARM"
        action = "趋势偏热，关注回调风险，不追高"
    elif min_bias < -20:
        risk = "EXTREME_OVERSOLD"
        action = "极端超卖，关注左侧机会，可分批试探"
    elif min_bias < -10:
        risk = "OVERSOLD"
        action = "超卖区间，关注反弹信号"
    else:
        risk = "NORMAL"
        action = "乖离率正常"

    return {
        "ok": True,
        "biases": biases,
        "max_bias": max_bias,
        "min_bias": min_bias,
        "short_bias": short_bias,
        "mid_bias": mid_bias,
        "long_bias": long_bias,
        "risk": risk,
        "action": action,
    }


def classify_pullback_vs_breakdown(hist, current_price, lr=None) -> dict:
    """⑧.⑦ 回踩vs破位判定器（v0.90新增）。

    核心问题：多头排列中的下跌不一定是回踩，可能是破位。
    7/2兆易创新跳空跌停时均线仍呈多头排列（滞后），
    但这是破位不是回踩。

    判定维度（评分制，>=4分为破位）：
    1. 回撤幅度：从近期高点回撤>5% +1，>10% +2
    2. 成交量方向：放量(LR>1.2) +1，缩量(LR<0.8) -1
    3. 连续阴线数：>=3根 +1
    4. MA5斜率：拐头向下 +1
    5. 跌停：直接 +5（极端事件，一票否决）
    """
    if not hist.get("ok"):
        return {"ok": False, "classification": "UNKNOWN", "confidence": 0, "score": 0, "reason": "数据不可用", "action": "无法判定"}

    # 从hist获取近5日K线数据
    daily = hist.get("daily_list", [])
    if len(daily) < 5:
        closes_tail = hist.get("closes_tail", [])
        if len(closes_tail) < 3:
            return {"ok": False, "classification": "UNKNOWN", "confidence": 0, "score": 0, "reason": "K线数据不足", "action": "无法判定"}
        daily = [{"close": c, "open": c, "high": c, "low": c, "volume": 0} for c in closes_tail]

    recent = daily[-5:] if len(daily) >= 5 else daily

    # 维度1: 回撤幅度
    recent_high = max(d.get("high", d.get("close", 0)) for d in recent)
    drawdown = (current_price - recent_high) / recent_high * 100 if recent_high > 0 else 0

    # 维度2: 成交量方向
    vols = [d.get("volume", 0) for d in recent]
    vol_today = vols[-1] if vols else 0
    vol_avg = sum(vols[:-1]) / max(len(vols) - 1, 1) if len(vols) > 1 else 0
    vol_ratio = vol_today / vol_avg if vol_avg > 0 else 1
    if lr is not None and lr > 0:
        vol_ratio = max(vol_ratio, lr)

    # 维度3: 连续阴线数
    bearish_count = sum(1 for d in recent if d.get("close", 0) < d.get("open", 0))

    # 维度4: MA5斜率
    closes = [d.get("close", 0) for d in recent]
    if len(closes) >= 5:
        ma5_today = sum(closes[-5:]) / 5
        ma5_3ago = sum(closes[-5:-3]) / 2
        ma5_slope_down = ma5_today < ma5_3ago
    else:
        ma5_slope_down = False

    # 维度5: 是否有跌停（单日跌幅>9.5%）
    has_limit_down = False
    for d in recent:
        c = d.get("close", 0)
        o = d.get("open", 0)
        prev_c = d.get("pre_close", o)
        if prev_c > 0 and (c - prev_c) / prev_c < -0.095:
            has_limit_down = True
            break
    if not has_limit_down:
        for d in recent:
            c = d.get("close", 0)
            o = d.get("open", 0)
            if o > 0 and (c - o) / o < -0.095:
                has_limit_down = True
                break

    # 综合评分
    breakdown_score = 0
    reasons = []

    if drawdown < -5:
        breakdown_score += 1
        reasons.append(f"回撤{drawdown:.1f}%")
    if drawdown < -10:
        breakdown_score += 2
        reasons.append(f"回撤幅度大({drawdown:.1f}%)")
    if vol_ratio > 1.2:
        breakdown_score += 1
        reasons.append(f"放量(量比{vol_ratio:.2f})")
    elif vol_ratio < 0.8:
        breakdown_score -= 1
        reasons.append(f"缩量(量比{vol_ratio:.2f})")
    if bearish_count >= 3:
        breakdown_score += 1
        reasons.append(f"连阴{bearish_count}天")
    if ma5_slope_down:
        breakdown_score += 1
        reasons.append("MA5拐头向下")
    if has_limit_down:
        breakdown_score += 5
        reasons.append("出现跌停")

    # 判定
    if breakdown_score >= 4 or has_limit_down:
        classification = "BREAKDOWN"
        confidence = min(breakdown_score * 15 + 20, 95)
        action = "禁止回踩买入，持仓者考虑减仓"
        reason_str = f"破位信号(评分{breakdown_score})：" + "，".join(reasons)
    elif breakdown_score <= 1:
        classification = "PULLBACK"
        confidence = 85 - abs(breakdown_score) * 10
        action = "可按回踩策略执行"
        reason_str = f"正常回踩(评分{breakdown_score})：" + "，".join(reasons) if reasons else "正常回踩"
    else:
        classification = "NEUTRAL"
        confidence = 50
        action = "观望，不执行买入"
        reason_str = f"信号混合(评分{breakdown_score})：" + "，".join(reasons) if reasons else "信号混合"

    return {
        "ok": True,
        "classification": classification,
        "confidence": confidence,
        "score": breakdown_score,
        "drawdown": round(drawdown, 2),
        "vol_ratio": round(vol_ratio, 2),
        "bearish_count": bearish_count,
        "ma5_slope_down": ma5_slope_down,
        "has_limit_down": has_limit_down,
        "reason": reason_str,
        "action": action,
    }


def analyze_trend(price, hist) -> dict:
    """① 趋势定性：实时价 vs MA5/10/20/60 多空排列 + 乖离率监控（v0.90增强）。"""
    if not hist.get("ok"):
        return {"verdict": "数据不可用", "detail": "日K数据获取失败", "ma": {}, "bias": {"ok": False}}

    ma5, ma10, ma20, ma60 = hist.get("ma5"), hist.get("ma10"), hist.get("ma20"), hist.get("ma60")
    ma = {"ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60}
    p = price if price else hist["latest"]["close"]

    # 判定多空排列
    parts = [x for x in [ma5, ma10, ma20, ma60] if x is not None]
    if len(parts) < 4:
        return {"verdict": "数据不足", "detail": "均线数据不全", "ma": ma, "bias": {"ok": False}}

    # 核心判定：价与MA20/MA60（中期趋势）+ MA5/MA10（短期节奏）
    above_ma20 = p > ma20
    above_ma60 = p > ma60
    ma5_above_ma20 = ma5 > ma20
    ma5_above_ma10 = ma5 > ma10

    if p > ma5 > ma10 > ma20 > ma60:
        verdict = "多头排列(强趋势)"
        detail = f"价{p}>MA5>MA10>MA20>MA60，趋势健康向上"
    elif above_ma20 and above_ma60 and ma5_above_ma20 and p > ma5:
        verdict = "多头排列(强势)"
        detail = f"价{p}>MA5>MA20>MA60，短中期多头，中期趋势向上"
    elif above_ma20 and above_ma60 and p > ma5:
        verdict = "多头格局(短期整理)"
        detail = f"价{p}>MA5且在MA20/MA60上方，中期多头，MA5({ma5})略低于MA10({ma10})属短期整理"
    elif above_ma20 and above_ma60 and ma5_above_ma20:
        verdict = "多头格局(回踩中)"
        detail = f"在MA20/MA60上方但价<MA5，多头格局中的回踩，关注MA20支撑"
    elif p < ma5 < ma10 < ma20:
        verdict = "空头排列(弱势)"
        detail = f"价{p}<MA5<MA10<MA20，趋势走弱，警惕"
    elif not above_ma20 and not above_ma60 and ma5 < ma20 < ma60 and p < ma5:
        verdict = "空头排列(强弱势)"
        detail = "长短均线全部空头，坚决回避"
    elif ma20 and abs(p - ma20) / ma20 < 0.02:
        verdict = "粘合震荡"
        detail = f"价格在MA20({ma20})附近缠绕，方向不明"
    else:
        verdict = "震荡分化"
        detail = f"均线排列混乱(价{p}/MA5{ma5}/MA10{ma10}/MA20{ma20}/MA60{ma60})，无明确趋势"

    # MA20 生命线风险提示
    if ma20 and p < ma20:
        detail += f" ｜ ⚠️跌破MA20生命线({ma20})"

    # v0.90新增：乖离率监控
    bias = calc_bias_rate(p, hist)
    if bias.get("ok"):
        max_bias = bias.get("max_bias", 0)
        risk = bias.get("risk", "NORMAL")
        if risk == "EXTREME_OVERHEAT":
            detail += f" ｜ 🔴极端过热(乖离{max_bias:+.1f}%)，禁止开新仓"
        elif risk == "OVERHEAT":
            detail += f" ｜ 🟠过热(乖离{max_bias:+.1f}%)，仓位上限-10%"
        elif risk == "WARM":
            detail += f" ｜ 🟡偏热(乖离{max_bias:+.1f}%)，不追高"
        elif risk == "EXTREME_OVERSOLD":
            detail += f" ｜ 🔵极端超卖(乖离{bias.get('min_bias', 0):.1f}%)，关注左侧机会"
        elif risk == "OVERSOLD":
            detail += f" ｜ 🟢超卖(乖离{bias.get('min_bias', 0):.1f}%)，关注反弹"

    return {"verdict": verdict, "detail": detail, "ma": ma, "bias": bias}


def calc_recovery_rate(hist: dict) -> dict:
    """⑥ 暴跌修复率（第6个健康度指标，v0.85 新增）。

    以近60日最低收盘价为基准，计算当前价格相对该低点的修复程度。
    衡量"距历史极端低点的安全边际"，借鉴claude-stock的锚定创伤方法。

    Args:
        hist: get_stock_hist() 返回的 dict（需含 closes_tail 字段）

    Returns:
        {
            "recent_low": float,      # 近60日最低收盘价
            "current_price": float,    # 当前价
            "recovery_pct": float,     # 修复率 = (现价-低点)/低点 * 100%
            "verdict": str,            # 判定结果
            "health_score": int        # 健康+2 / 衰减+1 / 反转0
        }
    """
    if not hist.get("ok"):
        return {"verdict": "数据不可用", "health_score": 0, "recovery_pct": None}

    latest = hist.get("latest", {})
    current = latest.get("close")
    if not current or current <= 0:
        return {"verdict": "价格无效", "health_score": 0, "recovery_pct": None}

    # 从日K线中取近60日最低收盘价
    # get_stock_hist 默认取120天数据，closes_tail只有近5天
    # 需要从完整K线中提取，这里用 recent_low20 做近似（20日低点）
    # 如果有更多数据可以用 hist 中的 closes 列表
    recent_low = hist.get("recent_low20")
    if not recent_low or recent_low <= 0:
        return {"verdict": "低点数据不足", "health_score": 0, "recovery_pct": None}

    recovery_pct = round((current - recent_low) / recent_low * 100, 2)

    if current < recent_low:
        verdict = "创新低"
        health_score = 0
    elif recovery_pct < 5:
        verdict = f"未修复(+{recovery_pct}%)，贴近低点{recent_low}"
        health_score = 0
    elif recovery_pct < 20:
        verdict = f"修复中(+{recovery_pct}%)，低点{recent_low}"
        health_score = 1
    else:
        verdict = f"已修复(+{recovery_pct}%)，低点{recent_low}"
        health_score = 2

    return {
        "recent_low": recent_low,
        "current_price": current,
        "recovery_pct": recovery_pct,
        "verdict": verdict,
        "health_score": health_score,
    }


def analyze_intraday(code) -> dict:
    """② 分时形态：是否站稳分时均线(VWAP黄线)。"""
    intra = dl.get_intraday(code)
    if not intra.get("ok"):
        return {"available": False, "note": "盘后/非盘中，分时数据不可用"}

    vwap = intra.get("vwap")
    last = intra.get("last_price")
    if not vwap or not last:
        return {"available": False, "note": "分时数据不完整"}

    # 计算分时走势方向（用末段 ticks）
    ticks = intra.get("ticks", [])
    if len(ticks) >= 10:
        recent = [t["price"] for t in ticks[-20:] if t.get("price")]
        early = [t["price"] for t in ticks[:20] if t.get("price")]
        if recent and early:
            slope = (sum(recent) / len(recent)) - (sum(early) / len(early))

    if last > vwap:
        if last > vwap * 1.01:
            verdict = "站稳分时线(偏强)"
            detail = f"现价{last}在VWAP{vwap}上方1%+，分时偏强"
        else:
            verdict = "分时线上方(中性偏强)"
            detail = f"现价{last}略高于VWAP{vwap}"
    elif last < vwap:
        if last < vwap * 0.99:
            verdict = "跌破分时线(偏弱)"
            detail = f"现价{last}在VWAP{vwap}下方1%+，分时偏弱，警惕"
        else:
            verdict = "分时线下方(中性偏弱)"
            detail = f"现价{last}略低于VWAP{vwap}"
    else:
        verdict = "贴着分时线(平衡)"
        detail = f"现价{last}贴近VWAP{vwap}"

    return {
        "available": True,
        "verdict": verdict,
        "vwap": vwap,
        "last_price": last,
        "detail": detail,
    }


def analyze_volume_price(snap, hist) -> dict:
    """③ 量价关系：量比/换手/LR量能火控/量价背离。"""
    if not hist.get("ok"):
        return {"verdict": "数据不可用", "detail": "日K缺失"}

    lr = hist.get("lr")  # 量能火控 = 今日量/MA20量
    turnover = snap.get("turnover") if snap else hist["latest"].get("turnover")
    pct = snap.get("pct") if snap else hist["latest"].get("pct")

    # LR 体制判定（SKILL.md 模块2量能火控）
    if lr is None:
        regime, verdict = "未知", "量能数据不全"
    elif lr < 0.6:
        regime, verdict = "冰冻期", "严重缩量(冰冻)"
    elif lr < 0.9:
        regime, verdict = "枯水期", "缩量(枯水)"
    elif lr < 1.1:
        regime, verdict = "平水期", "量能正常(平水)"
    elif lr < 1.5:
        regime, verdict = "丰水期", "温和放量(丰水)"
    else:
        regime, verdict = "洪水期", "显著放量(洪水)"

    # 量价背离判断
    detail = f"LR={lr}({regime})" if lr else "LR未知"
    if pct is not None and lr is not None:
        if pct > 3 and lr < 0.9:
            detail += " ｜ ⚠️涨而缩量(顶背离迹象)"
        elif pct < -3 and lr > 1.3:
            detail += " ｜ ⚠️跌而放量(恐慌/出货行为)"
        elif pct > 3 and lr > 1.3:
            detail += " ｜ ✅放量上涨(资金进场)"
        elif -1 < pct < 1 and lr > 1.5:
            detail += " ｜ ⚠️放量滞涨(顶部信号)"

    if turnover:
        detail += f" ｜ 换手{turnover}%"

    return {"verdict": verdict, "lr": lr, "lr_regime": regime, "turnover": turnover, "detail": detail}


def check_volume_price_signal(code: str, snap: dict, hist: dict) -> dict:
    """③+ 量价信号硬规则判断（v0.8新增）。

    三层判断：
    1. 量比+跌幅 → 日线级别大方向（恐慌出货/缩量阴跌/混合）
    2. 分时成交量 → 盘中精确时机（放量下跌/放量反弹/缩量）
    3. 综合信号 → 操作建议

    核心规则（必须记住）：
    - 量比>2 且 跌幅>5% → 恐慌出货 → 清仓
    - 量比<1.2 且 跌幅<4% → 缩量阴跌 → 持有观察
    - 其他情况 → 看分时成交量方向

    Returns:
        {
            ok: bool,
            signal: 'PANIC' | 'NORMAL' | 'MIXED',
            volume_ratio: float,
            change_pct: float,
            minute_signal: 'SELLING' | 'BOUNCE' | 'NEUTRAL',
            action: str,  # 操作建议
            detail: str,  # 详细说明
            must_output: str,  # 强制输出格式
        }
    """
    # 获取跌幅
    change_pct = snap.get("pct") if snap else None
    if change_pct is None and hist and hist.get("ok"):
        change_pct = hist["latest"].get("pct")

    # 获取量比（优先用snap，否则用hist的LR）
    volume_ratio = snap.get("volume_ratio") if snap else None
    if volume_ratio is None and hist and hist.get("ok"):
        # 用LR（量能火控）代替量比：今日量/MA20量
        volume_ratio = hist.get("lr")

    if change_pct is None:
        return {
            "ok": False,
            "signal": "UNKNOWN",
            "detail": "跌幅数据不可用",
        }

    if volume_ratio is None:
        return {
            "ok": False,
            "signal": "UNKNOWN",
            "detail": "量比/LR数据不可用",
        }

    abs_pct = abs(change_pct)

    # === 第一层：量比+跌幅 硬规则 ===
    if volume_ratio > 2.0 and abs_pct > 5.0:
        signal = "PANIC"  # 恐慌出货
        base_action = "立即清仓"
        base_detail = f"量比{volume_ratio}>2 且 跌幅{abs_pct}%>5% → 恐慌出货"
    elif volume_ratio < 1.2 and abs_pct < 4.0:
        signal = "NORMAL"  # 缩量阴跌
        base_action = "持有观察"
        base_detail = f"量比{volume_ratio}<1.2 且 跌幅{abs_pct}%<4% → 缩量阴跌，非恐慌"
    else:
        signal = "MIXED"  # 混合信号，需要看分时
        base_action = "需看分时成交量"
        base_detail = f"量比{volume_ratio}，跌幅{abs_pct}% → 混合信号"

    # === 第二层：分时成交量判断 ===
    minute_signal = "NEUTRAL"
    minute_detail = ""

    try:
        minute_data = dl.get_minute_kline(code, scale=5, datalen=10)
        if minute_data.get("ok") and minute_data.get("klines"):
            klines = minute_data["klines"]
            # 分析最近3-5根K线的量价关系
            recent = klines[-5:] if len(klines) >= 5 else klines

            # 计算下跌量和上涨量
            down_volume = 0
            up_volume = 0
            for k in recent:
                if k["close"] < k["open"]:
                    down_volume += k["volume"]
                else:
                    up_volume += k["volume"]

            total_volume = down_volume + up_volume
            if total_volume > 0:
                down_ratio = down_volume / total_volume
                up_ratio = up_volume / total_volume

                if up_ratio > 0.6:
                    minute_signal = "BOUNCE"
                    minute_detail = f"分时放量反弹(上涨量占{up_ratio*100:.0f}%)"
                    if signal == "PANIC":
                        base_action = "等反弹高点减仓"
                    elif signal == "NORMAL":
                        base_action = "持有，不要卖"
                    else:  # MIXED
                        base_action = "持有，不要卖"
                elif down_ratio > 0.6:
                    minute_signal = "SELLING"
                    minute_detail = f"分时放量下跌(下跌量占{down_ratio*100:.0f}%)"
                    if signal == "PANIC":
                        base_action = "立即清仓"
                    elif signal == "NORMAL":
                        base_action = "减仓1/2"
                    else:  # MIXED
                        base_action = "减仓1/2"
                else:
                    minute_signal = "NEUTRAL"
                    minute_detail = "分时量能均衡"
    except Exception:
        minute_detail = "分时数据获取失败"

    # === 第三层：综合信号 ===
    full_detail = f"{base_detail}。{minute_detail}"

    # 强制输出格式
    vr_status = "✅" if volume_ratio < 2 else "🔴"
    pct_status = "✅" if abs_pct < 5 else "🔴"
    must_output = f"""【量价信号检查】
量比：{volume_ratio}（<2 {vr_status} / >2 🔴）
跌幅：-{abs_pct}%（<5% {pct_status} / >5% 🔴）
分时：{minute_detail}
判断：{signal}（{base_detail}）
建议：{base_action}"""

    return {
        "ok": True,
        "signal": signal,
        "volume_ratio": volume_ratio,
        "change_pct": change_pct,
        "minute_signal": minute_signal,
        "action": base_action,
        "detail": full_detail,
        "must_output": must_output,
    }


def analyze_fund_flow(snap, hist) -> dict:
    """④ 资金动向：主力资金流接口被封，用成交额+换手近似推断。"""
    # 真实资金流接口(stock_individual_fund_flow)被限流，无法获取主力净流入
    # 降级方案：用换手率+涨跌幅+量能组合推断资金态度
    if not hist.get("ok"):
        return {"verdict": "数据不可用", "detail": "日K缺失"}

    pct = snap.get("pct") if snap else hist["latest"].get("pct")
    lr = hist.get("lr")
    turnover = snap.get("turnover") if snap else hist["latest"].get("turnover")

    if pct is None:
        return {"verdict": "数据不足", "detail": "涨跌幅缺失"}

    # 降级推断规则
    if pct > 5 and lr and lr > 1.3:
        verdict = "资金进场(推断)"
        detail = f"大涨{pct}%+放量(LR={lr})，推断主力资金净流入"
    elif pct > 2 and lr and lr > 1.1:
        verdict = "资金偏多(推断)"
        detail = f"上涨{pct}%+温和放量，资金态度偏多"
    elif pct < -5 and lr and lr > 1.3:
        verdict = "资金出逃(推断)"
        detail = f"大跌{pct}%+放量(LR={lr})，推断主力资金净流出/恐慌"
    elif pct < -2 and lr and lr > 1.1:
        verdict = "资金偏空(推断)"
        detail = f"下跌{pct}%+放量，资金态度偏空"
    elif abs(pct) < 1 and lr and lr < 0.8:
        verdict = "资金观望(推断)"
        detail = f"窄幅震荡+缩量，资金观望"
    else:
        verdict = "资金中性(推断)"
        detail = f"涨跌{pct}%，资金态度不明显"

    detail += " ｜ ⚠️资金流接口被限流，以上为基于量价的降级推断，非真实主力数据"

    return {"verdict": verdict, "detail": detail, "_degraded": True}


def analyze_accumulation_distribution(code: str, snap: dict, hist: dict,
                                       intraday_data: dict | None = None,
                                       trend: dict | None = None) -> dict:
    """⑨ 筹码行为分析：判断放量是主力收集还是拉高出货（v0.85新增）。

    五维度综合判断：
    1. 分时买卖盘力量比（tick-level 主动买入/卖出占比）
    2. 5分钟K线上涨量/下跌量比（分钟级别量价配合）
    3. 多日量价结构（日线级别积累/派发模式）
    4. 换手活跃度（换手率 vs 20日均值）
    5. 高位判定（60日区间位置 × 换手）

    Returns:
        {
            ok: bool,
            verdict: str,   # "收集(强)" / "收集" / "派发(强)" / "派发" / "换手(中性)" / "不明确"
            score: int,     # -5(强派发) ~ +5(强收集)
            signals: list,  # 各维度信号描述
            buy_ratio: float | None,   # 主动买入占比
            sell_ratio: float | None,  # 主动卖出占比
            detail: str,
            _degraded: bool,
        }
    """
    signals = []
    score = 0
    buy_ratio = None
    sell_ratio = None
    degraded = False

    # ============================================================
    # 维度1：分时买卖盘力量比（最直接的庄家行为指标）
    # ============================================================
    if intraday_data and intraday_data.get("ok"):
        bv = intraday_data.get("buy_vol", 0)
        sv = intraday_data.get("sell_vol", 0)
        nv = intraday_data.get("neutral_vol", 0)
        total_bs = bv + sv + nv

        if total_bs > 0 and intraday_data.get("has_bs_data"):
            buy_ratio = round(bv / total_bs, 3)
            sell_ratio = round(sv / total_bs, 3)

            if buy_ratio > 0.60:
                score += 2
                signals.append(f"🟢 主动买入占{buy_ratio:.0%}(>60%)，买方主导")
            elif buy_ratio > 0.52:
                score += 1
                signals.append(f"🟢 主动买入占{buy_ratio:.0%}(>52%)，买方偏强")
            elif sell_ratio > 0.60:
                score -= 2
                signals.append(f"🔴 主动卖出占{sell_ratio:.0%}(>60%)，卖方主导")
            elif sell_ratio > 0.52:
                score -= 1
                signals.append(f"🟡 主动卖出占{sell_ratio:.0%}(>52%)，卖方偏强")
            else:
                signals.append(f"⚪ 买卖均衡(买{buy_ratio:.0%}/卖{sell_ratio:.0%})")
        elif total_bs > 0:
            # 有成交量但无买卖分类 → 用 tick 价格方向推断
            ticks = intraday_data.get("ticks", [])
            up_hands, down_hands = 0, 0
            for i in range(1, len(ticks)):
                if ticks[i]["price"] > ticks[i-1]["price"]:
                    up_hands += ticks[i]["hands"]
                elif ticks[i]["price"] < ticks[i-1]["price"]:
                    down_hands += ticks[i]["hands"]
            total_ud = up_hands + down_hands
            if total_ud > 0:
                up_r = up_hands / total_ud
                if up_r > 0.60:
                    score += 1
                    signals.append(f"🟢 tick上行量占{up_r:.0%}(推断买方偏强，无BS分类)")
                elif up_r < 0.40:
                    score -= 1
                    signals.append(f"🔴 tick下行量占{1-up_r:.0%}(推断卖方偏强，无BS分类)")
                else:
                    signals.append(f"⚪ tick方向均衡(上行{up_r:.0%}，无BS分类)")
            degraded = True
        else:
            signals.append("⚪ 分时买卖盘数据为空")
            degraded = True
    else:
        signals.append("⚪ 分时数据不可用(盘后/限流)")
        degraded = True

    # ============================================================
    # 维度2：5分钟K线量价配合（分钟级别量价背离检测）
    # ============================================================
    mk = dl.get_minute_kline(code, scale=5, datalen=20)
    if mk.get("ok") and mk.get("klines"):
        klines = mk["klines"]
        up_vol, down_vol = 0, 0
        up_count, down_count = 0, 0
        recent_spike = False  # 最近5根是否有冲高回落放量

        for i, k in enumerate(klines):
            vol = k.get("volume", 0)
            if k["close"] >= k["open"]:
                up_vol += vol
                up_count += 1
            else:
                down_vol += vol
                down_count += 1

            # 检测冲高回落放量（上影线长 + 收盘偏低 = 典型出货）
            if i >= len(klines) - 5:
                bar_range = k["high"] - k["low"]
                if bar_range > 0:
                    upper_shadow = k["high"] - max(k["open"], k["close"])
                    if (upper_shadow / bar_range > 0.5
                            and k["close"] < (k["high"] + k["low"]) / 2
                            and vol > 0):
                        recent_spike = True

        total_mvol = up_vol + down_vol
        if total_mvol > 0 and (up_count + down_count) > 0:
            up_vol_r = up_vol / total_mvol
            if up_vol_r > 0.60:
                score += 1
                signals.append(f"🟢 5min上涨量占{up_vol_r:.0%}(量价配合)")
            elif up_vol_r < 0.40:
                score -= 1
                signals.append(f"🔴 5min下跌量占{1-up_vol_r:.0%}(下跌放量)")

            if recent_spike:
                score -= 1
                signals.append("🔴 近5根5minK线冲高回落放量(派发特征)")

    # ============================================================
    # 维度3：多日量价结构（日线级别收集/派发模式识别）
    # ============================================================
    if hist.get("ok"):
        closes = hist.get("closes", [])
        volumes = hist.get("volumes", [])

        if len(closes) >= 6 and len(volumes) >= 6:
            recent_n = min(5, len(closes) - 1)
            # 逐日量价关系统计
            up_with_vol, down_with_vol = 0, 0
            vol_rising, vol_falling = 0, 0

            for i in range(-recent_n, 0):
                pct_d = (closes[i] - closes[i-1]) / closes[i-1] if closes[i-1] else 0
                vol_d = (volumes[i] - volumes[i-1]) / volumes[i-1] if volumes[i-1] else 0

                if pct_d > 0.005 and vol_d > 0:
                    up_with_vol += 1  # 放量上涨
                elif pct_d < -0.005 and vol_d > 0:
                    down_with_vol += 1  # 放量下跌
                if vol_d > 0:
                    vol_rising += 1
                else:
                    vol_falling += 1

            # 整体趋势方向
            price_rising = closes[-1] > closes[-recent_n]
            avg_recent_vol = sum(volumes[-recent_n:]) / recent_n
            avg_vol_20 = sum(volumes[-min(20, len(volumes)):]) / min(20, len(volumes))

            if up_with_vol >= 3:
                score += 1
                signals.append(f"🟢 近{recent_n}日{up_with_vol}次放量上涨(积累)")
            elif down_with_vol >= 3:
                score -= 1
                signals.append(f"🔴 近{recent_n}日{down_with_vol}次放量下跌(派发)")
            elif price_rising and vol_falling > vol_rising:
                score -= 1
                signals.append(f"🟡 价涨量缩({vol_falling}日缩量/{vol_rising}日放量)，顶背离迹象")
            elif not price_rising and vol_rising > vol_falling:
                # 价格不涨但放量 → 高位派发特征
                score -= 1
                signals.append(f"🟡 放量但价格不涨({vol_rising}日放量)，滞涨派发迹象")

            # 放量滞涨检测（经典派发信号）
            if avg_vol_20 > 0:
                vol_expand = (avg_recent_vol - avg_vol_20) / avg_vol_20
                price_chg = (closes[-1] - closes[-recent_n]) / closes[-recent_n] if closes[-recent_n] else 0
                if vol_expand > 0.3 and abs(price_chg) < 0.02:
                    score -= 1
                    signals.append(f"🔴 近{recent_n}日放量{vol_expand:.0%}但价格仅变{price_chg:.1%}(放量滞涨=派发)")
                elif vol_expand > 0.1 and price_chg > 0.03:
                    score += 1
                    signals.append(f"🟢 近{recent_n}日放量{vol_expand:.0%}+涨{price_chg:.1%}(量价齐升=收集)")

    # ============================================================
    # 维度4：换手活跃度
    # ============================================================
    turnover = snap.get("turnover") if snap else None
    if turnover is None and hist.get("ok"):
        turnover = hist["latest"].get("turnover")

    if turnover and hist.get("ok"):
        vols = hist.get("volumes", [])
        if len(vols) >= 20:
            avg_vol_20 = sum(vols[-20:]) / 20
            latest_vol = vols[-1] if vols else 0
            if avg_vol_20 > 0:
                vol_ratio = latest_vol / avg_vol_20
                if vol_ratio > 2.0:
                    if turnover > 10:
                        signals.append(f"🔴 换手{turnover}%极高(>{vol_ratio:.1f}x均量)，警惕对倒出货")
                        score -= 1
                    else:
                        signals.append(f"🟡 放量{vol_ratio:.1f}x均量，换手{turnover}%，需结合方向判断")
                elif vol_ratio < 0.5:
                    signals.append(f"⚪ 缩量{vol_ratio:.1f}x均量，换手{turnover}%，观望")

    # ============================================================
    # 维度5：高位判定（60日区间位置）
    # ============================================================
    if hist.get("ok"):
        closes60 = hist.get("closes60", [])
        highs60 = hist.get("highs60", [])
        lows60 = hist.get("lows60", [])
        price = snap.get("price") if snap else None
        if not price and hist.get("ok"):
            price = hist["latest"].get("price")

        if price and highs60 and lows60:
            high60 = max(highs60)
            low60 = min(lows60)
            range60 = high60 - low60
            if range60 > 0:
                position = (price - low60) / range60
                pos_label = "高位" if position > 0.8 else ("中位" if position > 0.5 else "低位")

                if position > 0.8:
                    if turnover and turnover > 8:
                        score -= 1
                        signals.append(f"🔴 60日{pos_label}({position:.0%})+高换手{turnover}%=高位派发风险")
                    else:
                        signals.append(f"🟡 60日{pos_label}({position:.0%})，关注是否放量出货")
                elif position < 0.3:
                    score += 1
                    signals.append(f"🟢 60日{pos_label}({position:.0%})，底部区间利于收集")

    # ============================================================
    # 综合判定
    # ============================================================
    score = max(-5, min(5, score))

    if score >= 3:
        verdict = "收集(强)"
        icon = "🟢🟢"
    elif score >= 1:
        verdict = "收集"
        icon = "🟢"
    elif score <= -3:
        verdict = "派发(强)"
        icon = "🔴🔴"
    elif score <= -1:
        verdict = "派发"
        icon = "🔴"
    elif score == 0 and len(signals) > 0:
        verdict = "换手(中性)"
        icon = "⚪"
    else:
        verdict = "不明确"
        icon = "❓"

    detail_parts = [f"{icon} 筹码行为: {verdict}(评分{score:+d})"]
    for s in signals:
        detail_parts.append(f"  {s}")

    return {
        "ok": True,
        "verdict": verdict,
        "score": score,
        "signals": signals,
        "buy_ratio": buy_ratio,
        "sell_ratio": sell_ratio,
        "detail": "\n".join(detail_parts),
        "_degraded": degraded,
    }


def analyze_relative_strength(snap, code, pool_meta=None) -> dict:
    """⑤ 相对强弱（核心）：个股 vs 大盘 vs 板块 vs 龙头 四象限。"""
    stock_pct = snap.get("pct") if snap else None
    if stock_pct is None:
        return {"verdict": "数据不可用", "detail": "个股涨跌幅缺失"}

    # 大盘：用沪深300
    idx = dl.get_index_daily("sh000300")
    index_pct = idx.get("pct") if idx.get("ok") else None

    # 板块：从新浪板块涨跌里找（用别名映射匹配）
    config_sector = dl.find_sector_of(code, pool_meta)
    sector_name = config_sector  # 显示用配置名
    matched_sector = None
    sector_pct = None
    sb = dl.get_sector_board()
    if sb.get("ok") and config_sector:
        matched_sector = dl.match_sector_in_board(config_sector, sb["sectors"])
        if matched_sector:
            sector_pct = matched_sector.get("pct")
            sector_name = matched_sector.get("name")  # 用实际匹配到的板块名
        else:
            sector_name = config_sector  # 未匹配则保留配置名

    # 计算超额收益
    excess_vs_index = round(stock_pct - index_pct, 2) if index_pct is not None else None
    excess_vs_sector = round(stock_pct - sector_pct, 2) if sector_pct is not None else None

    # 综合判定
    parts = []
    if excess_vs_index is not None:
        if excess_vs_index > 2:
            parts.append("显著强于大盘")
        elif excess_vs_index > 0:
            parts.append("强于大盘")
        elif excess_vs_index < -2:
            parts.append("显著弱于大盘")
        else:
            parts.append("弱于大盘")

    if excess_vs_sector is not None:
        if excess_vs_sector > 2:
            parts.append("领涨板块")
        elif excess_vs_sector > 0:
            parts.append("强于板块")
        elif excess_vs_sector < -2:
            parts.append("板块掉队")
        else:
            parts.append("弱于板块")

    if not parts:
        verdict = "参照数据不全"
        detail = "无法获取大盘或板块涨跌"
    else:
        verdict = "，".join(parts)
        detail = f"个股{stock_pct}%"
        if index_pct is not None:
            detail += f"，大盘{index_pct}%(超额{excess_vs_index}%)"
        if sector_pct is not None:
            detail += f"，板块「{sector_name}」{sector_pct}%(相对{excess_vs_sector}%)"

    # 操作含义
    if excess_vs_index is not None and excess_vs_index < 0 and stock_pct > 0:
        detail += " ｜ ⚠️涨但跑输大盘，属被动跟涨，独立性差"
    if excess_vs_sector is not None and excess_vs_sector < -1:
        detail += " ｜ ⚠️明显弱于板块，可能掉队，不宜追高"

    return {
        "verdict": verdict,
        "comparison": {
            "stock_pct": stock_pct,
            "index_pct": index_pct,
            "excess_vs_index": excess_vs_index,
            "sector_name": sector_name,
            "sector_pct": sector_pct,
            "excess_vs_sector": excess_vs_sector,
        },
        "detail": detail,
    }


def calc_key_levels(price, hist, pool_meta=None) -> dict:
    """⑥ 关键技术位：支撑/压力/止损（v0.85增强）。

    新增：黄金分割回撤位、MA60、布林带上下轨、60日高低、整数关口。
    返回结构化 supports[]/resistances[] 列表 + 兼容旧字段 support/resistance/stop_loss。
    """
    if not hist.get("ok"):
        return {"verdict": "数据不可用"}

    ma5 = hist.get("ma5")
    ma10 = hist.get("ma10")
    ma20 = hist.get("ma20")
    ma60 = hist.get("ma60")
    recent_high20 = hist.get("recent_high20")
    recent_low20 = hist.get("recent_low20")
    p = price if price else hist["latest"]["close"]

    # ---------- 60日高低 ----------
    highs60 = hist.get("highs60", [])
    lows60 = hist.get("lows60", [])
    closes60 = hist.get("closes60", [])
    high60 = max(highs60) if highs60 else None
    low60 = min(lows60) if lows60 else None

    # ---------- 黄金分割回撤位（基于60日高低点） ----------
    fib_levels = []
    if high60 and low60 and high60 > low60:
        diff = high60 - low60
        for ratio in [0.236, 0.382, 0.5, 0.618, 0.786]:
            val = round(high60 - diff * ratio, 2)
            fib_levels.append({"level": val, "label": f"Fib {ratio}"})

    # ---------- 布林带（MA20 ± 2σ） ----------
    boll_upper = None
    boll_lower = None
    if len(closes60) >= 20:
        ma20_slice = closes60[-20:]
        mean20 = sum(ma20_slice) / 20
        variance = sum((c - mean20) ** 2 for c in ma20_slice) / 20
        std20 = variance ** 0.5
        boll_upper = round(mean20 + 2 * std20, 2)
        boll_lower = round(mean20 - 2 * std20, 2)

    # ---------- 整数关口（现价上下各2个） ----------
    round_numbers = []
    if p and p > 0:
        magnitude = 10 ** max(0, len(str(int(p))) - 1)  # 10/100/1000
        if magnitude < 10:
            magnitude = 10
        base = int(p / magnitude) * magnitude
        for offset in [-2, -1, 0, 1, 2]:
            rn = base + offset * magnitude
            if rn > 0 and rn != int(p):
                round_numbers.append(rn)

    # ========== 构建支撑位列表（现价下方） ==========
    supports = []
    # 均线支撑
    for label, val in [("MA5", ma5), ("MA10", ma10), ("MA20", ma20), ("MA60", ma60)]:
        if val and val < p:
            supports.append({"level": val, "label": label, "type": "ma"})
    # 布林带下轨
    if boll_lower and boll_lower < p:
        supports.append({"level": boll_lower, "label": "BOLL下轨", "type": "boll"})
    # 黄金分割（现价下方）
    for f in fib_levels:
        if f["level"] < p:
            supports.append({"level": f["level"], "label": f["label"], "type": "fib"})
    # 20日/60日低点
    if recent_low20 and recent_low20 < p:
        supports.append({"level": recent_low20, "label": "20日低点", "type": "swing"})
    if low60 and low60 < p and low60 != recent_low20:
        supports.append({"level": low60, "label": "60日低点", "type": "swing"})
    # 整数关口（现价下方）
    for rn in round_numbers:
        if rn < p:
            supports.append({"level": rn, "label": f"整数{rn}", "type": "round"})

    # 按价格从高到低排序（最近的支撑排前面）
    supports.sort(key=lambda x: x["level"], reverse=True)
    # 去重（同价位保留type优先级更高的）
    seen_levels = set()
    unique_supports = []
    type_priority = {"ma": 0, "boll": 1, "fib": 2, "swing": 3, "round": 4}
    for s in supports:
        rounded = round(s["level"], 1)  # 0.1元内视为同价位
        if rounded not in seen_levels:
            seen_levels.add(rounded)
            unique_supports.append(s)
    supports = unique_supports[:8]  # 最多保留8层

    # ========== 构建压力位列表（现价上方） ==========
    resistances = []
    for label, val in [("MA5", ma5), ("MA10", ma10), ("MA20", ma20), ("MA60", ma60)]:
        if val and val > p:
            resistances.append({"level": val, "label": label, "type": "ma"})
    if boll_upper and boll_upper > p:
        resistances.append({"level": boll_upper, "label": "BOLL上轨", "type": "boll"})
    for f in fib_levels:
        if f["level"] > p:
            resistances.append({"level": f["level"], "label": f["label"], "type": "fib"})
    if recent_high20 and recent_high20 > p:
        resistances.append({"level": recent_high20, "label": "20日高点", "type": "swing"})
    if high60 and high60 > p and high60 != recent_high20:
        resistances.append({"level": high60, "label": "60日高点", "type": "swing"})
    for rn in round_numbers:
        if rn > p:
            resistances.append({"level": rn, "label": f"整数{rn}", "type": "round"})

    resistances.sort(key=lambda x: x["level"])  # 最近的压力排前面
    seen_levels = set()
    unique_resistances = []
    for r in resistances:
        rounded = round(r["level"], 1)
        if rounded not in seen_levels:
            seen_levels.add(rounded)
            unique_resistances.append(r)
    resistances = unique_resistances[:8]

    # ========== 兼容旧字段 ==========
    support = supports[0]["level"] if supports else None
    resistance = resistances[0]["level"] if resistances else None

    # 止损：优先持仓池配置 → MA20下方2% → 最近支撑下方2%
    # v0.93 新增：止损位合理性校验，防止陈旧数据（除权/拆股后未更新）导致止损位失真
    stop_loss = None
    stop_loss_source = "none"

    if pool_meta and pool_meta.get("stop_loss"):
        pool_sl = pool_meta["stop_loss"]
        # 合理性检查：止损位与现价偏差超过50%视为陈旧数据
        if price and price > 0:
            deviation_pct = abs(pool_sl - price) / price * 100
            if deviation_pct <= 50:
                stop_loss = pool_sl
                stop_loss_source = "pool_meta"
            else:
                # 止损位严重偏离，降级为MA20计算
                print(f"  [WARN] 300476 池子止损位{pool_sl}与现价{price}偏差{deviation_pct:.1f}%，疑似陈旧数据，改用MA20计算")
                if ma20:
                    stop_loss = round(ma20 * 0.98, 2)
                    stop_loss_source = "ma20_fallback"
                elif support:
                    stop_loss = round(support * 0.98, 2)
                    stop_loss_source = "support_fallback"
        else:
            # 无法获取现价，直接使用池子数据（保守）
            stop_loss = pool_sl
            stop_loss_source = "pool_meta_no_price_check"

    if stop_loss is None:
        if ma20:
            stop_loss = round(ma20 * 0.98, 2)
            stop_loss_source = "ma20"
        elif support:
            stop_loss = round(support * 0.98, 2)
            stop_loss_source = "support"

    # ========== 详情文本 ==========
    detail_parts = []
    if supports:
        top_sup = supports[:3]
        detail_parts.append("支撑: " + " / ".join(f"{s['label']}({s['level']})" for s in top_sup))
    if resistances:
        top_res = resistances[:3]
        detail_parts.append("压力: " + " / ".join(f"{r['label']}({r['level']})" for r in top_res))
    if stop_loss:
        source_tag = f"({stop_loss_source})" if stop_loss_source != "pool_meta" else ""
        detail_parts.append(f"止损{stop_loss}{source_tag}")
    if boll_upper and boll_lower:
        detail_parts.append(f"BOLL [{boll_lower}-{boll_upper}]")

    return {
        "support": support,
        "resistance": resistance,
        "stop_loss": stop_loss,
        "stop_loss_source": stop_loss_source,
        "supports": supports,
        "resistances": resistances,
        "fib_levels": fib_levels,
        "boll": {"upper": boll_upper, "lower": boll_lower},
        "range60": {"high": high60, "low": low60},
        "detail": "，".join(detail_parts) if detail_parts else "技术位数据不足",
    }


def calc_trade_prices(hist: dict, levels: dict, trend: dict, lr: float = None, volprice: dict = None, price: float = None) -> dict:
    """回踩/突破策略价格计算（v0.85新增）。

    根据趋势判断(多头=回踩策略, 空头/缠绕=突破策略)输出两套买入方案，
    含价格区间、止损、R:R风险收益比。

    Args:
        hist: get_stock_hist() 返回值
        levels: calc_key_levels() 返回值
        trend: analyze_trend() 返回值
        lr: 当前量能火控值（可选，用于判断量能条件）

    Returns:
        dict: {strategy, plans[], recommendation, rr}
    """
    if not hist.get("ok"):
        return {"ok": False, "strategy": "数据不可用", "plans": []}

    price = hist["latest"]["close"]
    ma5 = hist.get("ma5")
    ma10 = hist.get("ma10")
    ma20 = hist.get("ma20")
    tv = trend.get("verdict", "")
    supports = levels.get("supports", [])
    resistances = levels.get("resistances", [])
    stop_loss_pool = levels.get("stop_loss")

    plans = []

    # v0.90新增：回踩vs破位判定 + 量价异常拦截
    actual_price = price if price else hist["latest"]["close"]
    pb_breakdown = classify_pullback_vs_breakdown(hist, actual_price, lr=lr)

    # v0.90新增：量价异常检查——放量下跌时拦截回踩买入
    volprice_warning = False
    volprice_detail = ""
    if volprice and volprice.get("detail"):
        volprice_detail = volprice.get("detail", "")
        if "跌而放量" in volprice_detail or "恐慌/出货" in volprice_detail:
            volprice_warning = True

    # ====== 方案A：回踩策略（多头排列 / 缠绕偏多） ======
    is_bullish = "多头" in tv
    is_neutral = "缠绕" in tv
    # v0.90新增：破位判定或量价异常时，跳过回踩方案
    if (is_bullish or is_neutral) and pb_breakdown.get("classification") == "BREAKDOWN":
        plans.append({
            "name": "方案A: 回踩买入(已拦截)",
            "strategy": "pullback_blocked",
            "buy_zone": "N/A",
            "buy_target": None,
            "sell_target": None,
            "stop_loss": None,
            "rr": None,
            "lr_condition": "N/A",
            "lr_met": False,
            "lr_current": lr,
            "conditions": [
                f"⚠️破位判定拦截：{pb_breakdown.get('reason', '')}",
                "回踩买入方案已拦截，等待趋势企稳",
            ],
            "blocked": True,
            "block_reason": pb_breakdown.get("reason", "破位信号"),
        })
    elif (is_bullish or is_neutral) and volprice_warning:
        plans.append({
            "name": "方案A: 回踩买入(已拦截)",
            "strategy": "pullback_blocked",
            "buy_zone": "N/A",
            "buy_target": None,
            "sell_target": None,
            "stop_loss": None,
            "rr": None,
            "lr_condition": "N/A",
            "lr_met": False,
            "lr_current": lr,
            "conditions": [
                f"⚠️量价异常拦截：{volprice_detail}",
                "放量下跌信号，回踩买入方案已拦截",
            ],
            "blocked": True,
            "block_reason": f"量价异常：{volprice_detail}",
        })
    elif is_bullish or is_neutral:
        # 买入价：最近的均线支撑（MA5/MA10），给一个小范围
        buy_candidates = []
        for s in supports:
            if s["type"] == "ma" and s["level"] < price:
                buy_candidates.append(s["level"])
        if not buy_candidates and ma10:
            buy_candidates.append(ma10)
        if not buy_candidates and ma20:
            buy_candidates.append(ma20)

        if buy_candidates:
            buy_target = max(buy_candidates)  # 最近的均线支撑
            buy_low = round(buy_target * 0.99, 2)  # 下方1%的容差
            buy_high = round(buy_target * 1.005, 2)  # 上方0.5%

            # 止盈：第一个压力位，且保证R:R≥1.2
            sell_target = None
            for r in resistances:
                risk = buy_target - (stop_loss_pool or buy_target * 0.97)
                if risk > 0 and (r["level"] - buy_target) / risk >= 1.2:
                    sell_target = r["level"]
                    break
            if sell_target is None and resistances:
                sell_target = resistances[0]["level"]
            if sell_target is None:
                sell_target = round(buy_target * 1.10, 2)  # 兜底10%

            # 止损
            stop = stop_loss_pool
            if stop is None:
                # 用次一级支撑下方2%
                next_supports = [s["level"] for s in supports if s["level"] < buy_target]
                if next_supports:
                    stop = round(max(next_supports) * 0.98, 2)
                else:
                    stop = round(buy_target * 0.97, 2)  # 买入价下方3%

            # R:R
            risk = buy_target - stop if stop else buy_target * 0.03
            reward = sell_target - buy_target if sell_target else buy_target * 0.10
            rr = round(reward / risk, 2) if risk > 0 else None

            # LR条件（回踩建仓 LR≥0.8）
            lr_condition = "回踩日缩量(LR<0.8)+买入日放量(LR≥0.8)"
            lr_met = lr is not None and lr >= 0.8

            plans.append({
                "name": "方案A: 回踩买入",
                "strategy": "pullback",
                "buy_zone": f"{buy_low}-{buy_high}",
                "buy_target": buy_target,
                "sell_target": sell_target,
                "stop_loss": stop,
                "rr": rr,
                "lr_condition": lr_condition,
                "lr_met": lr_met,
                "lr_current": lr,
                "conditions": [
                    f"价格回踩{buy_target}附近(MA支撑)",
                    f"回踩日缩量(LR<0.8)+买入日放量(LR≥0.8)",
                    f"composite_shock≤2",
                    f"当日涨>5%不追/高开>3%不追",
                ],
            })

    # ====== 方案B：突破策略（任何趋势均可） ======
    if ma5 and ma10:
        # 突破确认价：MA5×1.01（站上MA5+1%确认突破）
        break_price = round(ma5 * 1.01, 2)

        # 止损：MA5下方2% 或 最近支撑下方2%
        stop_b = round(ma5 * 0.98, 2)
        if supports:
            nearest_below = [s["level"] for s in supports if s["level"] < break_price]
            if nearest_below:
                alt_stop = round(max(nearest_below) * 0.98, 2)
                stop_b = max(stop_b, alt_stop)

        # 止盈：保证R:R≥1.5
        risk_b = break_price - stop_b
        min_reward_b = risk_b * 1.5
        sell_b = round(break_price + min_reward_b, 2)
        # 尝试用压力位
        for r in resistances:
            if r["level"] > break_price and (r["level"] - break_price) / risk_b >= 1.5:
                sell_b = r["level"]
                break

        rr_b = round((sell_b - break_price) / risk_b, 2) if risk_b > 0 else None

        lr_condition_b = "突破日放量(LR≥1.2)"
        lr_met_b = lr is not None and lr >= 1.2

        plans.append({
            "name": "方案B: 突破买入",
            "strategy": "breakout",
            "buy_zone": f"≥{break_price}",
            "buy_target": break_price,
            "sell_target": sell_b,
            "stop_loss": stop_b,
            "rr": rr_b,
            "lr_condition": lr_condition_b,
            "lr_met": lr_met_b,
            "lr_current": lr,
            "conditions": [
                f"放量突破{break_price}(MA5+1%)",
                f"突破日LR≥1.2(丰水期)",
                f"composite_shock≤2",
                f"当日涨>5%不追(突破日除外)",
            ],
        })

    # ====== 推荐哪个方案 ======
    # v0.90新增：乖离率检查影响推荐
    bias_info = trend.get("bias", {})
    bias_risk = bias_info.get("risk", "NORMAL") if bias_info.get("ok") else "NORMAL"

    recommendation = "观望，暂无合适方案"
    if plans:
        # v0.90新增：极端过热时禁止推荐买入
        if bias_risk == "EXTREME_OVERHEAT":
            recommendation = f"⚠️极端过热(乖离{bias_info.get('max_bias', 0):+.1f}%)，禁止开新仓，持仓者考虑减仓"
        elif bias_risk == "OVERHEAT":
            non_blocked = [p for p in plans if not p.get("blocked")]
            if non_blocked:
                recommendation = f"⚠️过热(乖离{bias_info.get('max_bias', 0):+.1f}%)，仅限减仓后观察，不新增仓位"
            else:
                recommendation = f"⚠️过热+{plans[0].get('block_reason', '信号异常')}，观望"
        elif is_bullish:
            non_blocked = [p for p in plans if not p.get("blocked")]
            if non_blocked:
                recommendation = f"推荐{non_blocked[0]['name']}(多头排列优先回踩)"
            elif plans:
                recommendation = f"⚠️回踩方案被拦截：{plans[0].get('block_reason', '')}，观望"
        else:
            breakout = [p for p in plans if p["strategy"] == "breakout"]
            if breakout:
                recommendation = f"推荐{breakout[0]['name']}(非多头排列等突破确认)"
            else:
                recommendation = f"推荐{plans[0]['name']}"

    return {
        "ok": True,
        "strategy": "回踩" if is_bullish else ("回踩/突破均可" if is_neutral else "突破"),
        "trend_verdict": tv,
        "plans": plans,
        "recommendation": recommendation,
        "pullback_vs_breakdown": pb_breakdown,
        "bias_risk": bias_risk,
    }


def analyze_sector_sync(code, pool_meta=None) -> dict:
    """⑦ 板块联动：所属板块整体涨跌、是否共振。"""
    config_sector = dl.find_sector_of(code, pool_meta)
    sb = dl.get_sector_board()
    if not sb.get("ok"):
        return {"verdict": "板块数据不可用", "detail": ""}

    if not config_sector:
        return {"verdict": "板块归属未知", "detail": "个股所属板块未配置(见auto_target_pool.json的sector字段)，无法判断板块联动"}

    # 用别名映射匹配板块
    matched = dl.match_sector_in_board(config_sector, sb["sectors"])
    total = len(sb["sectors"])
    if not matched:
        return {"verdict": "板块未匹配", "detail": f"板块「{config_sector}」在新浪板块表里未找到匹配，可在data_layer.py的SECTOR_ALIASES补充映射"}

    sector_name = matched.get("name", config_sector)
    sector_pct = matched.get("pct")
    # 计算排名
    rank = None
    for i, s in enumerate(sb["sectors"], 1):
        if s.get("name") == sector_name:
            rank = i
            break

    # 板块强弱判定
    if rank and total:
        if rank <= total * 0.2:
            verdict = "板块强势(领涨)"
            detail = f"板块「{sector_name}」{sector_pct}%，排名{rank}/{total}，属领涨板块"
        elif rank >= total * 0.8:
            verdict = "板块弱势(领跌)"
            detail = f"板块「{sector_name}」{sector_pct}%，排名{rank}/{total}，属领跌板块"
        else:
            verdict = "板块中性"
            detail = f"板块「{sector_name}」{sector_pct}%，排名{rank}/{total}"

    return {"verdict": verdict, "detail": detail, "sector": sector_name, "sector_pct": sector_pct, "rank": rank}


def synthesize_advice(trend, intraday, volprice, fundflow, rs, levels, sector_sync, price, pool_meta=None, deviation=None, recovery=None, acc_dist=None) -> dict:
    """⑧ 综合操作建议：把前7维 + 偏离度 + 筹码行为加权合成最终动作。"""
    score = 5  # 基准分5/10
    reasons = []

    # 趋势加分/减分（权重最高）
    tv = trend.get("verdict", "")
    if "多头" in tv and "强" in tv:
        score += 2
        reasons.append("趋势多头")
    elif "多头" in tv:
        score += 1
        reasons.append("趋势偏多")
    elif "空头" in tv and "强" in tv:
        score -= 3
        reasons.append("趋势强空头")
    elif "空头" in tv:
        score -= 2
        reasons.append("趋势偏空")

    # 相对强弱
    rv = rs.get("verdict", "")
    if "显著强于大盘" in rv or "领涨板块" in rv:
        score += 1
        reasons.append("相对强势")
    elif "显著弱于大盘" in rv or "掉队" in rv:
        score -= 1
        reasons.append("相对弱势")

    # 量价
    vv = volprice.get("verdict", "")
    if "放量" in vv and "冰冻" not in vv and "枯水" not in vv:
        score += 1
        reasons.append("量能配合")
    elif "冰冻" in vv or "枯水" in vv:
        score -= 1
        reasons.append("量能不足")
    if "顶背离" in volprice.get("detail", "") or "放量滞涨" in volprice.get("detail", ""):
        score -= 1
        reasons.append("量价背离")
    # v0.90新增：跌而放量(恐慌/出货)减分——修复架构断层
    if "跌而放量" in volprice.get("detail", "") or "恐慌/出货" in volprice.get("detail", ""):
        score -= 2
        reasons.append("跌而放量(出货信号)")

    # 分时
    if intraday.get("available"):
        iv = intraday.get("verdict", "")
        if "站稳分时线" in iv or "偏强" in iv:
            score += 1
            reasons.append("分时偏强")
        elif "跌破分时线" in iv or "偏弱" in iv:
            score -= 1
            reasons.append("分时偏弱")

    # 板块
    sv = sector_sync.get("verdict", "")
    if "板块强势" in sv:
        score += 1
        reasons.append("板块联动向好")
    elif "板块弱势" in sv:
        score -= 1
        reasons.append("板块走弱")

    # 偏离度（第 9 维）：过热扣分、滞涨加分（需结合板块强弱）
    if deviation and deviation.get("ok"):
        dev_status = deviation.get("status", "")
        if dev_status == "OVERHEAT":
            score -= 2
            reasons.append(f"个股领涨板块{deviation.get('deviation','')}%，过热见顶风险")
        elif dev_status == "WEAK":
            score -= 1
            reasons.append(f"个股独立走弱{deviation.get('deviation','')}%，破位风险")
        elif dev_status == "LAGGING":
            # 滞涨的解读取决于板块强弱
            if "板块强势" in sv:
                score += 1
                reasons.append("滞涨但板块强势，补涨候选")
            elif "板块弱势" in sv:
                score -= 1
                reasons.append("滞涨且板块弱势，独立走弱前兆")

    # 暴跌修复率（第 6 个健康度指标，v0.85新增）
    if recovery and recovery.get("health_score") is not None:
        rh = recovery["health_score"]
        score += rh
        rv_txt = recovery.get("verdict", "")
        if rh >= 2:
            reasons.append(f"暴跌已修复({rv_txt})")
        elif rh == 1:
            reasons.append(f"暴跌修复中({rv_txt})")
        else:
            reasons.append(f"暴跌未修复({rv_txt})")

    # 筹码行为分析（v0.85新增：收集 vs 派发）
    # v0.86修复：派发惩罚加重+硬规则禁止派发时建议买入
    chip_distribution_detected = False
    if acc_dist and acc_dist.get("ok"):
        ad_score = acc_dist.get("score", 0)
        ad_verdict = acc_dist.get("verdict", "")
        if ad_score >= 2:
            score += 1
            reasons.append(f"筹码收集({ad_verdict})")
        elif ad_score <= -1:  # v0.86: 从<=-2改为<=-1，匹配"派发"判定条件
            score -= 2  # v0.86: 惩罚从-1增加到-2
            reasons.append(f"筹码派发({ad_verdict})，主力出货信号")
            chip_distribution_detected = True

    # 月历板块偏好加分（第二批新增：个股所属板块属于当月偏好板块则加分）
    try:
        import monthly_regime
        regime = monthly_regime.get_today_regime()
        sector_name = sector_sync.get("sector") or ""
        if sector_name and monthly_regime.is_sector_favored(sector_name, regime):
            score += 1
            reasons.append(f"当月偏好板块({sector_name})")
    except Exception:
        pass

    # 限定范围
    score = max(1, min(10, score))

    # 动作映射
    lv = levels
    if score >= 8:
        action = "加仓/买入"
    elif score >= 6:
        action = "持有/回踩可加仓"
    elif score >= 4:
        action = "持有/观望"
    elif score >= 2:
        action = "减仓/不追"
    else:
        action = "清仓/止损"

    # v0.86硬规则：筹码派发时禁止建议买入，最高只能"持有/观望"
    if chip_distribution_detected:
        if action in ["加仓/买入", "持有/回踩可加仓"]:
            action = "持有/观望（筹码派发中，禁止加仓）"

    return {
        "action": action,
        "entry_price": f"{lv.get('support')}-{lv.get('support',0)*1.01:.2f}" if lv.get("support") else None,
        "add_price": lv.get("support"),
        "reduce_price": lv.get("resistance"),
        "stop_loss": lv.get("stop_loss"),
        "reason": "，".join(reasons) if reasons else "各维度信号中性",
        "score": score,
    }


# =========================================================
# 主诊断入口
# =========================================================
def diagnose(code: str, pool_meta: dict | None = None) -> dict:
    """对单只股票执行完整8维诊断。

    Args:
        code: 股票代码（6位数字）
        pool_meta: 可选，来自 auto_target_pool.json 的标的元信息（含 sector/stop_loss 等）。
                   若未传，会自动从 auto_target_pool.json 查找匹配项。

    Returns:
        完整诊断 dict（结构见 md_renderer.render_diagnosis）
    """
    code = dl._clean_code(code)
    diag_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_gaps = []

    # 单股模式：若未传 pool_meta，自动从持仓池查（用于补 sector/stop_loss）
    if pool_meta is None:
        pool_meta = _lookup_pool_meta(code)

    # 拉数据
    snap = dl.get_stock_realtime(code)
    hist = dl.get_stock_hist(code, 120)

    if not snap.get("ok") and not hist.get("ok"):
        return {"ok": False, "code": code, "error": "实时行情和日K均获取失败，无法诊断"}

    price = snap.get("price")
    name = snap.get("name") or (pool_meta.get("name") if pool_meta else "") or ""

    # 8 维诊断
    trend = analyze_trend(price, hist)
    intraday = analyze_intraday(code)
    volprice = analyze_volume_price(snap if snap.get("ok") else None, hist)
    fundflow = analyze_fund_flow(snap if snap.get("ok") else None, hist)
    rs = analyze_relative_strength(snap if snap.get("ok") else None, code, pool_meta)
    levels = calc_key_levels(price, hist, pool_meta)
    sector_sync = analyze_sector_sync(code, pool_meta)

    # 第 8.5 维：筹码行为分析（v0.85新增：判断放量是收集还是出货）
    intraday_raw = dl.get_intraday(code)  # 原始分时数据（含买卖盘性质）
    acc_dist = analyze_accumulation_distribution(
        code,
        snap if snap.get("ok") else None,
        hist,
        intraday_data=intraday_raw if intraday_raw.get("ok") else None,
        trend=trend,
    )

    # 第 9 维：个股-板块偏离度检测（Top-Down 补充）
    deviation = {}
    try:
        import stock_sector_deviation as ssd_mod
        deviation = ssd_mod.diagnose_deviation(code, pool_meta.get("sector") if pool_meta else None)
    except Exception:
        deviation = {"ok": False, "error": "偏离度检测模块加载失败"}

    # 第 10 维：量价信号硬规则判断（v0.8新增：区分恐慌出货/缩量阴跌）
    vp_signal = check_volume_price_signal(
        code,
        snap if snap.get("ok") else None,
        hist
    )

    # 第 10.5 维：暴跌修复率（v0.85新增：距近20日低点的修复程度）
    recovery = calc_recovery_rate(hist)

    advice = synthesize_advice(trend, intraday, volprice, fundflow, rs, levels, sector_sync, price, pool_meta, deviation=deviation, recovery=recovery, acc_dist=acc_dist)

    # 第 11.5 维：交易价格计算（v0.85新增：回踩/突破策略+R:R）
    trade_prices = calc_trade_prices(hist, levels, trend, lr=hist.get("lr"), volprice=volprice, price=price)

    # 第 12 维：交易纪律检查（v0.8新增：卖出理由审计+仓位铁律+止损位检查）
    discipline = trading_discipline.check_sell_discipline(
        action=advice.get("action", ""),
        price=price,
        stop_loss=levels.get("stop_loss"),
        prev_close=snap.get("prev_close") if snap else None,
        market_risk=False,  # 需要外部传入（如美债破5%）
        logic_invalidated=False,  # 需要外部传入
    )
    # 如果纪律检查不通过，修改建议
    if not discipline.get("ok"):
        modified_action = trading_discipline.integrate_with_advice(
            advice.get("action", ""),
            discipline
        )
        advice["action"] = modified_action
        advice["discipline_warning"] = True

    # 记录数据缺口
    if not snap.get("ok") or snap.get("source") == "daily_close_fallback":
        data_gaps.append("实时行情不可用，使用上一交易日收盘价，盘中请以实际盘面为准")
    if fundflow.get("_degraded"):
        data_gaps.append("资金流接口被限流，资金动向为基于量价的降级推断")
    if not intraday.get("available"):
        data_gaps.append("分时数据不可用（盘后或接口被限流），分时形态维度缺失")
    if not rs.get("comparison", {}).get("sector_pct"):
        data_gaps.append("个股所属板块未配置或板块表未匹配，相对板块强弱缺失（请在auto_target_pool.json补充sector字段）")
    if acc_dist.get("_degraded"):
        data_gaps.append("筹码行为分析部分降级(分时买卖盘分类不可用，使用tick方向推断)")

    return {
        "ok": True,
        "code": code,
        "name": name,
        "diag_time": diag_time,
        "data_source": snap.get("source", ""),
        "snapshot": snap,
        "trend": trend,
        "intraday": intraday,
        "volume_price": volprice,
        "volume_price_signal": vp_signal,  # v0.8新增：量价信号硬规则
        "trading_discipline": discipline,  # v0.8新增：交易纪律检查
        "fund_flow": fundflow,
        "relative_strength": rs,
        "levels": levels,
        "sector_sync": sector_sync,
        "accumulate_distribution": acc_dist,  # v0.85新增：筹码收集/派发分析
        "deviation": deviation,
        "recovery": recovery,  # v0.85新增：暴跌修复率
        "trade_prices": trade_prices,  # v0.85新增：回踩/突破策略价格
        "advice": advice,
        "data_gaps": data_gaps,
    }


def _lookup_pool_meta(code: str) -> dict | None:
    """从 auto_target_pool.json 查找某代码的元信息（sector/stop_loss 等）。"""
    pool_path = DATABASE_DIR / "auto_target_pool.json"
    if not pool_path.exists():
        return None
    try:
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        for item in pool:
            if dl._clean_code(item.get("ticker", "")) == code:
                return item
    except Exception:
        return None
    return None


def resolve_code(user_input: str) -> tuple[str, str]:
    """把用户输入解析为 (代码, 名称)。支持三种输入：

    - 纯数字代码："300502" → ("300502", "新易盛")
    - 带前缀代码："sz300502" → ("300502", "新易盛")
    - 中文名称："新易盛" → ("300502", "新易盛")  （从全市场行情反查）

    返回 (code, name)。查不到返回 ("", "")。
    """
    s = (user_input or "").strip()
    if not s:
        return "", ""

    # 1) 纯数字或带sz/sh前缀 → 直接当代码
    digits = dl._clean_code(s)
    if digits and digits == s.replace("sh", "").replace("sz", "").replace("SH", "").replace("SZ", ""):
        # 是代码，反查名称
        all_q = dl.get_realtime_quotes()
        if all_q.get("ok") and digits in all_q["quotes"]:
            return digits, all_q["quotes"][digits].get("name", "")
        # 持仓池里找名称
        meta = _lookup_pool_meta(digits)
        return digits, (meta.get("name", "") if meta else "")

    # 2) 中文名称 → 从全市场行情反查代码
    all_q = dl.get_realtime_quotes()
    if all_q.get("ok"):
        for code, q in all_q["quotes"].items():
            name = q.get("name", "")
            if name and (name == s or s in name or name in s):
                return dl._clean_code(code), name

    # 3) 持仓池里按名称找
    pool_path = DATABASE_DIR / "auto_target_pool.json"
    if pool_path.exists():
        try:
            pool = json.loads(pool_path.read_text(encoding="utf-8"))
            for item in pool:
                if item.get("name", "") == s or s in item.get("name", ""):
                    return dl._clean_code(item.get("ticker", "")), item.get("name", "")
        except Exception:
            pass

    return "", ""


def diagnose_pool() -> list[dict]:
    """诊断 auto_target_pool.json 里全部标的。"""
    pool_path = DATABASE_DIR / "auto_target_pool.json"
    if not pool_path.exists():
        return []
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    results = []
    for item in pool:
        code = item.get("ticker", "")
        if not code:
            continue
        try:
            r = diagnose(code, pool_meta=item)
            results.append(r)
        except Exception as e:
            results.append({"ok": False, "code": code, "error": f"{type(e).__name__}: {e}"})
    return results


# =========================================================
# 命令行入口
# =========================================================
def main():
    parser = argparse.ArgumentParser(description="盘中个股8维快速诊断")
    parser.add_argument("code", nargs="?", default="", help="股票代码或名称，如 300502 或 新易盛")
    parser.add_argument("--pool", action="store_true", help="诊断 auto_target_pool.json 全部标的")
    parser.add_argument("--push", action="store_true", help="诊断结果推送到飞书")
    parser.add_argument("--save", action="store_true", help="保存诊断报告到 database/")
    args = parser.parse_args()

    if args.pool:
        # 池模式
        print("=" * 60)
        print("🚀 持仓池自动巡航诊断")
        print("=" * 60)
        results = diagnose_pool()
        if not results:
            print("持仓池为空或文件不存在")
            return

        # 汇总
        summary = md_renderer.render_pool_summary(results)
        print("\n" + summary)

        # 各股明细
        for r in results:
            if r.get("ok"):
                print("\n" + "=" * 60)
                print(md_renderer.render_diagnosis(r))

        if args.push:
            import feishu_pusher
            feishu_pusher.send_md(f"持仓池诊断汇总 {datetime.now().strftime('%m-%d %H:%M')}", summary)
        return

    if not args.code:
        parser.print_help()
        print('\n示例：\n  python stock_diagoser.py 300502        # 按代码\n  python stock_diagoser.py 新易盛         # 按名称\n  python stock_diagoser.py 新易盛 --push  # 诊断+推送飞书\n  python stock_diagoser.py --pool          # 诊断全部持仓池')
        return

    # 解析输入：支持代码(300502)或名称(新易盛)
    code, name = resolve_code(args.code)
    if not code:
        print(f"❌ 无法识别「{args.code}」，请输入6位代码或股票名称")
        return
    display = f"{name}({code})" if name else code

    # 单股模式
    print(f"🔍 正在诊断 {display} ...")
    result = diagnose(code)
    if not result.get("ok"):
        print(f"❌ 诊断失败：{result.get('error')}")
        return

    md = md_renderer.render_diagnosis(result)
    print("\n" + md)

    if args.save:
        today = datetime.now().strftime("%Y-%m-%d")
        out = DATABASE_DIR / f"diagnosis_{code}_{today}.md"
        out.write_text(md, encoding="utf-8")
        print(f"\n💾 已保存：{out}")

    if args.push:
        import feishu_pusher
        name = result.get("name", "") or name
        feishu_pusher.send_md(f"{name}({code}) 诊断 {datetime.now().strftime('%H:%M')}", md)
        print("\n📤 已推送到飞书")


if __name__ == "__main__":
    main()
