# -*- coding: utf-8 -*-
"""trading_discipline.py — 交易纪律检查模块（重建版）
接口签名按 stock_diagoser 调用点还原：
  check_sell_discipline(action, price, stop_loss, prev_close, market_risk, logic_invalidated) -> {"ok": bool, ...}
  integrate_with_advice(action, discipline) -> str
规则来自 STRATEGY_DEPOSIT / 交易卡片三问：
  卖出理由审计（允许/禁止清单）、仓位铁律、止损位检查。
"""
LIMITS = {
    "single_stock_max_pct": 20,   # 单只 <=20%
    "sector_max_pct": 40,         # 单板块 <=40%
    "single_trade_max_pct": 50,   # 单次 <=50% 剩余仓位
}

ALLOWED_SELL_REASONS = ["止损", "破位", "基本面恶化", "达到目标价", "仓位再平衡", "更好机会换仓"]
FORBIDDEN_SELL_REASONS = ["跌了怕", "烦了", "别人都卖", "感觉不好"]


def check_sell_discipline(action="", price=None, stop_loss=None,
                          prev_close=None, market_risk=False,
                          logic_invalidated=False):
    """卖出/减仓动作的纪律审计。返回 ok=True 表示该动作合规。
    规则：止损位被跌破 => 必须卖（ok=True 且 reason=止损）；
          无止损参照、非破位、非基本面 => 提示需补充交易卡片。"""
    res = {"ok": True, "checks": [], "reason": None, "action": "pass"}
    if price is None:
        res["checks"].append("无价格数据，跳过纪律检查")
        return res
    # 1) 止损检查：跌破止损 => 允许且必须
    if stop_loss is not None and price is not None and float(price) <= float(stop_loss):
        res["checks"].append("价格 %s 已跌破止损 %s => 强制卖出合规" % (price, stop_loss))
        res["reason"] = "止损"
        res["action"] = "must_sell"
        return res
    # 2) 无止损且要卖 => 需说明理由（提示，不阻断）
    if stop_loss is None:
        res["checks"].append("⚠️ 无止损位记录，卖出前必须补交易卡片（为什么买/拿多久/止损位）")
    # 3) 逻辑失效（买入理由消失）
    if logic_invalidated:
        res["checks"].append("买入逻辑已失效 => 卖出合规")
        res["reason"] = "基本面恶化"
        return res
    # 4) 市场系统性风险
    if market_risk:
        res["checks"].append("市场系统性风险(如美债破5%) => 允许防御性减仓")
        res["reason"] = "系统性风险"
        return res
    # 5) 默认：持有中的普通减仓，检查情绪状态提示
    res["checks"].append("普通减仓：请对照交易卡片三问与情绪熔断状态")
    return res


def integrate_with_advice(action, discipline):
    """纪律检查不通过时修正操作建议文案"""
    checks = (discipline or {}).get("checks") or []
    note = checks[0] if checks else "纪律检查未通过"
    if not action:
        return "【纪律修正】%s" % note
    return "%s（纪律提示：%s）" % (action, note)


def check_position_limits(single_pct=None, sector_pct=None, trade_pct=None):
    """仓位合规检查（交易卡片之仓位铁律）"""
    problems = []
    if single_pct is not None and single_pct > LIMITS["single_stock_max_pct"]:
        problems.append("单只 %.0f%% 超上限 %d%%" % (single_pct, LIMITS["single_stock_max_pct"]))
    if sector_pct is not None and sector_pct > LIMITS["sector_max_pct"]:
        problems.append("板块 %.0f%% 超上限 %d%%" % (sector_pct, LIMITS["sector_max_pct"]))
    if trade_pct is not None and trade_pct > LIMITS["single_trade_max_pct"]:
        problems.append("单次 %.0f%% 超上限 %d%%" % (trade_pct, LIMITS["single_trade_max_pct"]))
    return {"ok": not problems, "problems": problems}
