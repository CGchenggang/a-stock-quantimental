"""P13-Q: probability / calibration analysis over the P13-O OOS audit.

Research-only. Consumes data/industry/p13o/oos_predictions_76.json baseline
rows; never touches src/. The calibration temporal protocol is fixed a
priori: calibration methods are fitted on discovery OOS rows
(decision_time < 2025-01-01) and evaluated on validation OOS rows
(decision_time >= 2025-01-01) - the same a priori boundary as P13-P.
Probability bins are the fixed 0.05 grid from docs/P13Q_RESEARCH_PLAN.md.
All registry statuses are research_only by design: P13-O consumed the whole
history, so no virgin holdout exists for calibration validation either.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from math import log
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_p13u_gate import assert_research_zone

SEED = 20260929
BOOTSTRAP_ROUNDS = 1000
SPLIT_DATE = "2025-01-01"
BIN_EDGES = [round(0.05 * i, 2) for i in range(21)]  # 0.00 .. 1.00
EPS = 1e-12

STATUS_VOCABULARY = (
    "research_only", "candidate", "validated_candidate",
    "insufficient_evidence", "rejected",
)


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------

def brier(ps, ys):
    return float(np.mean((np.asarray(ps) - np.asarray(ys)) ** 2))


def log_loss(ps, ys):
    p = np.clip(np.asarray(ps, dtype=float), EPS, 1 - EPS)
    y = np.asarray(ys, dtype=float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def entropy(ps):
    p = np.clip(np.asarray(ps, dtype=float), EPS, 1 - EPS)
    return float(np.mean(-p * np.log(p) - (1 - p) * np.log(1 - p)))


def bin_of(p: float, edges=BIN_EDGES) -> int:
    """Bucket index on the fixed 0.05 grid; last bucket is closed."""
    if p >= edges[-1]:
        return len(edges) - 2
    return int(np.searchsorted(edges, p, side="right") - 1)


def bucket_stats(ps, ys, next_returns=None, edges=BIN_EDGES) -> list[dict]:
    ps = np.asarray(ps, dtype=float)
    ys = np.asarray(ys, dtype=float)
    out = []
    for b in range(len(edges) - 1):
        lo, hi = edges[b], edges[b + 1]
        if b == len(edges) - 2:
            mask = (ps >= lo) & (ps <= hi)
        else:
            mask = (ps >= lo) & (ps < hi)
        n = int(mask.sum())
        entry = {
            "bin": f"[{lo:.2f},{hi:.2f}]" + ("" if b < len(edges) - 2 else " closed"),
            "lo": lo, "hi": hi, "n": n,
            "mean_p": float(ps[mask].mean()) if n else None,
            "observed_rate": float(ys[mask].mean()) if n else None,
        }
        if entry["mean_p"] is not None:
            entry["difference"] = entry["mean_p"] - entry["observed_rate"]
            entry["calibration_error"] = abs(entry["difference"])
        else:
            entry["difference"] = None
            entry["calibration_error"] = None
        if next_returns is not None:
            nr = np.asarray(next_returns, dtype=float)[mask]
            entry["mean_next_return"] = float(nr.mean()) if n and nr.size else None
        out.append(entry)
    return out


def ece(ps, ys, edges=BIN_EDGES) -> float:
    table = bucket_stats(ps, ys, edges=edges)
    total = sum(b["n"] for b in table)
    if not total:
        return float("nan")
    return float(sum(
        (b["n"] / total) * b["calibration_error"]
        for b in table if b["calibration_error"] is not None
    ))


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def calibration_slope_intercept(ps, ys):
    """OOS calibration curve: logistic fit of y on logit(p).

    slope=1 / intercept=0 means perfectly calibrated in the logistic sense.
    Fitted with deterministic Newton-IRLS on strictly OOS rows.
    """
    x = _logit(ps)
    y = np.asarray(ys, dtype=float)
    beta = np.array([0.0, 0.0])  # [intercept, slope]
    x_design = np.column_stack([np.ones_like(x), x])
    for _ in range(50):
        eta = x_design @ beta
        mu = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
        w = np.clip(mu * (1 - mu), 1e-9, None)
        gradient = x_design.T @ (y - mu)
        hessian = x_design.T @ (x_design * w[:, None])
        step = np.linalg.solve(hessian, gradient)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break
    return {"calibration_intercept": float(beta[0]), "calibration_slope": float(beta[1])}


def audit_block(ps, ys, next_returns=None):
    ps = np.asarray(ps, dtype=float)
    ys = np.asarray(ys, dtype=float)
    out = {
        "n": int(ps.size),
        "positive_rate": float(ys.mean()) if ps.size else float("nan"),
        "mean_probability": float(ps.mean()) if ps.size else float("nan"),
        "mean_label": float(ys.mean()) if ps.size else float("nan"),
        "brier": brier(ps, ys) if ps.size else float("nan"),
        "log_loss": log_loss(ps, ys) if ps.size else float("nan"),
        "ece": ece(ps, ys) if ps.size else float("nan"),
    }
    if ps.size:
        out.update(calibration_slope_intercept(ps, ys))
    if next_returns is not None:
        nr = np.asarray(next_returns, dtype=float)
        out["mean_next_return"] = float(nr.mean()) if nr.size else float("nan")
    return out


# --------------------------------------------------------------------------
# calibration methods (fit on discovery, apply to validation)
# --------------------------------------------------------------------------

def fit_platt(ps, ys):
    """Platt scaling: logistic (a, b) on logit(p); returns an apply closure."""
    x = _logit(ps)
    y = np.asarray(ys, dtype=float)
    beta = np.array([0.0, 1.0])  # [intercept, slope]
    x_design = np.column_stack([np.ones_like(x), x])
    for _ in range(50):
        eta = x_design @ beta
        mu = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
        w = np.clip(mu * (1 - mu), 1e-9, None)
        gradient = x_design.T @ (y - mu)
        hessian = x_design.T @ (x_design * w[:, None])
        step = np.linalg.solve(hessian, gradient)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break
    a, b = float(beta[0]), float(beta[1])

    def apply_platt(p_new):
        return 1.0 / (1.0 + np.exp(-np.clip(a + b * _logit(p_new), -30, 30)))

    return {"apply": apply_platt, "intercept": a, "slope": b}


def fit_isotonic(ps, ys):
    """PAVA isotonic regression on (p, y); step-function predict."""
    order = np.argsort(np.asarray(ps, dtype=float), kind="stable")
    ys_sorted = np.asarray(ys, dtype=float)[order]
    p_sorted = np.asarray(ps, dtype=float)[order]
    # blocks: [weight, sum, value]
    blocks = [[1.0, ys_sorted[0], ys_sorted[0]]]
    for value in ys_sorted[1:]:
        blocks.append([1.0, value, value])
        while len(blocks) >= 2 and blocks[-2][2] > blocks[-1][2]:
            w2, s2, _ = blocks.pop()
            w1, s1, _ = blocks.pop()
            blocks.append([w1 + w2, s1 + s2, (s1 + s2) / (w1 + w2)])
    fitted = np.concatenate([np.full(int(round(b[0])), b[2]) for b in blocks])
    assert fitted.size == p_sorted.size

    def apply_isotonic(p_new):
        idx = np.searchsorted(p_sorted, np.asarray(p_new, dtype=float), side="right") - 1
        idx = np.clip(idx, 0, fitted.size - 1)
        return fitted[idx]

    return {"apply": apply_isotonic, "train_min": float(p_sorted[0]),
            "train_max": float(p_sorted[-1])}


# --------------------------------------------------------------------------
# tasks
# --------------------------------------------------------------------------

def _baseline_rows(audit) -> list[dict]:
    return [r for r in audit["predictions"] if r["variant"] == "baseline"]


def _slices(rows) -> dict[str, list[dict]]:
    times = sorted({r["decision_time"] for r in rows})
    thirds = len(times) // 3
    first = set(times[:thirds])
    middle = set(times[thirds:2 * thirds])
    slices = {
        "all": rows,
        "discovery": [r for r in rows if r["decision_time"][:10] < SPLIT_DATE],
        "validation": [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE],
        "first_third": [r for r in rows if r["decision_time"] in first],
        "middle_third": [r for r in rows if r["decision_time"] in middle],
        "last_third": [r for r in rows if r["decision_time"] not in first | middle],
    }
    for year in sorted({r["decision_time"][:4] for r in rows}):
        slices[f"year_{year}"] = [r for r in rows if r["decision_time"][:4] == year]
    return slices


def _next_return_map(audit) -> dict[tuple[str, str], float]:
    out = {}
    for symbol, per_day in audit["factors"].items():
        for decision_time, entry in per_day.items():
            out[(symbol, decision_time)] = entry.get("next_return")
    return out


def _write(out_dir: Path, name: str, payload: dict, md: str | None = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(
        json.dumps(payload, sort_keys=True, indent=1), encoding="utf-8"
    )
    if md is not None:
        (out_dir / f"{name}.md").write_text(md, encoding="utf-8", newline="\n")
    if md:
        print(md)


def _md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def task_probability_audit(rows, out_dir: Path, next_returns):
    slices = _slices(rows)
    payload = {"split_date": SPLIT_DATE, "windows": {}}
    md_rows = []
    for name, subset in slices.items():
        ps = [r["p"] for r in subset]
        ys = [r["y"] for r in subset]
        nrs = [next_returns.get((r["symbol"], r["decision_time"])) for r in subset]
        block = audit_block(ps, ys, next_returns=nrs)
        payload["windows"][name] = block
        md_rows.append([
            name, block["n"], f"{block['mean_probability']:.4f}",
            f"{block['positive_rate']:.4f}", f"{block['brier']:.5f}",
            f"{block['log_loss']:.5f}", f"{block['ece']:.5f}",
            f"{block.get('calibration_intercept', float('nan')):+.4f}",
            f"{block.get('calibration_slope', float('nan')):+.4f}",
        ])
    md = (
        f"# P13-Q T1/T4: raw probability audit (split_date={SPLIT_DATE})\n\n"
        "Strictly OOS walk-forward probabilities; slope/intercept from a "
        "logistic fit of the label on logit(p) within each window.\n\n"
        + _md_table(
            ["window", "N", "mean_p", "pos_rate", "brier", "logloss", "ece",
             "intercept", "slope"],
            md_rows,
        )
    )
    _write(out_dir, "probability_audit", payload, md)
    return payload


def task_calibration_curve(rows, out_dir: Path):
    ps = [r["p"] for r in rows]
    ys = [r["y"] for r in rows]
    table = bucket_stats(ps, ys)
    payload = {
        "bin_edges": BIN_EDGES,
        "note": "edges fixed a priori (0.05 grid); left-closed, last bucket closed",
        "buckets": table,
    }
    md_rows = [
        [b["bin"], b["n"],
         f"{b['mean_p']:.4f}" if b["mean_p"] is not None else "-",
         f"{b['observed_rate']:.4f}" if b["observed_rate"] is not None else "-",
         f"{b['difference']:+.4f}" if b["difference"] is not None else "-"]
        for b in table
    ]
    md = (
        "# P13-Q T2: reliability curve (fixed 0.05 bins)\n\n"
        + _md_table(["bin", "n", "mean_p", "observed", "difference"], md_rows)
    )
    _write(out_dir, "calibration_curve", payload, md)
    return payload


def task_bucket_stability(rows, out_dir: Path, next_returns):
    slices = _slices(rows)
    payload = {"bin_edges": BIN_EDGES, "windows": {}}
    for name, subset in slices.items():
        ps = [r["p"] for r in subset]
        ys = [r["y"] for r in subset]
        nrs = [next_returns.get((r["symbol"], r["decision_time"])) for r in subset]
        payload["windows"][name] = bucket_stats(ps, ys, next_returns=nrs)
    key_windows = ("all", "discovery", "validation")
    md_rows = []
    for name in key_windows:
        for b in payload["windows"][name]:
            if b["n"] == 0:
                continue
            md_rows.append([
                name, b["bin"], b["n"],
                f"{b['mean_p']:.4f}", f"{b['observed_rate']:.4f}",
                f"{b['calibration_error']:.4f}",
                f"{b.get('mean_next_return', float('nan')):+.5f}",
            ])
    md = (
        "# P13-Q T3: bucket stability on fixed bins (all/discovery/validation)\n\n"
        "Full per-year bucket tables are in the JSON artifact.\n\n"
        + _md_table(
            ["window", "bin", "N", "mean_p", "observed", "calib_err", "mean_next_ret"],
            md_rows,
        )
    )
    _write(out_dir, "bucket_stability", payload, md)
    return payload


def task_diagnostics(rows, out_dir: Path):
    ps = np.asarray([r["p"] for r in rows], dtype=float)
    table = bucket_stats(ps, [0] * ps.size)
    payload = {
        "n": int(ps.size),
        "histogram": [{"bin": b["bin"], "n": b["n"],
                       "frequency": b["n"] / ps.size} for b in table],
        "prediction_entropy": entropy(ps),
        "extreme_low_lt_0p1": {"n": int((ps < 0.1).sum()),
                               "frequency": float((ps < 0.1).mean())},
        "extreme_high_gt_0p9": {"n": int((ps > 0.9).sum()),
                                "frequency": float((ps > 0.9).mean())},
        "near_half_0p45_to_0p55": {"n": int(((ps >= 0.45) & (ps <= 0.55)).sum()),
                                   "frequency": float(((ps >= 0.45) & (ps <= 0.55)).mean())},
        "note": "descriptive only; no probability is adjusted here",
    }
    md_rows = [[h["bin"], h["n"], f"{h['frequency']:.4f}"] for h in payload["histogram"]]
    md = (
        f"# P13-Q probability quality diagnostics (N={payload['n']})\n\n"
        f"- prediction entropy (mean, nats): {payload['prediction_entropy']:.4f}\n"
        f"- extreme low (<0.10): {payload['extreme_low_lt_0p1']['n']} "
        f"({payload['extreme_low_lt_0p1']['frequency']:.4%})\n"
        f"- extreme high (>0.90): {payload['extreme_high_gt_0p9']['n']} "
        f"({payload['extreme_high_gt_0p9']['frequency']:.4%})\n"
        f"- near 0.50 ([0.45,0.55]): {payload['near_half_0p45_to_0p55']['n']} "
        f"({payload['near_half_0p45_to_0p55']['frequency']:.4%})\n\n"
        + _md_table(["bin", "n", "frequency"], md_rows)
    )
    _write(out_dir, "probability_diagnostics", payload, md)
    return payload


METHODS = ("raw", "platt", "isotonic")


def _evaluate_methods(rows, fit_rows, next_returns):
    """Fit every method on fit_rows and evaluate on rows (identical set)."""
    ps_fit = np.asarray([r["p"] for r in fit_rows], dtype=float)
    ys_fit = np.asarray([r["y"] for r in fit_rows], dtype=float)
    ps = np.asarray([r["p"] for r in rows], dtype=float)
    ys = np.asarray([r["y"] for r in rows], dtype=float)
    fitted = {}
    outputs = {"raw": ps}
    fitted["platt"] = fit_platt(ps_fit, ys_fit)
    outputs["platt"] = fitted["platt"]["apply"](ps)
    fitted["isotonic"] = fit_isotonic(ps_fit, ys_fit)
    outputs["isotonic"] = fitted["isotonic"]["apply"](ps)

    payload = {"methods": {}, "training_n": int(ps_fit.size), "evaluation_n": int(ps.size)}
    for method in METHODS:
        block = audit_block(outputs[method], ys)
        payload["methods"][method] = block
    for method in ("platt", "isotonic"):
        raw = payload["methods"]["raw"]
        mod = payload["methods"][method]
        mod["delta_brier"] = mod["brier"] - raw["brier"]
        mod["delta_log_loss"] = mod["log_loss"] - raw["log_loss"]
        mod["delta_ece"] = mod["ece"] - raw["ece"]
    payload["_fitted"] = fitted
    payload["_outputs"] = outputs
    payload["_ys"] = ys
    payload["_symbols"] = [r["symbol"] for r in rows]
    return payload


def _bootstrap_deltas(payload):
    ys = np.asarray(payload["_ys"])
    symbols = np.asarray(payload["_symbols"])
    outputs = payload["_outputs"]
    order = np.argsort(symbols, kind="stable")
    symbols_sorted = symbols[order]
    boundaries = np.flatnonzero(np.r_[True, symbols_sorted[1:] != symbols_sorted[:-1], True])
    clusters = [
        order[boundaries[i]:boundaries[i + 1]] for i in range(len(boundaries) - 1)
    ]
    rng = np.random.default_rng(SEED)
    metrics = ("delta_brier", "delta_log_loss", "delta_ece")
    samples = {f"{method}:{metric}": [] for method in ("platt", "isotonic")
               for metric in metrics}
    for _ in range(BOOTSTRAP_ROUNDS):
        pick = rng.integers(0, len(clusters), len(clusters))
        idx = np.concatenate([clusters[i] for i in pick])
        ys_b = ys[idx]
        raw_ps = outputs["raw"][idx]
        raw = {"brier": brier(raw_ps, ys_b), "log_loss": log_loss(raw_ps, ys_b),
               "ece": ece(raw_ps, ys_b)}
        for method in ("platt", "isotonic"):
            ps_m = outputs[method][idx]
            mod = {"brier": brier(ps_m, ys_b), "log_loss": log_loss(ps_m, ys_b),
                   "ece": ece(ps_m, ys_b)}
            for metric in metrics:
                key = metric.removeprefix("delta_")
                samples[f"{method}:{metric}"].append(mod[key] - raw[key])
    result = {}
    for key, values in samples.items():
        method, metric = key.split(":", 1)
        point = payload["methods"][method][metric]
        result[key] = {
            "point": point,
            "ci95_low": float(np.quantile(values, 0.025)),
            "ci95_high": float(np.quantile(values, 0.975)),
        }
    return result


def task_calibration_methods(rows, out_dir: Path):
    discovery = [r for r in rows if r["decision_time"][:10] < SPLIT_DATE]
    validation = [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE]
    payload = _evaluate_methods(validation, discovery, None)
    payload["training_period"] = f"discovery OOS (decision_time < {SPLIT_DATE})"
    payload["evaluation_period"] = f"validation OOS (decision_time >= {SPLIT_DATE})"
    payload["rows_aligned"] = (
        [r["decision_time"] for r in discovery] is not None
        and all(r["decision_time"][:10] >= SPLIT_DATE for r in validation)
    )
    payload["bootstrap"] = _bootstrap_deltas(payload)
    payload["fitted_parameters"] = {
        "platt": {"intercept": payload["_fitted"]["platt"]["intercept"],
                  "slope": payload["_fitted"]["platt"]["slope"]},
        "isotonic": {"train_min": payload["_fitted"]["isotonic"]["train_min"],
                     "train_max": payload["_fitted"]["isotonic"]["train_max"]},
    }

    md_rows = []
    for method in METHODS:
        m = payload["methods"][method]
        md_rows.append([
            method, m["n"], f"{m['brier']:.5f}", f"{m['log_loss']:.5f}",
            f"{m['ece']:.5f}",
            f"{m.get('calibration_intercept', float('nan')):+.4f}",
            f"{m.get('calibration_slope', float('nan')):+.4f}",
        ])
    bs = payload["bootstrap"]
    boot_rows = []
    for key in sorted(bs):
        e = bs[key]
        boot_rows.append([
            key, f"{e['point']:+.5f}", f"[{e['ci95_low']:+.5f}, {e['ci95_high']:+.5f}]",
        ])
    md = (
        f"# P13-Q T5/T6: calibration methods "
        f"(fit: {payload['training_period']}; evaluate: {payload['evaluation_period']})\n\n"
        + _md_table(
            ["method", "N", "brier", "logloss", "ece", "intercept", "slope"], md_rows,
        )
        + "\n\n## Δ vs raw (negative = improvement), symbol-clustered bootstrap "
          f"(B={BOOTSTRAP_ROUNDS}, seed={SEED})\n\n"
        + _md_table(["method:metric", "point", "ci95"], boot_rows)
    )
    payload_for_write = {
        k: v for k, v in payload.items()
        if k not in ("_fitted", "_outputs", "_ys", "_symbols")
    }
    _write(out_dir, "calibration_methods", payload_for_write, md)
    return payload


def task_registry(methods_payload, out_dir: Path):
    statuses = {method: "research_only" for method in METHODS}
    registry = {
        "generated_for": "P13-Q",
        "split_date": SPLIT_DATE,
        "status_rule": (
            "research_only by design: P13-O consumed the full history, so the "
            "calibration evaluation window is not a virgin holdout; statuses "
            "may be revisited only on genuinely future data"
        ),
        "methods": {},
    }
    for method in METHODS:
        m = methods_payload["methods"][method]
        registry["methods"][method] = {
            "method": method,
            "role": (
                "production_baseline_probability" if method == "raw"
                else "post_hoc_calibration_research"
            ),
            "training_period": (
                "production walk-forward (protocol 252/20/20/1)" if method == "raw"
                else methods_payload["training_period"]
            ),
            "evaluation_period": methods_payload["evaluation_period"],
            "n_training": (
                methods_payload["training_n"] if method != "raw"
                else None
            ),
            "n_evaluation": methods_payload["evaluation_n"],
            "brier": m["brier"],
            "logloss": m["log_loss"],
            "ece": m["ece"],
            "calibration_intercept": m.get("calibration_intercept"),
            "calibration_slope": m.get("calibration_slope"),
            "delta_brier": m.get("delta_brier"),
            "delta_logloss": m.get("delta_log_loss"),
            "delta_ece": m.get("delta_ece"),
            "status": statuses[method],
        }
    (out_dir / "calibration_registry.json").write_text(
        json.dumps(registry, sort_keys=True, indent=1), encoding="utf-8"
    )
    print(f"calibration_registry_written={out_dir / 'calibration_registry.json'}")
    return registry


def task_manifest(out_dir: Path):
    manifest = {}
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        data = path.read_bytes()
        manifest[path.name] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
    payload = {"files": manifest}
    (out_dir / "manifest.json").write_text(
        json.dumps(payload, sort_keys=True, indent=1), encoding="utf-8"
    )
    print(f"manifest_written={out_dir / 'manifest.json'} ({len(manifest)} files)")
    return payload


TASKS = ("audit", "curve", "buckets", "diagnostics", "methods", "registry", "manifest", "all")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True,
                        help="P13-O predictions JSON (with .meta.json beside it)")
    parser.add_argument("--out-dir", default="data/industry/p13q")
    parser.add_argument("task", choices=TASKS)
    args = parser.parse_args()

    with open(args.audit, encoding="utf-8") as f:
        audit = json.load(f)
    with open(args.audit.replace(".json", ".meta.json"), encoding="utf-8") as f:
        audit["meta"] = json.load(f)
    assert_research_zone([r["decision_time"] for r in audit["predictions"]])
    rows = _baseline_rows(audit)
    next_returns = _next_return_map(audit)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.task in ("audit", "all"):
        task_probability_audit(rows, out_dir, next_returns)
    if args.task in ("curve", "all"):
        task_calibration_curve(rows, out_dir)
    if args.task in ("buckets", "all"):
        task_bucket_stability(rows, out_dir, next_returns)
    if args.task in ("diagnostics", "all"):
        task_diagnostics(rows, out_dir)
    methods_payload = None
    if args.task in ("methods", "all"):
        methods_payload = task_calibration_methods(rows, out_dir)
    if args.task in ("registry", "all"):
        if methods_payload is None:
            loaded = json.loads((out_dir / "calibration_methods.json").read_text(encoding="utf-8"))
            methods_payload = _evaluate_methods(
                [r for r in rows if r["decision_time"][:10] >= SPLIT_DATE],
                [r for r in rows if r["decision_time"][:10] < SPLIT_DATE],
                None,
            )
            # keep loaded window metrics for consistency with the artifact
            methods_payload["methods"] = loaded["methods"]
        task_registry(methods_payload, out_dir)
    if args.task == "all":
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        config = {
            "git_commit": commit,
            "seed": SEED,
            "bootstrap_rounds": BOOTSTRAP_ROUNDS,
            "split_date": SPLIT_DATE,
            "protocol": {"train_size": 252, "test_size": 20, "step": 20, "gap": 1},
            "universe_size": len(audit["meta"]["universe"]),
            "factor_list": ["momentum", "volatility", "trend", "volume_ratio",
                            "industry_relative_return_5", "industry_relative_return_20"],
            "calibration_methods": list(METHODS),
            "probability_bins": BIN_EDGES,
            "audit_file": args.audit,
        }
        (out_dir / "analysis_config.json").write_text(
            json.dumps(config, sort_keys=True, indent=1), encoding="utf-8"
        )
        print(f"analysis_config_written={out_dir / 'analysis_config.json'}")
        task_manifest(out_dir)


if __name__ == "__main__":
    main()
