"""P13-R: research-only recommendation engine over the P13-O/P13-Q layer.

Consumes the P13-O audit JSON (no production rerun). Calibrators are fitted
on discovery OOS rows only (< 2025-01-01) and evaluated on validation OOS
rows (>= 2025-01-01) - the same a priori boundary as P13-P/P13-Q. The eight
decision policies are fixed in docs/P13R_RESEARCH_PLAN.md BEFORE any window
result was inspected; nothing here may add, drop or re-tune a policy.

Everything is research: packets carry no order intent, no production path is
touched, and no policy may be described as validated for production use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_p13o_analysis import RegimeLabeler, _md_table, _write
from scripts.run_p13q_analysis import (
    SEED,
    BOOTSTRAP_ROUNDS,
    SPLIT_DATE,
    brier,
    ece,
    fit_isotonic,
    fit_platt,
    log_loss,
)


def accuracy(ps, ys):
    ps = np.asarray(ps, dtype=float)
    ys = np.asarray(ys, dtype=float)
    if ps.size == 0:
        return float("nan")
    return float(np.mean((ps >= 0.5) == (ys == 1)))

COST_SCENARIOS = {
    "zero": {"commission_bp": 0.0, "slippage_bp": 0.0},
    "low": {"commission_bp": 5.0, "slippage_bp": 5.0},
    "medium": {"commission_bp": 10.0, "slippage_bp": 10.0},
}
HISTORY_WINDOW = 60
WINSOR_QUANTILES = (0.01, 0.99)
MAX_PER_INDUSTRY = 2
TOP_K = 3
PERCENTILE = 0.80
ER_THRESHOLD = 0.0
POLICY_IDS = (
    "hold_all", "threshold_raw_p50", "threshold_platt_p50",
    "threshold_iso_p50", "topk_platt_k3", "percentile_platt_p80",
    "er_platt_0", "er_platt_pos_risk",
)


# --------------------------------------------------------------------------
# PIT-safe rolling expected-return / risk features
# --------------------------------------------------------------------------

def _winsorize(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    lo, hi = np.quantile(values, WINSOR_QUANTILES[0]), np.quantile(values, WINSOR_QUANTILES[1])
    return np.clip(values, lo, hi)


def _date_to_decision_time(date_str: str) -> str:
    return f"{date_str}T16:00:00+08:00"


def rolling_features(audit):
    """Per-row PIT expected-return/risk features from earlier completed rows.

    A past row (decision day d, next_return) only becomes public at d+1's
    close, so a candidate at day t may use rows whose decision date is
    strictly before t. Window = last HISTORY_WINDOW such returns,
    winsorized at the fixed 1%/99% quantiles; fewer than 10 rows falls back
    to the discovery-wide pooled statistics (computed once).
    """
    by_symbol = defaultdict(list)
    for symbol, per_day in audit["factors"].items():
        for decision_time, entry in per_day.items():
            nr = entry.get("next_return")
            if nr is not None and nr == nr:
                by_symbol[symbol].append((decision_time[:10], float(nr)))
    for symbol in by_symbol:
        by_symbol[symbol].sort(key=lambda item: item[0])

    # Discovery rows only: for any validation-row candidate the whole
    # discovery window lies in its past, so the fallback stays PIT-safe.
    pooled = _winsorize(np.array(
        [nr for rows in by_symbol.values() for date_str, nr in rows
         if date_str < SPLIT_DATE], dtype=float
    ))
    if pooled.size == 0:
        pooled = np.array([0.0])
    pooled_pos, pooled_neg = pooled[pooled > 0], pooled[pooled < 0]
    fallback = {
        "upside": float(pooled_pos.mean()) if pooled_pos.size else 0.0,
        "downside": float(pooled_neg.mean()) if pooled_neg.size else 0.0,
        "volatility": float(pooled.std()) if pooled.size else 0.02,
        "downside_deviation": float(pooled_neg.std()) if pooled_neg.size else 0.0,
        "max_drawdown": 0.0,
    }

    features: dict[tuple[str, str], dict] = {}
    for symbol, rows in by_symbol.items():
        past: list[float] = []
        for date_str, nr in rows:
            if len(past) >= 10:
                window = _winsorize(np.array(past[-HISTORY_WINDOW:]))
                pos, neg = window[window > 0], window[window < 0]
                curve = np.cumprod(1.0 + window)
                peak = np.maximum.accumulate(np.concatenate([[1.0], curve]))[1:]
                features[(symbol, _date_to_decision_time(date_str))] = {
                    "upside": float(pos.mean()) if pos.size else 0.0,
                    "downside": float(neg.mean()) if neg.size else 0.0,
                    "volatility": float(window.std()),
                    "downside_deviation": float(neg.std()) if neg.size else 0.0,
                    "max_drawdown": float((curve / peak - 1.0).min()),
                }
            else:
                features[(symbol, _date_to_decision_time(date_str))] = dict(fallback)
            past.append(nr)
    return features


# --------------------------------------------------------------------------
# policy evaluation
# --------------------------------------------------------------------------

def apply_policy(policy: dict, rows: list[dict]) -> list[dict]:
    """Select rows for one policy, then apply the shared constraints.

    rows must carry: symbol, decision_time, industry, p_raw, p_platt,
    p_iso, expected_return, volatility. Selection happens per decision day
    in deterministic (symbol, decision_time) order; the industry cap is
    applied after the family-specific rule, keeping the first candidates in
    that same deterministic order.
    """
    rule = policy["selection_rule"]
    cal = policy["calibration_method"]
    prob_key = {"raw": "p", "platt": "p_platt", "isotonic": "p_iso",
                "none": "p"}[cal]
    selected = []
    by_day = defaultdict(list)
    for row in rows:
        by_day[row["decision_time"]].append(row)
    for day in sorted(by_day):
        day_rows = sorted(by_day[day], key=lambda r: (r["symbol"], r["decision_time"]))
        if rule == "hold_all":
            picks = list(day_rows)
        elif rule == "threshold":
            picks = [r for r in day_rows if r[prob_key] >= policy["probability_threshold"]]
        elif rule == "top_k":
            ranked = sorted(day_rows, key=lambda r: (-r[prob_key], r["symbol"]))
            picks = ranked[: policy["top_k"]]
        elif rule == "percentile":
            values = np.array([r[prob_key] for r in day_rows])
            cut = np.quantile(values, policy["percentile"])
            picks = [r for r in day_rows if r[prob_key] >= cut]
        elif rule == "expected_return":
            picks = [
                r for r in day_rows
                if r["expected_return"] > policy["expected_return_threshold"]
                and (policy.get("risk_filter") is None
                     or r["volatility"] <= policy["risk_filter"])
            ]
        else:
            raise ValueError(f"unknown selection rule: {rule}")
        industry_count = defaultdict(int)
        for row in picks:
            code = row.get("industry")
            if code is None or industry_count[code] < MAX_PER_INDUSTRY:
                selected.append(row)
                if code is not None:
                    industry_count[code] += 1
    return selected


def turnover_ratio(selected: list[dict]) -> float:
    """Mean per-day membership change relative to the current book size."""
    by_day = defaultdict(set)
    for row in selected:
        by_day[row["decision_time"]].add(row["symbol"])
    days = sorted(by_day)
    if len(days) < 2:
        return 0.0
    changes, total = 0, 0
    previous = set()
    for day in days:
        current = by_day[day]
        changes += len(current ^ previous)
        total += max(len(current), 1)
        previous = current
    return changes / max(total, 1)


def portfolio_metrics(selected: list[dict], cost_bp: float, all_rows: list[dict],
                      prob_key: str = "p_used") -> dict:
    if not selected:
        return {"n": 0, "coverage": 0.0, "hit_rate": float("nan"),
                "brier": float("nan"), "log_loss": float("nan"),
                "gross_return_per_day": float("nan"), "net_return_per_day": float("nan"),
                "turnover": 0.0, "cost_per_day": 0.0,
                "volatility": float("nan"), "downside_deviation": float("nan"),
                "max_drawdown": float("nan"), "candidate_count_per_day": 0.0,
                "median_return": float("nan"), "downside_return": float("nan")}
    returns = np.array([r["next_return"] for r in selected], dtype=float)
    ps = np.array([r[prob_key] for r in selected], dtype=float)
    ys = np.array([r["y"] for r in selected], dtype=float)
    cost_rate = cost_bp / 10000.0
    turnover = turnover_ratio(selected)
    gross = float(returns.mean())
    cost = cost_rate * turnover
    daily_book = defaultdict(list)
    for row in selected:
        daily_book[row["decision_time"]].append(row["next_return"])
    day_returns = np.array([np.mean(v) for _, v in sorted(daily_book.items())])
    cumulative = np.cumprod(1.0 + day_returns)
    peak = np.maximum.accumulate(np.concatenate([[1.0], cumulative]))[1:]
    negative = returns[returns < 0]
    days_total = len({r["decision_time"] for r in all_rows})
    return {
        "n": int(returns.size),
        "coverage": float(returns.size / max(len(all_rows), 1)),
        "hit_rate": float((ys == 1).mean()),
        "brier": brier(ps, ys),
        "log_loss": log_loss(ps, ys),
        "ece": ece(ps, ys),
        "gross_return_per_day": gross,
        "turnover": float(turnover),
        "cost_per_day": float(cost),
        "net_return_per_day": float(gross - cost),
        "median_return": float(np.median(returns)),
        "downside_return": float(negative.mean()) if negative.size else 0.0,
        "volatility": float(returns.std()),
        "downside_deviation": float(negative.std()) if negative.size else 0.0,
        "max_drawdown": float((cumulative / peak - 1.0).min()),
        "candidate_count_per_day": float(returns.size / max(days_total, 1)),
    }


def _slope_intercept(ps, ys):
    """Degenerate selected subsets (constant outcome or constant logit) can
    make the IRLS Hessian singular; report NaN instead of crashing."""
    from scripts.run_p13q_analysis import calibration_slope_intercept
    try:
        return calibration_slope_intercept(ps, ys)
    except np.linalg.LinAlgError:
        return {"calibration_intercept": float("nan"),
                "calibration_slope": float("nan")}


def _stability_tables(selected: list[dict]) -> dict:
    tables = {"yearly": defaultdict(list), "regime": defaultdict(list),
              "industry": defaultdict(list), "symbol": defaultdict(list)}
    for row in selected:
        tables["yearly"][row["decision_time"][:4]].append(row)
        if row.get("market_regime"):
            tables["regime"][row["market_regime"]].append(row)
        if row.get("industry"):
            tables["industry"][row["industry"]].append(row)
        tables["symbol"][row["symbol"]].append(row)
    out = {}
    for name, groups in tables.items():
        out[name] = {
            key: {
                "n": len(rows),
                "hit_rate": float(np.mean([r["y"] for r in rows])) if rows else None,
                "net_return_per_day": float(np.mean([r["next_return"] for r in rows]))
                if rows else None,
            }
            for key, rows in sorted(groups.items())
        }
    return out


SELECTION_REASON_TEMPLATE = {
    "hold_all": "baseline_hold_all",
    "threshold_raw_p50": "raw_probability_ge_0.50",
    "threshold_platt_p50": "platt_probability_ge_0.50",
    "threshold_iso_p50": "isotonic_probability_ge_0.50",
    "topk_platt_k3": "top_3_platt_probability",
    "percentile_platt_p80": "platt_probability_ge_daily_p80",
    "er_platt_0": "expected_return_gt_0",
    "er_platt_pos_risk": "expected_return_gt_0_and_volatility_le_daily_median",
}
PACKET_COST_SCENARIO = "low"
# Adopting one recommendation is modelled as one unit of turnover at the
# policy's low-cost rate (commission + slippage), deducted once per packet.


def build_packets(rows: list[dict], selected_keys: set, regime_of, policy: dict) -> list[dict]:
    prob_key = {"raw": "p", "platt": "p_platt", "isotonic": "p_iso",
                "none": "p"}[policy["calibration_method"]]
    cost_params = COST_SCENARIOS[PACKET_COST_SCENARIO]
    cost_rate = (cost_params["commission_bp"] + cost_params["slippage_bp"]) / 10000.0
    reason = SELECTION_REASON_TEMPLATE[policy["policy_id"]]
    packets = []
    for row in sorted(rows, key=lambda r: (r["decision_time"], r["symbol"])):
        key = (row["symbol"], row["decision_time"])
        if key not in selected_keys:
            continue
        # data_available_time equals the decision boundary: every packet
        # input (walk-forward probability, PIT features, industry, regime)
        # is admissible at decision_time, and the audit makes no stronger
        # field-level publication-time claim.
        packets.append({
            "decision_time": row["decision_time"],
            "symbol": row["symbol"],
            "policy_id": policy["policy_id"],
            "calibration_method": policy["calibration_method"],
            "raw_probability": row["p"],
            "calibrated_probability": row[prob_key],
            "expected_return": row["expected_return"],
            "risk_score": row["volatility"],
            "cost_scenario": PACKET_COST_SCENARIO,
            "cost_adjusted_expected_return": (
                float(row["expected_return"]) - cost_rate
            ),
            "market_regime": regime_of(row["decision_time"]),
            "selection_reason": reason,
            "risk_flags": row.get("risk_flags", []),
            "data_available_time": row["decision_time"],
        })
    return packets


def task_manifest(out_dir: Path):
    manifest = {}
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        data = path.read_bytes()
        manifest[path.name] = {
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
        }
    (out_dir / "manifest.json").write_text(
        json.dumps({"files": manifest, "generated_for": "P13-R"},
                   sort_keys=True, indent=1),
        encoding="utf-8",
    )
    print(f"manifest_written={out_dir / 'manifest.json'} ({len(manifest)} files)")
    return manifest


TASKS = ("features", "policies", "bootstrap", "registry", "manifest", "all")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--membership", required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument("--out-dir", default="data/industry/p13r")
    parser.add_argument("task", choices=TASKS)
    args = parser.parse_args()

    with open(args.audit, encoding="utf-8") as f:
        audit = json.load(f)
    with open(args.audit.replace(".json", ".meta.json"), encoding="utf-8") as f:
        audit["meta"] = json.load(f)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- base rows: validation OOS baseline rows with calibrated probs ----
    baseline = [r for r in audit["predictions"] if r["variant"] == "baseline"]
    discovery = [r for r in baseline if r["decision_time"][:10] < SPLIT_DATE]
    validation = [r for r in baseline if r["decision_time"][:10] >= SPLIT_DATE]
    ps_fit = np.array([r["p"] for r in discovery])
    ys_fit = np.array([r["y"] for r in discovery])
    platt = fit_platt(ps_fit, ys_fit)
    isotonic = fit_isotonic(ps_fit, ys_fit)

    from astock_v2.data.local_store import LocalHistoricalStore
    store = LocalHistoricalStore(args.root)
    labeler = RegimeLabeler(store, tuple(audit["meta"]["universe"]))
    from scripts.run_p13o_analysis import IndustryAttributor
    attributor = IndustryAttributor(args.membership)

    features = rolling_features(audit)
    rows = []
    p_val = np.array([r["p"] for r in validation])
    p_platt_arr = platt["apply"](p_val)
    p_iso_arr = isotonic["apply"](p_val)
    for i, r in enumerate(validation):
        key = (r["symbol"], r["decision_time"])
        feat = features.get(key) or {}
        p_cal = float(p_platt_arr[i])
        expected = None
        if feat:
            expected = p_cal * feat["upside"] + (1 - p_cal) * feat["downside"]
        rows.append({
            "symbol": r["symbol"],
            "decision_time": r["decision_time"],
            "p": r["p"],
            "p_platt": p_cal,
            "p_iso": float(p_iso_arr[i]),
            "y": r["y"],
            "next_return": next_return_of(audit, r),
            "expected_return": float(expected) if expected is not None else float("nan"),
            "volatility": feat.get("volatility", float("nan")),
            "max_drawdown": feat.get("max_drawdown", float("nan")),
            "downside_deviation": feat.get("downside_deviation", float("nan")),
            "industry": attributor.industry(r["symbol"], r["decision_time"]),
            "market_regime": labeler.regime(r["decision_time"]),
        })
    universe_median_vol = float(np.median([r["volatility"] for r in rows
                                           if r["volatility"] == r["volatility"]]))

    policies = build_policy_registry(universe_median_vol)

    if args.task in ("features", "all"):
        (out_dir / "feature_audit.json").write_text(json.dumps({
            "rows": len(rows),
            "pit_rule": "features use only rows whose decision_time date is "
                        "before the candidate's decision date",
            "sample_feature": {
                f"{symbol}|{decision_time}": value
                for (symbol, decision_time), value in list(features.items())[:1]
            } if features else {},
        }, sort_keys=True, indent=1), encoding="utf-8")

    if args.task in ("policies", "all"):
        evaluate_policies(policies, rows, COST_SCENARIOS, out_dir,
                          regime_of=labeler.regime)
    if args.task in ("bootstrap", "all"):
        run_bootstrap(policies, rows, out_dir)
    if args.task in ("registry", "all"):
        (out_dir / "decision_policy_registry.json").write_text(
            json.dumps({"split_date": SPLIT_DATE, "policies": policies,
                        "status": "research_only (no virgin holdout; see plan)"},
                       sort_keys=True, indent=1),
            encoding="utf-8",
        )
    if args.task == "all":
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        config = {
            "git_commit": commit,
            "seed": SEED,
            "bootstrap_rounds": BOOTSTRAP_ROUNDS,
            "split_date": SPLIT_DATE,
            "protocol": {"train": 252, "test": 20, "step": 20, "gap": 1},
            "universe_size": len(audit["meta"]["universe"]),
            "policy_ids": list(POLICY_IDS),
            "calibration_methods": ["raw", "platt", "isotonic"],
            "cost_scenarios": COST_SCENARIOS,
            "audit_file": args.audit,
        }
        (out_dir / "analysis_config.json").write_text(
            json.dumps(config, sort_keys=True, indent=1), encoding="utf-8"
        )
        print(f"analysis_config_written={out_dir / 'analysis_config.json'}")
        task_manifest(out_dir)


def next_return_of(audit, row):
    entry = audit["factors"].get(row["symbol"], {}).get(row["decision_time"], {})
    return entry.get("next_return")


def build_policy_registry(universe_median_vol: float) -> list[dict]:
    policies = [
        {"policy_id": "hold_all", "family": "baseline", "calibration_method": "none",
         "selection_rule": "hold_all", "selection_method": "hold_all",
         "probability_threshold": None, "top_k": None,
         "expected_return_threshold": None,
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
        {"policy_id": "threshold_raw_p50", "family": "threshold",
         "calibration_method": "raw", "selection_rule": "threshold",
         "selection_method": "probability_threshold",
         "probability_threshold": 0.50, "top_k": None,
         "expected_return_threshold": None,
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
        {"policy_id": "threshold_platt_p50", "family": "threshold",
         "calibration_method": "platt", "selection_rule": "threshold",
         "selection_method": "probability_threshold",
         "probability_threshold": 0.50, "top_k": None,
         "expected_return_threshold": None,
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
        {"policy_id": "threshold_iso_p50", "family": "threshold",
         "calibration_method": "isotonic", "selection_rule": "threshold",
         "selection_method": "probability_threshold",
         "probability_threshold": 0.50, "top_k": None,
         "expected_return_threshold": None,
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
        {"policy_id": "topk_platt_k3", "family": "top-k",
         "calibration_method": "platt", "selection_rule": "top_k",
         "selection_method": "top_k", "probability_threshold": None,
         "top_k": TOP_K, "expected_return_threshold": None,
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
        {"policy_id": "percentile_platt_p80", "family": "percentile",
         "calibration_method": "platt", "selection_rule": "percentile",
         "selection_method": "cross_sectional_percentile",
         "probability_threshold": None, "top_k": None, "percentile": PERCENTILE,
         "expected_return_threshold": None,
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
        {"policy_id": "er_platt_0", "family": "expected-return",
         "calibration_method": "platt", "selection_rule": "expected_return",
         "selection_method": "expected_return_threshold",
         "probability_threshold": None, "top_k": None,
         "expected_return_threshold": ER_THRESHOLD,
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
        {"policy_id": "er_platt_pos_risk", "family": "expected-return",
         "calibration_method": "platt", "selection_rule": "expected_return",
         "selection_method": "expected_return_plus_risk_filter",
         "probability_threshold": None, "top_k": None,
         "expected_return_threshold": ER_THRESHOLD,
         "risk_filter": "universe_median",
         "risk_constraints": {"max_per_industry": MAX_PER_INDUSTRY,
                              "volatility_max": "universe_median"},
         "cost_model": "zero/low/medium", "regime_filter": None,
         "industry_concentration_limit": MAX_PER_INDUSTRY, "turnover_limit": None},
    ]
    for policy in policies:
        if policy.get("risk_filter") == "universe_median":
            policy["risk_filter"] = universe_median_vol
    return policies


def evaluate_policies(policies, rows, cost_scenarios, out_dir, regime_of):
    policy_metrics = {}
    packets = {}
    for policy in policies:
        selected = apply_policy(policy, rows)
        prob_key = {"raw": "p", "platt": "p_platt", "isotonic": "p_iso",
                    "none": "p"}[policy["calibration_method"]]
        for r in selected:
            r["p_used"] = r[prob_key]
            r["policy_id"] = policy["policy_id"]
        by_cost = {}
        for scenario, params in cost_scenarios.items():
            cost_bp = params["commission_bp"] + params["slippage_bp"]
            by_cost[scenario] = portfolio_metrics(selected, cost_bp, rows)
        block = metrics_with_probability(selected, prob_key, total_rows=len(rows))
        block["cost_scenarios"] = by_cost
        block["stability"] = _stability_tables(selected)
        policy_metrics[policy["policy_id"]] = block
        packets[policy["policy_id"]] = build_packets(
            rows, {(r["symbol"], r["decision_time"]) for r in selected},
            regime_of, policy,
        )
    (out_dir / "policy_metrics.json").write_text(
        json.dumps(policy_metrics, sort_keys=True, indent=1), encoding="utf-8"
    )
    (out_dir / "recommendation_audit.json").write_text(
        json.dumps({"packets": packets, "note": "research-only; no order intent"},
                   sort_keys=True, indent=1),
        encoding="utf-8",
    )
    md_rows = []
    for pid, block in policy_metrics.items():
        net = block["cost_scenarios"]["low"]
        md_rows.append([
            pid, block["n"], f"{block['coverage']:.4f}",
            f"{block['hit_rate']:.4f}" if block["hit_rate"] == block["hit_rate"] else "-",
            f"{net['net_return_per_day']:+.5f}", f"{net['turnover']:.4f}",
            f"{net['max_drawdown']:.4f}" if net["max_drawdown"] == net["max_drawdown"] else "-",
        ])
    md = (
        "# P13-R policy comparison (low-cost scenario, validation window)\n\n"
        "Research observation only - not a validated production strategy.\n\n"
        + _md_table(["policy", "N", "coverage", "hit_rate", "net/day",
                     "turnover", "max_dd"], md_rows)
    )
    (out_dir / "policy_metrics.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)
    return policy_metrics


def metrics_with_probability(selected, prob_key, total_rows: int):
    if not selected:
        return {"n": 0, "coverage": 0.0}
    ps = [r[prob_key] for r in selected]
    ys = [r["y"] for r in selected]
    block = {
        "n": len(selected),
        "coverage": len(selected) / max(1, total_rows),
        "hit_rate": float(np.mean(ys)),
        "brier": brier(ps, ys),
        "log_loss": log_loss(ps, ys),
        "ece": ece(ps, ys),
    }
    block.update(_slope_intercept(ps, ys))
    return block


def run_bootstrap(policies, rows, out_dir):
    """Clustered bootstrap of low-cost net-return / hit-rate differences vs hold_all."""
    rng = np.random.default_rng(SEED)
    by_symbol = defaultdict(list)
    for r in rows:
        by_symbol[r["symbol"]].append(r)
    symbols = sorted(by_symbol)
    results = {}
    policy_selections = {}
    for policy in policies:
        policy_selections[policy["policy_id"]] = apply_policy(policy, rows)
    hold = policy_selections["hold_all"]
    cost_bp = COST_SCENARIOS["low"]["commission_bp"] + COST_SCENARIOS["low"]["slippage_bp"]

    def net_of(selected_idx):
        sel = [rows[i] for i in selected_idx]
        if not sel:
            return float("nan")
        returns = np.array([r["next_return"] for r in sel])
        return float(returns.mean() - cost_bp / 10000.0 * turnover_ratio(sel))

    index_by_symbol = defaultdict(list)
    for i, r in enumerate(rows):
        index_by_symbol[r["symbol"]].append(i)
    hold_keys = {(r["symbol"], r["decision_time"]) for r in hold}
    hold_idx = [i for i, r in enumerate(rows) if (r["symbol"], r["decision_time"]) in hold_keys]

    for policy in policies:
        pid = policy["policy_id"]
        if pid == "hold_all":
            continue
        sel = policy_selections[pid]
        sel_keys = {(r["symbol"], r["decision_time"]) for r in sel}
        deltas = {"net": [], "hit": [], "coverage": []}
        for _ in range(BOOTSTRAP_ROUNDS):
            pick = rng.integers(0, len(symbols), len(symbols))
            idx = [i for s in pick for i in index_by_symbol[symbols[s]]]
            sub_hold_idx = [i for i in idx
                            if (rows[i]["symbol"], rows[i]["decision_time"]) in hold_keys]
            sub_sel_idx = [i for i in idx
                           if (rows[i]["symbol"], rows[i]["decision_time"]) in sel_keys]
            deltas["net"].append(net_of(sub_sel_idx) - net_of(sub_hold_idx))
            sub_sel = [rows[i] for i in sub_sel_idx]
            sub_hold = [rows[i] for i in sub_hold_idx]
            if sub_sel and sub_hold:
                deltas["hit"].append(
                    float(np.mean([r["y"] for r in sub_sel]))
                    - float(np.mean([r["y"] for r in sub_hold]))
                )
            deltas["coverage"].append(len(sub_sel) / max(len(idx), 1)
                                      - len(sub_hold) / max(len(idx), 1))
        results[pid] = {
            "vs": "hold_all",
            "cost_scenario": "low",
            "net_return_difference": _ci(deltas["net"]),
            "hit_rate_difference": _ci(deltas["hit"]),
            "coverage_difference": _ci(deltas["coverage"]),
        }
    (out_dir / "bootstrap_results.json").write_text(
        json.dumps({"unit": "symbol", "rounds": BOOTSTRAP_ROUNDS, "seed": SEED,
                    "results": results},
                   sort_keys=True, indent=1),
        encoding="utf-8",
    )
    print(f"bootstrap_written={out_dir / 'bootstrap_results.json'}")
    return results


def _ci(values):
    arr = np.asarray([v for v in values if v == v], dtype=float)
    if arr.size == 0:
        return {"point": float("nan"), "ci95_low": float("nan"),
                "ci95_high": float("nan")}
    return {
        "point": float(arr.mean()),
        "ci95_low": float(np.quantile(arr, 0.025)),
        "ci95_high": float(np.quantile(arr, 0.975)),
    }


if __name__ == "__main__":
    main()
