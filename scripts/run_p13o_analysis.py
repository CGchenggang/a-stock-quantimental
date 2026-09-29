"""P13-O factor stability analysis over exported OOS predictions.

All analyses consume the audit JSON produced by
run_local_industry_relative_oos.py --predictions-out. Nothing here mutates
the production pipeline: every metric is computed on exactly the OOS
prediction rows the runner summarizes, and every slice reports N.

Subcommands: time symbol industry quantiles regime cost bootstrap all
Each writes data/industry/p13o/<name>.{json,md} and prints a short summary.
`all` also records analysis_config.json (commit, seed, protocol, inputs).

Research conventions fixed before looking at any sliced result:
- metrics: accuracy = mean((p >= 0.5) == y); brier/log-loss as in the runner.
- every factor-vs-baseline delta is computed on the identical OOS row set
  (baseline probability is carried per row), so deltas never mix samples.
- PIT industry attribution uses the same PIT schedule lookup as the factor.
- regime labels only use returns available at or before the decision time.
- bootstrap: symbol-clustered resampling, seed 20260929, B=1000.
- cost model: 10 bp per unit turnover, next-day close-to-close execution.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from math import log
from pathlib import Path

import numpy as np

SEED = 20260929
BOOTSTRAP_ROUNDS = 1000
COST_RATE = 0.001  # 10 bp per unit turnover, one side
REGIME_WINDOW = 20
REGIME_UP = 0.03   # prior thresholds, fixed before slicing (see report)
REGIME_DOWN = -0.03

FACTOR_NAMES = (
    "momentum", "volatility", "trend", "volume_ratio",
    "industry_relative_return_5", "industry_relative_return_20",
)


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


def block(rows, p_key="p", base_key="baseline_p"):
    """Metrics of one row set plus paired baseline deltas."""
    ps = [r[p_key] for r in rows]
    bs = [r[base_key] for r in rows]
    ys = [r["y"] for r in rows]
    acc, br, ll = accuracy(ps, ys), brier(ps, ys), log_loss(ps, ys)
    bacc, bbr, bll = accuracy(bs, ys), brier(bs, ys), log_loss(bs, ys)
    return {
        "n": len(rows),
        "accuracy": acc, "brier": br, "log_loss": ll,
        "mean_p": sum(ps) / len(ps) if ps else float("nan"),
        "positive_rate": sum(ys) / len(ys) if ys else float("nan"),
        "baseline_accuracy": bacc, "baseline_brier": bbr, "baseline_log_loss": bll,
        "delta_accuracy": acc - bacc if rows else float("nan"),
        "delta_brier": br - bbr if rows else float("nan"),
        "delta_log_loss": ll - bll if rows else float("nan"),
    }


def _write(out_dir: Path, name: str, payload: dict, md: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.json").write_text(
        json.dumps(payload, sort_keys=True, indent=1), encoding="utf-8"
    )
    (out_dir / f"{name}.md").write_text(md, encoding="utf-8", newline="\n")
    print(md)


def _md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


def _quantiles(values, qs=(0.1, 0.25, 0.5, 0.75, 0.9)):
    if not values:
        return {q: float("nan") for q in qs}
    arr = np.sort(np.asarray(values, dtype=float))
    return {q: float(np.quantile(arr, q)) for q in qs}


# --------------------------------------------------------------------------
# P13-O3: PIT-safe industry attribution (same lookup as the factor itself)
# --------------------------------------------------------------------------

class IndustryAttributor:
    def __init__(self, membership_path: str):
        from astock_v2.industry_loader import load_industry_memberships
        from astock_v2.industry_relative import _membership_schedule

        memberships = load_industry_memberships(membership_path)
        self._schedules = {}
        for m in memberships:
            self._schedules.setdefault(m.symbol, []).append(m)
        self._schedules = {
            symbol: _membership_schedule(items)
            for symbol, items in self._schedules.items()
        }
        self._cache: dict[tuple[str, str], str | None] = {}

    def industry(self, symbol: str, decision_time: str) -> str | None:
        key = (symbol, decision_time)
        if key in self._cache:
            return self._cache[key]
        from astock_v2.industry_relative import _scheduled_industry, _parse_aware

        schedule = self._schedules.get(symbol)
        code = None
        if schedule is not None:
            membership = _scheduled_industry(
                schedule, decision_time[:10], _parse_aware(decision_time)
            )
            if membership is not None:
                code = membership.industry_code
        self._cache[key] = code
        return code


# --------------------------------------------------------------------------
# P13-O5: minimal PIT-safe market regime label
# --------------------------------------------------------------------------

class RegimeLabeler:
    """Equal-weight universe index regime, fixed +/-3% 20-day window.

    The label for decision day t uses only index returns of trading days
    before t (their available_time is the same day 16:00, which is at or
    before t's 16:00 boundary for t-1 and earlier). Thresholds are fixed
    priors, not fitted on the OOS sample.
    """

    def __init__(self, store, universe: tuple[str, ...]):
        from astock_v2.industry_relative import _build_pit_return_state, _advance_pit_return_state

        records = {
            symbol: store.read_records("cn_stock_daily", symbol)
            for symbol in universe
        }
        state = _build_pit_return_state(records)
        days = sorted({r.event_time[:10] for rows in records.values() for r in rows})
        daily = {}
        for day in days:
            decision = f"{day}T16:00:00+08:00"
            _advance_pit_return_state(state, decision)
            vals = [item["returns"].get(day) for item in state.values()]
            vals = [v for v in vals if v is not None]
            if vals:
                daily[day] = sum(vals) / len(vals)
        # cumulative 20-day window ending at each day (inclusive of that day)
        ordered = sorted(daily)
        cum = {}
        for pos, day in enumerate(ordered):
            window = ordered[max(0, pos - REGIME_WINDOW + 1): pos + 1]
            cum[day] = float(np.prod([1.0 + daily[d] for d in window]) - 1.0)
        # label for decision day t uses the window through t-1 only
        self._label_by_day: dict[str, str] = {"": "NO_DATA"}
        for pos, day in enumerate(ordered):
            if pos == 0:
                self._label_by_day[day] = "NO_DATA"
                continue
            window_cum = cum[ordered[pos - 1]]
            if window_cum > REGIME_UP:
                self._label_by_day[day] = "BULL"
            elif window_cum < REGIME_DOWN:
                self._label_by_day[day] = "BEAR"
            else:
                self._label_by_day[day] = "NEUTRAL"

    def regime(self, decision_time: str) -> str:
        return self._label_by_day.get(decision_time[:10], "NO_DATA")


# --------------------------------------------------------------------------
# Analyses
# --------------------------------------------------------------------------

def analyze_time(audit, out_dir, args):
    """P13-O1: slice OOS predictions by time."""
    times = sorted({r["decision_time"] for r in audit["predictions"]})
    variants = sorted({r["variant"] for r in audit["predictions"]})

    def slice_rows(rows, pred):
        return [r for r in rows if pred(r["decision_time"])]

    thirds = len(times) // 3
    boundaries = set(times[:thirds]) | set(times[thirds:2 * thirds])
    cutoff_2y = (datetime.fromisoformat(times[-1][:10]) - timedelta(days=730)).isoformat()

    slices = {
        "all": lambda t: True,
        "first_third": lambda t: t in set(times[:thirds]),
        "middle_third": lambda t: t in set(times[thirds:2 * thirds]),
        "last_third": lambda t: t not in boundaries,
        "last_2_years": lambda t: t[:10] >= cutoff_2y,
    }
    years = sorted({t[:4] for t in times})
    for year in years:
        slices[f"year_{year}"] = lambda t, y=year: t[:4] == y

    payload = {"slices": {}}
    md_rows = []
    for name, pred in slices.items():
        by_variant = {}
        for variant in variants:
            rows = [r for r in audit["predictions"] if r["variant"] == variant]
            rows = slice_rows(rows, pred)
            by_variant[variant] = block(rows)
        payload["slices"][name] = by_variant
        for variant in variants:
            m = by_variant[variant]
            md_rows.append([
                name, variant, m["n"], f"{m['accuracy']:.4f}", f"{m['brier']:.4f}",
                f"{m['log_loss']:.4f}", f"{m['mean_p']:.4f}", f"{m['positive_rate']:.4f}",
                f"{m['delta_accuracy']:+.4f}", f"{m['delta_brier']:+.5f}",
                f"{m['delta_log_loss']:+.5f}",
            ])
    md = (
        "# P13-O1 Time stability\n\n"
        "OOS predictions of the 76-stock run sliced by decision time. "
        "Deltas are factor minus baseline on the identical row set.\n\n"
        + _md_table(
            ["slice", "variant", "N", "acc", "brier", "logloss",
             "mean_p", "pos_rate", "d_acc", "d_brier", "d_logloss"],
            md_rows,
        )
    )
    _write(out_dir, "time_stability", payload, md)


def analyze_symbol(audit, out_dir, args):
    """P13-O2: per-symbol factor vs baseline deltas and their distribution."""
    variants = sorted({r["variant"] for r in audit["predictions"]})
    payload = {"variants": {}}
    for variant in variants:
        rows = [r for r in audit["predictions"] if r["variant"] == variant]
        by_symbol = defaultdict(list)
        for r in rows:
            by_symbol[r["symbol"]].append(r)
        per_symbol = {
            symbol: block(symbol_rows)
            for symbol, symbol_rows in sorted(by_symbol.items())
        }
        d_acc = [m["delta_accuracy"] for m in per_symbol.values()]
        d_brier = [m["delta_brier"] for m in per_symbol.values()]
        d_ll = [m["delta_log_loss"] for m in per_symbol.values()]
        summary = {
            "n_symbols": len(per_symbol),
            "improved_accuracy": sum(d > 0 for d in d_acc),
            "degraded_accuracy": sum(d < 0 for d in d_acc),
            "delta_accuracy": {
                "mean": float(np.mean(d_acc)), "median": float(np.median(d_acc)),
                **{f"q{int(q * 100)}": v for q, v in _quantiles(d_acc).items()},
            },
            "delta_brier": {
                "mean": float(np.mean(d_brier)), "median": float(np.median(d_brier)),
                **{f"q{int(q * 100)}": v for q, v in _quantiles(d_brier).items()},
            },
            "delta_log_loss": {
                "mean": float(np.mean(d_ll)), "median": float(np.median(d_ll)),
                **{f"q{int(q * 100)}": v for q, v in _quantiles(d_ll).items()},
            },
        }
        payload["variants"][variant] = {"summary": summary, "per_symbol": per_symbol}

    md_rows = []
    for variant in variants:
        s = payload["variants"][variant]["summary"]
        da = s["delta_accuracy"]
        md_rows.append([
            variant, s["n_symbols"], s["improved_accuracy"], s["degraded_accuracy"],
            f"{da['mean']:+.4f}", f"{da['median']:+.4f}",
            f"{da['q10']:+.4f}", f"{da['q25']:+.4f}", f"{da['q75']:+.4f}", f"{da['q90']:+.4f}",
        ])
    md = (
        "# P13-O2 Symbol stability\n\n"
        "Per-symbol OOS deltas (factor minus baseline, identical rows). "
        "The full per-symbol table is in the JSON artifact.\n\n"
        + _md_table(
            ["variant", "symbols", "improved", "degraded",
             "d_acc_mean", "d_acc_median", "q10", "q25", "q75", "q90"],
            md_rows,
        )
    )
    _write(out_dir, "symbol_stability", payload, md)


def analyze_industry(audit, out_dir, args):
    """P13-O3: PIT-safe SW1 industry attribution of every OOS row."""
    attributor = IndustryAttributor(args.membership)
    variants = sorted({r["variant"] for r in audit["predictions"]})
    skipped = 0
    enriched = defaultdict(lambda: defaultdict(list))
    for r in audit["predictions"]:
        code = attributor.industry(r["symbol"], r["decision_time"])
        if code is None:
            skipped += 1
            continue
        enriched[r["variant"]][code].append(r)

    payload = {"skipped_no_pit_membership": skipped, "industries": {}}
    md_rows = []
    for variant in variants:
        payload["industries"][variant] = {}
        for code in sorted(enriched[variant]):
            m = block(enriched[variant][code])
            payload["industries"][variant][code] = m
            if variant == "industry_5_20":
                md_rows.append([
                    code, m["n"], f"{m['accuracy']:.4f}", f"{m['brier']:.4f}",
                    f"{m['log_loss']:.4f}", f"{m['delta_accuracy']:+.4f}",
                    f"{m['delta_brier']:+.5f}", f"{m['delta_log_loss']:+.5f}",
                ])
    md = (
        "# P13-O3 Industry stability (PIT-safe SW1)\n\n"
        "Industry attribution uses the PIT schedule lookup of the factor "
        "itself at each decision time; rows without an admissible membership "
        f"are not classified (skipped={skipped}). Table shows industry_5_20.\n\n"
        + _md_table(
            ["industry", "N", "acc", "brier", "logloss", "d_acc", "d_brier", "d_logloss"],
            md_rows,
        )
    )
    _write(out_dir, "industry_stability", payload, md)


def analyze_quantiles(audit, out_dir, args):
    """P13-O4: factor value quintiles vs realized next-day outcome."""
    rows = [r for r in audit["predictions"] if r["variant"] == "baseline"]
    factors = audit["factors"]
    payload = {"factors": {}}
    for factor in FACTOR_NAMES:
        enriched = []
        for r in rows:
            value = factors.get(r["symbol"], {}).get(r["decision_time"], {}).get(factor)
            if value is None:
                continue
            nr = factors[r["symbol"]][r["decision_time"]].get("next_return")
            enriched.append((value, r["y"], nr))
        if not enriched:
            payload["factors"][factor] = {"n": 0}
            continue
        values = np.array([e[0] for e in enriched], dtype=float)
        edges = np.quantile(values, [0.2, 0.4, 0.6, 0.8])
        groups = [[] for _ in range(5)]
        for value, y, nr in enriched:
            q = int(np.searchsorted(edges, value, side="right"))
            groups[q].append((value, y, nr))
        payload["factors"][factor] = {"n": len(enriched), "quintiles": []}
        for q, group in enumerate(groups, start=1):
            if not group:
                continue
            ups = [y for _, y, _ in group]
            rets = [nr for _, _, nr in group if nr is not None]
            payload["factors"][factor]["quintiles"].append({
                "quintile": q, "n": len(group),
                "mean_factor": float(np.mean([g[0] for g in group])),
                "up_rate": float(np.mean(ups)) if ups else float("nan"),
                "mean_next_return": float(np.mean(rets)) if rets else float("nan"),
            })
    md_rows = []
    for factor in FACTOR_NAMES:
        entry = payload["factors"][factor]
        for q in entry.get("quintiles", []):
            md_rows.append([
                factor, q["quintile"], q["n"], f"{q['mean_factor']:.5f}",
                f"{q['up_rate']:.4f}", f"{q['mean_next_return']:+.5f}",
            ])
    md = (
        "# P13-O4 Factor quintiles (OOS rows, equal-frequency cuts)\n\n"
        "Quintile edges are computed within the OOS sample of each factor; "
        "this is a descriptive monotonicity check, not a traded portfolio.\n\n"
        + _md_table(
            ["factor", "q", "N", "mean_factor", "up_rate", "mean_next_return"],
            md_rows,
        )
    )
    _write(out_dir, "factor_quantiles", payload, md)


def analyze_regime(audit, out_dir, args):
    """P13-O5: factor performance conditioned on a PIT-safe regime label."""
    from astock_v2.data.local_store import LocalHistoricalStore

    store = LocalHistoricalStore(args.root)
    universe = tuple(audit["meta"]["universe"])
    labeler = RegimeLabeler(store, universe)
    variants = sorted({r["variant"] for r in audit["predictions"]})

    buckets = defaultdict(lambda: defaultdict(list))
    no_data = 0
    for r in audit["predictions"]:
        label = labeler.regime(r["decision_time"])
        if label == "NO_DATA":
            no_data += 1
            continue
        buckets[label][r["variant"]].append(r)

    payload = {
        "definition": {
            "index": "equal-weight universe daily-return index (PIT state)",
            "window_days": REGIME_WINDOW,
            "bull_threshold": REGIME_UP, "bear_threshold": REGIME_DOWN,
            "uses": "returns through t-1 only; thresholds fixed a priori",
        },
        "rows_without_regime": no_data,
        "regimes": {},
    }
    md_rows = []
    for regime in ("BULL", "NEUTRAL", "BEAR"):
        payload["regimes"][regime] = {}
        for variant in variants:
            rows = buckets[regime][variant]
            m = block(rows)
            payload["regimes"][regime][variant] = m
            md_rows.append([
                regime, variant, m["n"], f"{m['accuracy']:.4f}",
                f"{m['brier']:.4f}", f"{m['log_loss']:.4f}",
                f"{m['delta_accuracy']:+.4f}", f"{m['delta_brier']:+.5f}",
            ])
    md = (
        "# P13-O5 Regime-conditioned performance\n\n"
        "Regime = equal-weight universe index 20-day cumulative return through "
        "t-1 (PIT-safe); BULL > +3%, BEAR < -3%, else NEUTRAL. Thresholds are "
        "fixed priors. This is analysis only - no regime model is wired into "
        "prediction.\n\n"
        + _md_table(
            ["regime", "variant", "N", "acc", "brier", "logloss", "d_acc", "d_brier"],
            md_rows,
        )
    )
    _write(out_dir, "regime_analysis", payload, md)


def analyze_cost(audit, out_dir, args):
    """P13-O6: turnover and cost sensitivity of the threshold-0.5 signal."""
    variants = sorted({r["variant"] for r in audit["predictions"]})
    by_variant_symbol = defaultdict(lambda: defaultdict(list))
    for r in audit["predictions"]:
        by_variant_symbol[r["variant"]][r["symbol"]].append(r)

    def series_stats(rows):
        rows = sorted(rows, key=lambda r: r["decision_time"])
        positions = [1 if r["p"] >= 0.5 else 0 for r in rows]
        rets = []
        factors = audit["factors"]
        for r in rows:
            nr = factors.get(r["symbol"], {}).get(r["decision_time"], {}).get("next_return")
            rets.append(nr)
        gross, turnover, covered = 0.0, 0.0, 0
        previous = 0
        for pos, nr in zip(positions, rets):
            if nr is None:
                previous = pos
                continue
            gross += pos * nr
            turnover += abs(pos - previous)
            covered += 1
            previous = pos
        if not covered:
            return None
        cost = COST_RATE * turnover
        return {
            "n_days": covered,
            "gross_return_sum": gross / covered,
            "turnover_per_day": turnover / covered,
            "cost_per_day": cost / covered,
            "net_return_per_day": (gross - cost) / covered,
        }

    payload = {
        "assumptions": {
            "signal": "p >= 0.5 held one day, executed at the close",
            "return": "next_return = close(t+1)/close(t) - 1 (label definition)",
            "cost_rate_per_unit_turnover": COST_RATE,
            "turnover": "mean |position change| per day, first day included",
            "aggregation": "equal-weight mean across symbols; research estimate only",
        },
        "variants": {},
    }
    md_rows = []
    for variant in variants:
        stats = [
            s for s in (
                series_stats(rows) for rows in by_variant_symbol[variant].values()
            ) if s
        ]
        agg = {
            "n_symbols": len(stats),
            "gross_return_per_day": float(np.mean([s["gross_return_sum"] for s in stats])),
            "turnover_per_day": float(np.mean([s["turnover_per_day"] for s in stats])),
            "cost_per_day": float(np.mean([s["cost_per_day"] for s in stats])),
            "net_return_per_day": float(np.mean([s["net_return_per_day"] for s in stats])),
        }
        payload["variants"][variant] = agg
        md_rows.append([
            variant, agg["n_symbols"], f"{agg['gross_return_per_day']:+.5f}",
            f"{agg['turnover_per_day']:.4f}", f"{agg['cost_per_day']:+.5f}",
            f"{agg['net_return_per_day']:+.5f}",
        ])
    md = (
        "# P13-O6 Cost sensitivity (research estimate, not tradeable PnL)\n\n"
        "Signal p >= 0.5 held one day at the close; next_return as defined by "
        "the label; 10 bp per unit turnover.\n\n"
        + _md_table(
            ["variant", "symbols", "gross/day", "turnover/day", "cost/day", "net/day"],
            md_rows,
        )
    )
    _write(out_dir, "cost_sensitivity", payload, md)


def analyze_bootstrap(audit, out_dir, args):
    """P13-O7: symbol-clustered bootstrap of pooled factor-vs-baseline deltas."""
    variants = sorted({r["variant"] for r in audit["predictions"]})
    clusters = {
        variant: defaultdict(list) for variant in variants
    }
    for r in audit["predictions"]:
        clusters[r["variant"]][r["symbol"]].append(r)

    rng = np.random.default_rng(SEED)
    payload = {
        "method": {
            "unit": "symbol (cluster bootstrap, resample symbols with replacement)",
            "rounds": BOOTSTRAP_ROUNDS,
            "seed": SEED,
        },
        "variants": {},
    }
    md_rows = []
    for variant in variants:
        symbols = sorted(clusters[variant])
        if len(symbols) < 2:
            continue
        point_rows = [r for rows in clusters[variant].values() for r in rows]
        point = block(point_rows)
        samples = {"accuracy": [], "brier": [], "log_loss": []}
        for _ in range(BOOTSTRAP_ROUNDS):
            pick = rng.integers(0, len(symbols), len(symbols))
            rows = [r for i in pick for r in clusters[variant][symbols[i]]]
            m = block(rows)
            samples["accuracy"].append(m["delta_accuracy"])
            samples["brier"].append(m["delta_brier"])
            samples["log_loss"].append(m["delta_log_loss"])
        entry = {"point": point, "bootstrap": {}}
        for name, values in samples.items():
            entry["bootstrap"][name] = {
                "ci95_low": float(np.quantile(values, 0.025)),
                "ci95_high": float(np.quantile(values, 0.975)),
                "median": float(np.median(values)),
            }
        payload["variants"][variant] = entry
        md_rows.append([
            variant, f"{point['delta_accuracy']:+.4f}",
            f"[{entry['bootstrap']['accuracy']['ci95_low']:+.4f}, "
            f"{entry['bootstrap']['accuracy']['ci95_high']:+.4f}]",
            f"{point['delta_brier']:+.5f}",
            f"[{entry['bootstrap']['brier']['ci95_low']:+.5f}, "
            f"{entry['bootstrap']['brier']['ci95_high']:+.5f}]",
            f"{point['delta_log_loss']:+.5f}",
            f"[{entry['bootstrap']['log_loss']['ci95_low']:+.5f}, "
            f"{entry['bootstrap']['log_loss']['ci95_high']:+.5f}]",
        ])
    md = (
        f"# P13-O7 Clustered bootstrap (symbols with replacement, "
        f"B={BOOTSTRAP_ROUNDS}, seed={SEED})\n\n"
        "Point estimate is the pooled delta on all 76-stock OOS rows; the "
        "interval resamples symbols, preserving within-stock dependence.\n\n"
        + _md_table(
            ["variant", "d_acc", "acc CI95", "d_brier", "brier CI95",
             "d_logloss", "logloss CI95"],
            md_rows,
        )
    )
    _write(out_dir, "bootstrap", payload, md)


ANALYSES = {
    "time": analyze_time,
    "symbol": analyze_symbol,
    "industry": analyze_industry,
    "quantiles": analyze_quantiles,
    "regime": analyze_regime,
    "cost": analyze_cost,
    "bootstrap": analyze_bootstrap,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True,
                        help="predictions JSON from run_local_industry_relative_oos.py "
                             "--predictions-out")
    parser.add_argument("--out-dir", default="data/industry/p13o")
    parser.add_argument("--membership", required=True)
    parser.add_argument("--root", default="data")
    parser.add_argument("analysis", choices=[*ANALYSES, "all"])
    args = parser.parse_args()

    with open(args.audit, encoding="utf-8") as f:
        audit = json.load(f)
    with open(args.audit.replace(".json", ".meta.json"), encoding="utf-8") as f:
        audit["meta"] = json.load(f)

    if args.analysis == "all":
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        config = {
            "git_commit": commit,
            "seed": SEED,
            "bootstrap_rounds": BOOTSTRAP_ROUNDS,
            "cost_rate": COST_RATE,
            "regime": {"window": REGIME_WINDOW, "up": REGIME_UP, "down": REGIME_DOWN},
            "audit_file": args.audit,
            "membership": args.membership,
            "protocol": audit["meta"]["protocol"],
            "universe_size": len(audit["meta"]["universe"]),
        }
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "analysis_config.json").write_text(
            json.dumps(config, sort_keys=True, indent=1), encoding="utf-8"
        )
        for name, fn in ANALYSES.items():
            fn(audit, Path(args.out_dir), args)
        print(f"analysis_config_written={out_dir / 'analysis_config.json'}")
    else:
        ANALYSES[args.analysis](audit, Path(args.out_dir), args)


if __name__ == "__main__":
    main()
