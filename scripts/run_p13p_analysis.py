"""P13-P: independent factor validation and candidate selection.

Research-only: consumes the P13-O audit JSON (no production rerun), reuses
the runner's walk-forward evaluator per symbol exactly as the production
benchmark does, and writes artifacts to data/industry/p13p/. The production
prediction path is not touched and no result here feeds back into it.

Protocol invariants (locked by docs/P13P_RESEARCH_PLAN.md and tests):
- train=252 test=20 step=20 gap=1 logistic; every model walks the identical
  per-symbol row set, so OOS predictions align row for row.
- DISCOVERY = decision_time < SPLIT_DATE; VALIDATION = decision_time >=
  SPLIT_DATE (2025-01-01, fixed a priori natural-year boundary).
- Quintile edges are computed on the discovery OOS sample only and applied
  to every slice, so the validation window never shapes its own buckets.
- Bootstrap: symbol clusters, B=1000, seed 20260929.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from math import log
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_local_industry_relative_oos import (
    STOCK_FACTORS,
    TRAIN_SIZE,
    TEST_SIZE,
    STEP,
    GAP,
    evaluate,
)
from scripts.run_p13o_analysis import RegimeLabeler, _md_table, _write

SEED = 20260929
BOOTSTRAP_ROUNDS = 1000
SPLIT_DATE = "2025-01-01"

ALL_FACTORS = (
    "momentum", "volatility", "trend", "volume_ratio",
    "industry_relative_return_5", "industry_relative_return_20",
)

REGISTRY_STATUSES = (
    "candidate", "validated_candidate", "insufficient_evidence",
    "context_only", "risk_feature", "rejected_for_alpha",
)


@dataclass(frozen=True)
class AuditRow:
    """Minimal row contract expected by the shared walk-forward evaluator."""
    decision_time: str
    label: int


def accuracy(ps, ys):
    if not ys:
        return float("nan")
    return sum((p >= 0.5) == bool(y) for p, y in zip(ps, ys)) / len(ys)


def brier(ps, ys):
    if not ys:
        return float("nan")
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)


def log_loss(ps, ys):
    if not ys:
        return float("nan")
    eps = 1e-15
    return -sum(
        y * log(max(p, eps)) + (1 - y) * log(max(1 - p, eps))
        for p, y in zip(ps, ys)
    ) / len(ys)


def metrics_block(ps, ys, base_ps=None):
    out = {
        "n": len(ys),
        "accuracy": accuracy(ps, ys),
        "brier": brier(ps, ys),
        "log_loss": log_loss(ps, ys),
        "mean_p": sum(ps) / len(ps) if ps else float("nan"),
        "positive_rate": sum(ys) / len(ys) if ys else float("nan"),
    }
    if base_ps is not None:
        out["delta_accuracy"] = out["accuracy"] - accuracy(base_ps, ys)
        out["delta_brier"] = out["brier"] - brier(base_ps, ys)
        out["delta_log_loss"] = out["log_loss"] - log_loss(base_ps, ys)
    return out


def load_audit(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        audit = json.load(f)
    with open(path.replace(".json", ".meta.json"), encoding="utf-8") as f:
        audit["meta"] = json.load(f)
    return audit


def build_rows(audit: dict) -> dict[str, list[tuple[AuditRow, dict]]]:
    """Reconstruct per-symbol paired factor rows from the audit payload.

    Ordered by decision time; identical to the row sets the runner's
    _factor_rows produced, so walk-forward windows match the benchmark.
    """
    rows: dict[str, list[tuple[AuditRow, dict]]] = {}
    for symbol, per_day in audit["factors"].items():
        series = []
        for decision_time in sorted(per_day):
            entry = per_day[decision_time]
            series.append(
                (AuditRow(decision_time=decision_time, label=int(entry["label"])), dict(entry))
            )
        rows[symbol] = series
    return rows


def run_model(
    rows_by_symbol: dict[str, list[tuple[AuditRow, dict]]], factor_names: tuple[str, ...]
) -> list[tuple[str, str, float, int, float]]:
    """Evaluate one model per symbol (as the runner does) and pool OOS rows.

    Returns (symbol, decision_time, p, y, baseline_p) tuples. The baseline_p
    column is the runner's train-rate baseline; model-vs-model deltas are
    computed between pooled rows of two runs over the same row sets.
    """
    pooled = []
    for symbol in sorted(rows_by_symbol):
        details: list[tuple[str, float, int, float]] = []
        evaluate(rows_by_symbol[symbol], factor_names, details=details)
        for decision_time, p, y, base_p in details:
            pooled.append((symbol, decision_time, p, y, base_p))
    return pooled


def window_of(decision_time: str) -> str:
    return "validation" if decision_time[:10] >= SPLIT_DATE else "discovery"


def split_rows(rows):
    """Temporal discovery/validation split at SPLIT_DATE (a priori)."""
    discovery = [r for r in rows if r[0].decision_time[:10] < SPLIT_DATE]
    validation = [r for r in rows if r[0].decision_time[:10] >= SPLIT_DATE]
    return discovery, validation


def quintile_edges(values) -> tuple[float, ...]:
    """Equal-frequency quintile edges; callers pass discovery-sample values."""
    return tuple(float(q) for q in np.quantile(np.asarray(values), [0.2, 0.4, 0.6, 0.8]))


def quintile_of(value: float, edges: tuple[float, ...]) -> int:
    return int(np.searchsorted(edges, value, side="right"))


def quintile_table(enriched, edges) -> list[dict]:
    groups: list[list[tuple[float, int, float | None]]] = [[] for _ in range(5)]
    for value, y, next_return in enriched:
        groups[quintile_of(value, edges)].append((value, y, next_return))
    table = []
    for q, group in enumerate(groups, start=1):
        ups = [y for _, y, _ in group]
        rets = [nr for _, _, nr in group if nr is not None]
        table.append({
            "quintile": q,
            "n": len(group),
            "mean_factor": float(np.mean([g[0] for g in group])) if group else float("nan"),
            "up_rate": float(np.mean(ups)) if ups else float("nan"),
            "mean_next_return": float(np.mean(rets)) if rets else float("nan"),
        })
    return table


def spread(table: list[dict], key: str) -> float:
    if len(table) < 5:
        return float("nan")
    return table[4][key] - table[0][key]


def _time_slices(times: list[str]) -> dict[str, set[str]]:
    from datetime import datetime, timedelta

    thirds = len(times) // 3
    first = set(times[:thirds])
    middle = set(times[thirds:2 * thirds])
    cutoff_2y = (datetime.fromisoformat(times[-1][:10]) - timedelta(days=730)).isoformat()
    slices = {
        "all": set(times),
        "first_third": first,
        "middle_third": middle,
        "last_third": set(times) - first - middle,
        "last_2_years": {t for t in times if t[:10] >= cutoff_2y},
        "discovery": {t for t in times if t[:10] < SPLIT_DATE},
        "validation": {t for t in times if t[:10] >= SPLIT_DATE},
    }
    for year in sorted({t[:4] for t in times}):
        slices[f"year_{year}"] = {t for t in times if t[:4] == year}
    return slices


# --------------------------------------------------------------------------
# T1: single-factor audit (Model A baseline vs Model B baseline + factor)
# --------------------------------------------------------------------------

def run_single_factor_audit(audit, out_dir: Path, args):
    rows_by_symbol = build_rows(audit)
    payload = {"protocol": {
        "train_size": TRAIN_SIZE, "test_size": TEST_SIZE, "step": STEP, "gap": GAP,
        "note": "Model A and Model B walk the identical per-symbol row sets; "
                "the shared evaluator yields row-aligned OOS predictions.",
    }, "factors": {}}
    model_a = run_model(rows_by_symbol, STOCK_FACTORS)
    md_rows = []
    for factor in ALL_FACTORS:
        model_b = run_model(rows_by_symbol, STOCK_FACTORS + (factor,))
        aligned = [(s, dt, y) for s, dt, _, y, _ in model_a] == [
            (s, dt, y) for s, dt, _, y, _ in model_b
        ]
        pa = [p for _, _, p, _, _ in model_a]
        pb = [p for _, _, p, _, _ in model_b]
        ya = [y for _, _, _, y, _ in model_a]
        block_a = metrics_block(pa, ya)
        block_b = metrics_block(pb, ya, base_ps=pa)
        payload["factors"][factor] = {
            "aligned_rows": aligned,
            "n": block_b["n"],
            "model_a_baseline": block_a,
            "model_b_baseline_plus_factor": block_b,
        }
        md_rows.append([
            factor, block_b["n"], "yes" if aligned else "NO",
            f"{block_a['accuracy']:.4f}", f"{block_b['accuracy']:.4f}",
            f"{block_b['delta_accuracy']:+.4f}",
            f"{block_b['delta_brier']:+.5f}",
            f"{block_b['delta_log_loss']:+.5f}",
        ])
    md = (
        "# P13-P T1: single-factor OOS audit (Model A vs baseline+factor)\n\n"
        "Model A = the production baseline (momentum/volatility/trend/"
        "volume_ratio). Model B adds exactly one factor. Both walk the "
        "identical per-symbol row sets; deltas compare pooled OOS rows.\n\n"
        + _md_table(
            ["factor", "N", "aligned", "acc_A", "acc_B", "d_acc", "d_brier", "d_logloss"],
            md_rows,
        )
    )
    _write(out_dir, "single_factor_audit", payload, md)
    return payload


# --------------------------------------------------------------------------
# T2: volatility stability (time / symbol / regime / bootstrap)
# --------------------------------------------------------------------------

def _volatility_enriched(audit):
    """OOS (symbol, decision_time, value, y, next_return) for one factor."""
    oos_keys = {
        (r["symbol"], r["decision_time"])
        for r in audit["predictions"] if r["variant"] == "baseline"
    }
    enriched = []
    for symbol, per_day in audit["factors"].items():
        for decision_time, entry in per_day.items():
            if (symbol, decision_time) not in oos_keys:
                continue
            value = entry.get("volatility")
            if value is None:
                continue
            enriched.append((symbol, decision_time, value, int(entry["label"]),
                             entry.get("next_return")))
    return enriched


def run_volatility_stability(audit, out_dir: Path, args, store=None):
    enriched = _volatility_enriched(audit)
    disc_values = [
        v for _, dt, v, _, _ in enriched if dt[:10] < SPLIT_DATE
    ]
    edges = quintile_edges(disc_values)

    payload = {
        "factor": "volatility",
        "quintile_edges_discovery": list(edges),
        "edge_source": f"discovery OOS sample (decision_time < {SPLIT_DATE})",
        "slices": {},
        "per_symbol_spread": {},
    }

    slices = _time_slices(sorted({dt for _, dt, *_ in enriched}))
    for name, day_set in slices.items():
        subset = [(v, y, nr) for _, dt, v, y, nr in enriched if dt in day_set]
        table = quintile_table(subset, edges)
        payload["slices"][name] = {
            "n": len(subset),
            "quintiles": table,
            "spread_up_rate": spread(table, "up_rate"),
            "spread_next_return": spread(table, "mean_next_return"),
        }

    spreads_up, spreads_ret = [], []
    by_symbol = defaultdict(list)
    for symbol, dt, v, y, nr in enriched:
        by_symbol[symbol].append((v, y, nr))
    for symbol in sorted(by_symbol):
        subset = by_symbol[symbol]
        if len(subset) < 50:
            continue
        table = quintile_table(subset, edges)
        su = spread(table, "up_rate")
        sr = spread(table, "mean_next_return")
        payload["per_symbol_spread"][symbol] = {
            "n": len(subset), "spread_up_rate": su, "spread_next_return": sr,
        }
        spreads_up.append(su)
        spreads_ret.append(sr)

    def dist(values):
        arr = np.asarray(values, dtype=float)
        return {
            "n_symbols": int(arr.size),
            "positive": int((arr > 0).sum()),
            "negative": int((arr < 0).sum()),
            "near_zero_abs_lt_1e-9": int((np.abs(arr) < 1e-9).sum()),
            "mean": float(arr.mean()), "median": float(np.median(arr)),
            "q10": float(np.quantile(arr, 0.10)),
            "q25": float(np.quantile(arr, 0.25)),
            "q75": float(np.quantile(arr, 0.75)),
            "q90": float(np.quantile(arr, 0.90)),
        }

    payload["per_symbol_summary"] = {
        "spread_up_rate": dist(spreads_up),
        "spread_next_return": dist(spreads_ret),
    }

    if store is None:
        from astock_v2.data.local_store import LocalHistoricalStore
        store = LocalHistoricalStore(args.root)
    labeler = RegimeLabeler(store, tuple(audit["meta"]["universe"]))
    regime_buckets = defaultdict(list)
    for symbol, dt, v, y, nr in enriched:
        regime_buckets[labeler.regime(dt)].append((v, y, nr))
    payload["regimes"] = {}
    for regime in ("BULL", "NEUTRAL", "BEAR"):
        table = quintile_table(regime_buckets[regime], edges)
        payload["regimes"][regime] = {
            "n": len(regime_buckets[regime]),
            "quintiles": table,
            "spread_up_rate": spread(table, "up_rate"),
            "spread_next_return": spread(table, "mean_next_return"),
        }

    rng = np.random.default_rng(SEED)
    symbols = sorted(by_symbol)
    boot_up, boot_ret = [], []
    for _ in range(BOOTSTRAP_ROUNDS):
        pick = rng.integers(0, len(symbols), len(symbols))
        sample = [e for i in pick for e in by_symbol[symbols[i]]]
        table = quintile_table(sample, edges)
        boot_up.append(spread(table, "up_rate"))
        boot_ret.append(spread(table, "mean_next_return"))
    payload["bootstrap"] = {
        "unit": "symbol (clustered, resampled with replacement)",
        "rounds": BOOTSTRAP_ROUNDS,
        "seed": SEED,
        "spread_up_rate": {
            "point": payload["slices"]["all"]["spread_up_rate"],
            "ci95_low": float(np.quantile(boot_up, 0.025)),
            "ci95_high": float(np.quantile(boot_up, 0.975)),
        },
        "spread_next_return": {
            "point": payload["slices"]["all"]["spread_next_return"],
            "ci95_low": float(np.quantile(boot_ret, 0.025)),
            "ci95_high": float(np.quantile(boot_ret, 0.975)),
        },
    }

    md_rows = []
    for name in ("all", "first_third", "middle_third", "last_third",
                 "discovery", "validation", "year_2021", "year_2022",
                 "year_2023", "year_2024", "year_2025", "year_2026",
                 "last_2_years"):
        s = payload["slices"].get(name)
        if not s:
            continue
        md_rows.append([
            name, s["n"],
            f"{s['quintiles'][0]['up_rate']:.4f}",
            f"{s['quintiles'][4]['up_rate']:.4f}",
            f"{s['spread_up_rate']:+.4f}",
            f"{s['spread_next_return']:+.5f}",
        ])
    bs = payload["bootstrap"]
    md = (
        f"# P13-P T2: volatility quintile stability (edges from discovery < {SPLIT_DATE})\n\n"
        f"Bootstrap: {bs['unit']}, B={bs['rounds']}, seed={bs['seed']}.\n\n"
        "## Slices (Q1/Q5 up-rate and Q5-Q1 spreads)\n\n"
        + _md_table(["slice", "N", "q1_up", "q5_up", "spread_up", "spread_ret"], md_rows)
        + "\n\n## Symbol-clustered bootstrap CI95\n\n"
        f"- spread_up_rate: {bs['spread_up_rate']['point']:+.4f} "
        f"[{bs['spread_up_rate']['ci95_low']:+.4f}, {bs['spread_up_rate']['ci95_high']:+.4f}]\n"
        f"- spread_next_return: {bs['spread_next_return']['point']:+.5f} "
        f"[{bs['spread_next_return']['ci95_low']:+.5f}, "
        f"{bs['spread_next_return']['ci95_high']:+.5f}]\n"
    )
    _write(out_dir, "volatility_stability", payload, md)
    return payload


# --------------------------------------------------------------------------
# T3: incremental models A-E with discovery/validation windows + bootstrap
# --------------------------------------------------------------------------

INCREMENTAL_MODELS = {
    "A_baseline": STOCK_FACTORS,
    "B_baseline_plus_volatility": STOCK_FACTORS + ("volatility",),
    "C_baseline_plus_ir5": STOCK_FACTORS + ("industry_relative_return_5",),
    "D_baseline_plus_ir20": STOCK_FACTORS + ("industry_relative_return_20",),
    "E_baseline_plus_vol_ir5_ir20": STOCK_FACTORS + (
        "volatility", "industry_relative_return_5", "industry_relative_return_20",
    ),
}


def run_incremental_models(audit, out_dir: Path, args):
    rows_by_symbol = build_rows(audit)
    payload = {
        "split_date": SPLIT_DATE,
        "windows_note": (
            "window metrics restrict the full-sample walk-forward OOS rows to "
            "each temporal window; training inside the walk-forward only ever "
            "uses rows earlier than each test window, so no validation-period "
            "row can enter any training set."
        ),
        "models": {},
    }
    predictions = {}
    for model, factor_names in INCREMENTAL_MODELS.items():
        predictions[model] = run_model(rows_by_symbol, factor_names)

    for model, rows in predictions.items():
        entry = {}
        for window in ("full", "discovery", "validation"):
            sel = [
                (p, y, bp) for _, dt, p, y, bp in rows
                if window == "full" or window_of(dt) == window
            ]
            entry[window] = metrics_block(
                [p for p, _, _ in sel], [y for _, y, _ in sel],
                base_ps=[bp for _, _, bp in sel],
            )
        payload["models"][model] = entry

    md_rows = []
    for model in INCREMENTAL_MODELS:
        for window in ("full", "discovery", "validation"):
            m = payload["models"][model][window]
            md_rows.append([
                model, window, m["n"],
                f"{m['accuracy']:.4f}", f"{m['brier']:.5f}", f"{m['log_loss']:.5f}",
                f"{m['delta_accuracy']:+.4f}",
                f"{m['delta_brier']:+.5f}",
                f"{m['delta_log_loss']:+.5f}",
            ])
    payload["bootstrap_incremental"] = _bootstrap_incremental(
        rows_by_symbol, predictions
    )
    bi = payload["bootstrap_incremental"]
    md = (
        f"# P13-P T3: incremental models (split_date={SPLIT_DATE})\n\n"
        "Model A baseline; B +volatility; C +ir5; D +ir20; E +volatility+ir5+ir20. "
        "Identical per-symbol row sets and walk-forward; deltas are against the "
        "pooled Model A probabilities.\n\n"
        + _md_table(
            ["model", "window", "N", "acc", "brier", "logloss",
             "d_acc", "d_brier", "d_logloss"],
            md_rows,
        )
        + "\n\n## Symbol-clustered bootstrap of B-vs-A deltas (full window)\n\n"
        f"- B={bi['rounds']}, seed={bi['seed']}, unit={bi['unit']}\n"
        + "".join(
            f"- {metric}: {bi[metric]['point']:+.5f} "
            f"[{bi[metric]['ci95_low']:+.5f}, {bi[metric]['ci95_high']:+.5f}]\n"
            for metric in ("delta_accuracy", "delta_brier", "delta_log_loss")
        )
    )
    _write(out_dir, "incremental_models", payload, md)
    return payload


def _bootstrap_incremental(rows_by_symbol, predictions):
    """Clustered bootstrap of Model B minus Model A pooled deltas."""
    deltas_by_symbol = {}
    for symbol in sorted(rows_by_symbol):
        rows_a = [r for r in predictions["A_baseline"] if r[0] == symbol]
        rows_b = [r for r in predictions["B_baseline_plus_volatility"] if r[0] == symbol]
        if not rows_a or not rows_b:
            # symbols without SW1 membership produce zero factor rows and no
            # OOS predictions; they cannot contribute a delta.
            continue
        ps_a = [p for _, _, p, _, _ in rows_a]
        ps_b = [p for _, _, p, _, _ in rows_b]
        ys = [y for _, _, _, y, _ in rows_a]
        deltas_by_symbol[symbol] = {
            "delta_accuracy": accuracy(ps_b, ys) - accuracy(ps_a, ys),
            "delta_brier": brier(ps_b, ys) - brier(ps_a, ys),
            "delta_log_loss": log_loss(ps_b, ys) - log_loss(ps_a, ys),
        }
    symbols = sorted(deltas_by_symbol)
    rng = np.random.default_rng(SEED)
    metrics = ("delta_accuracy", "delta_brier", "delta_log_loss")
    samples = {metric: [] for metric in metrics}
    for _ in range(BOOTSTRAP_ROUNDS):
        pick = rng.integers(0, len(symbols), len(symbols))
        for metric in metrics:
            samples[metric].append(
                float(np.mean([deltas_by_symbol[symbols[i]][metric] for i in pick]))
            )
    point = {
        metric: float(np.mean([deltas_by_symbol[s][metric] for s in symbols]))
        for metric in metrics
    }
    out = {
        "unit": "symbol (clustered, resampled with replacement)",
        "rounds": BOOTSTRAP_ROUNDS,
        "seed": SEED,
        "comparison": "Model B (baseline+volatility) minus Model A (baseline)",
    }
    for metric in samples:
        out[metric] = {
            "point": point[metric],
            "ci95_low": float(np.quantile(samples[metric], 0.025)),
            "ci95_high": float(np.quantile(samples[metric], 0.975)),
        }
    return out


# --------------------------------------------------------------------------
# T4: redundancy diagnostics
# --------------------------------------------------------------------------

def run_factor_redundancy(audit, out_dir: Path, args):
    cols = {f: [] for f in ALL_FACTORS}
    n_missing = {f: 0 for f in ALL_FACTORS}
    n_rows = 0
    for symbol, per_day in audit["factors"].items():
        for decision_time, entry in per_day.items():
            n_rows += 1
            for f in ALL_FACTORS:
                v = entry.get(f)
                if v is None:
                    n_missing[f] += 1
                else:
                    cols[f].append(v)
    arrays = {f: np.asarray(cols[f], dtype=float) for f in ALL_FACTORS}

    def spearman(x, y):
        rx = np.argsort(np.argsort(x)).astype(float)
        ry = np.argsort(np.argsort(y)).astype(float)
        return float(np.corrcoef(rx, ry)[0, 1])

    corr_p, corr_s = {}, {}
    for i, a in enumerate(ALL_FACTORS):
        for b in ALL_FACTORS[i + 1:]:
            corr_p[f"{a}|{b}"] = float(np.corrcoef(arrays[a], arrays[b])[0, 1])
            corr_s[f"{a}|{b}"] = spearman(arrays[a], arrays[b])
    stats = {}
    for f in ALL_FACTORS:
        arr = arrays[f]
        stats[f] = {
            "n": int(arr.size), "missing": n_missing[f],
            "mean": float(arr.mean()), "std": float(arr.std()),
            "min": float(arr.min()), "q25": float(np.quantile(arr, 0.25)),
            "median": float(np.median(arr)), "q75": float(np.quantile(arr, 0.75)),
            "max": float(arr.max()),
        }
    def pair_key(a: str, b: str) -> str:
        return f"{a}|{b}" if ALL_FACTORS.index(a) < ALL_FACTORS.index(b) else f"{b}|{a}"

    payload = {
        "n_rows": n_rows,
        "distribution": stats,
        "pearson": corr_p,
        "spearman": corr_s,
        "focus": {
            f"volatility|{b}": {
                "pearson": corr_p[pair_key("volatility", b)],
                "spearman": corr_s[pair_key("volatility", b)],
            }
            for b in ("momentum", "trend", "volume_ratio",
                      "industry_relative_return_5", "industry_relative_return_20")
        },
        "note": "high correlation is diagnostic only; no factor is removed here",
    }
    md_rows = [
        [pair, f"{p:+.4f}", f"{corr_s[pair]:+.4f}"]
        for pair, p in sorted(corr_p.items(), key=lambda kv: -abs(kv[1]))
    ][:12]
    md = (
        "# P13-P T4: factor redundancy diagnostics\n\n"
        f"Rows={n_rows}. Ranked by |Pearson| (top 12 shown); full matrix in JSON.\n\n"
        + _md_table(["pair", "pearson", "spearman"], md_rows)
        + "\n\n## volatility focus\n\n"
        + _md_table(
            ["pair", "pearson", "spearman"],
            [[k, f"{v['pearson']:+.4f}", f"{v['spearman']:+.4f}"]
             for k, v in payload["focus"].items()],
        )
    )
    _write(out_dir, "factor_redundancy", payload, md)
    return payload


# --------------------------------------------------------------------------
# T5: candidate registry
# --------------------------------------------------------------------------

def run_candidate_registry(audit, out_dir: Path, args, incremental):
    """Build factor_candidates.json per the handoff schema.

    Statuses follow fixed rules stated before inspecting window results.
    volatility cannot exceed 'candidate': P13-O's discovery consumed the
    whole history, so no virgin holdout exists (insufficient independent
    validation data). No production factor is removed or demoted here.
    """
    t1 = json.loads((out_dir / "single_factor_audit.json").read_text(encoding="utf-8"))
    t2 = json.loads((out_dir / "volatility_stability.json").read_text(encoding="utf-8"))
    registry = {
        "generated_for": "P13-P",
        "split_date": SPLIT_DATE,
        "insufficient_independent_validation": (
            "discovery (P13-O) consumed the full history; the 2025-01-01 split "
            "is an internal consistency check, not a virgin holdout. Within "
            "that check the volatility Q5-Q1 up-rate spread flips sign "
            "(discovery +0.0525 vs validation -0.0026) and the positive full-"
            "sample bootstrap CI is driven by 2022-2024."
        ),
        "candidates": {},
    }

    def entry(factor, role, notes, status):
        t1e = t1["factors"][factor]["model_b_baseline_plus_factor"]
        vol_specific = factor == "volatility"
        return {
            "factor_name": factor,
            "role": role,
            "discovery_period": f"OOS < {SPLIT_DATE}",
            "validation_period": f"OOS >= {SPLIT_DATE}",
            "n_discovery": incremental["models"]["A_baseline"]["discovery"]["n"],
            "n_validation": incremental["models"]["A_baseline"]["validation"]["n"],
            "incremental_accuracy": t1e["delta_accuracy"],
            "incremental_brier": t1e["delta_brier"],
            "incremental_logloss": t1e["delta_log_loss"],
            "bootstrap_ci": t2["bootstrap"] if vol_specific else None,
            "time_stability": (
                {name: {"spread_up_rate": s["spread_up_rate"],
                        "spread_next_return": s["spread_next_return"]}
                 for name, s in sorted(t2["slices"].items())
                 if name.startswith("year_") or name in ("all", "discovery", "validation")}
                if vol_specific else "not_computed_this_phase"
            ),
            "symbol_stability": (
                t2["per_symbol_summary"] if vol_specific else "not_computed_this_phase"
            ),
            "regime_stability": (
                {k: {"spread_up_rate": v["spread_up_rate"],
                     "spread_next_return": v["spread_next_return"]}
                 for k, v in t2["regimes"].items()} if vol_specific
                else "not_computed_this_phase"
            ),
            "redundancy_notes": notes,
            "validation_status": status,
        }

    registry["candidates"]["volatility"] = entry(
        "volatility",
        "alpha_candidate_under_validation",
        "lowest |correlation| with the other production factors; monotone "
        "quintile structure discovered in P13-O, validation_status capped at "
        "candidate by the discovery-coverage rule",
        "candidate",
    )
    for factor in ("momentum", "trend", "volume_ratio"):
        registry["candidates"][factor] = entry(
            factor,
            "production_baseline_component",
            "already inside Model A; single-factor audit measures it on top of "
            "the other three, not as a new alpha claim",
            "context_only",
        )
    for factor in ("industry_relative_return_5", "industry_relative_return_20"):
        registry["candidates"][factor] = entry(
            factor,
            "industry_relative_candidate",
            "P13-O: no stable OOS increment and consistent small calibration "
            "loss; P13-P single-factor audit confirms on the same rows",
            "rejected_for_alpha",
        )
    (out_dir / "factor_candidates.json").write_text(
        json.dumps(registry, sort_keys=True, indent=1), encoding="utf-8"
    )
    print(f"factor_candidates_written={out_dir / 'factor_candidates.json'}")
    return registry


ANALYSES = ("single", "volatility", "incremental", "redundancy", "registry", "all")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True,
                        help="P13-O predictions JSON (with .meta.json beside it)")
    parser.add_argument("--out-dir", default="data/industry/p13p")
    parser.add_argument("--membership", required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument("task", choices=ANALYSES)
    args = parser.parse_args()

    audit = load_audit(args.audit)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.task in ("single", "all"):
        run_single_factor_audit(audit, out_dir, args)
    if args.task in ("volatility", "all"):
        run_volatility_stability(audit, out_dir, args)
    if args.task in ("incremental", "all"):
        run_incremental_models(audit, out_dir, args)
    if args.task in ("redundancy", "all"):
        run_factor_redundancy(audit, out_dir, args)
    if args.task in ("registry", "all"):
        incremental = json.loads(
            (out_dir / "incremental_models.json").read_text(encoding="utf-8")
        )
        run_candidate_registry(audit, out_dir, args, incremental)

    if args.task == "all":
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        config = {
            "git_commit": commit,
            "seed": SEED,
            "bootstrap_rounds": BOOTSTRAP_ROUNDS,
            "split_date": SPLIT_DATE,
            "audit_file": args.audit,
            "membership": args.membership,
            "protocol": {
                "train_size": TRAIN_SIZE, "test_size": TEST_SIZE,
                "step": STEP, "gap": GAP,
            },
            "universe_size": len(audit["meta"]["universe"]),
            "factor_list": list(ALL_FACTORS),
            "models": list(INCREMENTAL_MODELS),
        }
        (out_dir / "analysis_config.json").write_text(
            json.dumps(config, sort_keys=True, indent=1), encoding="utf-8"
        )
        print(f"analysis_config_written={out_dir / 'analysis_config.json'}")


if __name__ == "__main__":
    main()
