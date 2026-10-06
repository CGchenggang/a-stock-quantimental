"""P13-O-FORWARD-MODEL-EXECUTION-001 — authorized forward-model executor.

Executes the Human-Authorized training under the FROZEN parameters
(docs/artifacts/P13-O-FORWARD-MODEL-HUMAN-AUTHORIZATION.md, FROZEN
record) and freezes ONE MODEL_APPLICATION artifact + ONE bound
CALIBRATION artifact. Protocol verbatim:

    unregularized binary logistic, full-batch GD, 500 epochs, lr 0.05,
    zero init, float64, stable sigmoid (clip +-30), no scaler,
    rows sorted by (decision_time, symbol), one row per (symbol,
    decision_time), missing-factor rows dropped, SINGLE FINAL MODEL
    fitted on the whole frozen training window.

Governance guards enforced here:
- frozen identity re-verified in-process (feature_set_id, scope sha256,
  definition blobs) — any mismatch exits non-zero (STOP);
- windows verbatim half-open with the frozen label-availability
  exclusions (last training decision date 2024-12-30, last calibration
  decision date 2025-06-30);
- data truncated to decision dates < virgin_start (2026-09-23) BEFORE
  any row assembly, plus a post-fit virgin scan;
- deterministic double-fit inside the executor (artifact bytes must be
  identical) — any difference exits non-zero (STOP);
- no validation data is loaded, no model selection, no hyperparameter
  search; the seed is manifest metadata only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.industry_relative import (
    build_universe_industry_relative_context_maps,
)
from astock_v2.local_pipeline import build_local_factor_rows
from astock_v2.model import forward_model as fm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_local_industry_relative_oos import (  # noqa: E402  (frozen blob)
    STOCK_FACTORS,
    _factor_rows,
)
from run_p13q_analysis import fit_platt  # noqa: E402  (accepted numerical protocol)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "artifacts" / "p13o-forward-model"

MODEL_FAMILY = "unregularized_binary_logistic"
FEATURE_NAMES = list(fm.FROZEN_FEATURE_NAMES)
VARIANT = fm.FROZEN_MODEL_VARIANT
UNIVERSE_FILE = ROOT / "data" / "industry" / "validation_universe_76.txt"
MEMBERSHIP = ROOT / "data" / "industry" / "sw_official_sw1_membership_all.csv"
SOURCE_COMMIT = "91382faf9cd57cc7d1641b6d2a9df9cfd74fa517"
SEED = 20260929
EPOCHS, LR = 500, 0.05
RESEARCH_END = "2026-09-22"
VIRGIN_START = "2026-09-23"
TRAIN_START, TRAIN_END = "2020-01-02", "2025-01-01"
CAL_START, CAL_END = "2025-01-01", "2025-07-01"
VAL_START, VAL_END = "2025-07-01", "2026-09-22"
TRAIN_LAST_DECISION = "2024-12-30"   # frozen label-availability exclusion
CAL_LAST_DECISION = "2025-06-30"


def _dd(decision_time: str) -> str:
    return decision_time[:10]


def stop(message: str) -> "None":
    print(f"STOP — {message}", file=sys.stderr)
    raise SystemExit(2)


def load_scope() -> tuple[list[str], str, str]:
    symbols = sorted({line.strip().zfill(6)
                      for line in UNIVERSE_FILE.read_text(encoding="utf-8-sig").splitlines()
                      if line.strip()})
    universe_id = "universe-" + hashlib.sha256(
        "|".join(symbols).encode("utf-8")).hexdigest()[:16]
    scope = {"symbols": symbols, "universe_id": universe_id}
    scope_sha = fm.sha256_hex(fm.canonical_bytes(scope))
    if len(symbols) != 76 or universe_id != fm.FROZEN_UNIVERSE_ID:
        stop("SCOPE_MISMATCH")
    if scope_sha != fm.FROZEN_SCOPE_SHA256:
        stop("SCOPE_MISMATCH")
    return symbols, universe_id, scope_sha


def fit_forward_model(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    """The frozen protocol, verbatim (runner fit_predict body), returning
    the final parameters instead of test predictions."""
    x_train = np.asarray(x, dtype=np.float64)
    y_train = np.asarray(y, dtype=np.float64)
    n = float(len(x_train))
    w = np.zeros(x_train.shape[1], dtype=np.float64)
    b = 0.0
    for _ in range(EPOCHS):
        logits = b + x_train @ w
        q = np.empty_like(logits)
        positive = logits >= 0
        q[positive] = 1.0 / (1.0 + np.exp(-logits[positive]))
        exp_logits = np.exp(logits[~positive])
        q[~positive] = exp_logits / (1.0 + exp_logits)
        error = q - y_train
        w -= LR * (x_train.T @ error) / n
        b -= LR * float(error.sum()) / n
    return w, b


def window_rows(store, context_maps, symbols, *, start: str,
                last_decision: str) -> list[tuple]:
    """Assemble the frozen 6-feature design rows for one window:
    decision dates in [start, last_decision], one row per
    (symbol, decision_time), sorted by (decision_time, symbol)."""
    rows = []
    for symbol in symbols:
        for row, factors in _factor_rows(store, context_maps.get(symbol, {}), symbol):
            d = _dd(row.decision_time)
            if start <= d <= last_decision:
                try:
                    values = [float(factors[name]) for name in FEATURE_NAMES]
                except (KeyError, TypeError):
                    continue  # missing-factor rows: deterministic drop
                if any(not np.isfinite(v) for v in values) or row.label is None:
                    continue
                rows.append((row.decision_time, symbol, values, int(row.label)))
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows


def main() -> None:
    print(f"[1] frozen scope check (universe={fm.FROZEN_UNIVERSE_ID})")
    symbols, universe_id, scope_sha = load_scope()

    print("[2] data assembly (context truncated to < virgin_start)")
    store = LocalHistoricalStore(ROOT / "data")
    # The context builder scans the local store; truncate every context
    # entry to decision dates strictly before the virgin boundary so no
    # post-2026-09-22 row can reach any downstream stage.
    raw_context = build_universe_industry_relative_context_maps(
        store, str(MEMBERSHIP), tuple(symbols), lookback=20)
    context_maps = {
        symbol: {dt: ctx for dt, ctx in cmap.items() if _dd(dt) < VIRGIN_START}
        for symbol, cmap in raw_context.items()
    }

    print("[3] training window rows")
    train_rows = window_rows(store, context_maps, symbols,
                             start=TRAIN_START, last_decision=TRAIN_LAST_DECISION)
    print(f"    training rows: {len(train_rows)}")
    if not train_rows:
        stop("missing authorized training data")

    x = np.asarray([r[2] for r in train_rows], dtype=np.float64)
    y = np.asarray([r[3] for r in train_rows], dtype=np.float64)

    print("[4] deterministic double-fit (single final model)")
    w_a, b_a = fit_forward_model(x, y)
    w_b, b_b = fit_forward_model(x, y)
    art_a, sha_a, ver_a = fm.serialize_model_application(
        model_family=MODEL_FAMILY, feature_names=FEATURE_NAMES,
        weights=[float(v) for v in w_a], bias=float(b_a))
    art_b, sha_b, ver_b = fm.serialize_model_application(
        model_family=MODEL_FAMILY, feature_names=FEATURE_NAMES,
        weights=[float(v) for v in w_b], bias=float(b_b))
    if art_a != art_b or sha_a != sha_b:
        stop("NON-DETERMINISTIC TRAINING")
    print(f"    double-fit identical; sha256={sha_a}")

    print("[5] freeze MODEL_APPLICATION artifact + manifest")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "MODEL_APPLICATION.json").write_bytes(art_a)

    windows = {
        "training_start": TRAIN_START, "training_end": TRAIN_END,
        "calibration_start": CAL_START, "calibration_end": CAL_END,
        "validation_start": VAL_START, "validation_end": VAL_END,
        "research_end": RESEARCH_END,
    }
    manifest_bytes, manifest_sha, manifest = fm.build_manifest(
        artifact_sha256=sha_a, model_family=MODEL_FAMILY, variant=VARIANT,
        feature_set_id=fm.FROZEN_FEATURE_SET_ID, feature_names=FEATURE_NAMES,
        weights=[float(v) for v in w_a], bias=float(b_a), windows=windows,
        protocol_id=fm.FROZEN_PROTOCOL_ID, seed=SEED,
        scope={"universe_id": universe_id, "symbols": symbols,
               "scope_sha256": scope_sha},
        calibration_binding=None,  # bound below after the calibration freeze
        provenance={"executor": "scripts/run_p13o_forward_model_fit.py",
                    "definition_blobs": {
                        "src/astock_v2/local_pipeline.py":
                            "0582f91ef406d329c7ce3d7460db8f467c20ef75",
                        "scripts/run_local_industry_relative_oos.py":
                            "0b6c0f140fad636a50cee67d2502d6ce27adc5cb"},
                    "authorization":
                        "docs/artifacts/P13-O-FORWARD-MODEL-HUMAN-AUTHORIZATION.md"},
        source_commit=SOURCE_COMMIT)
    (OUT_DIR / "MODEL_APPLICATION_MANIFEST.json").write_bytes(manifest_bytes)

    print("[6] calibration window rows + platt fit (bound calibration)")
    cal_rows = window_rows(store, context_maps, symbols,
                           start=CAL_START, last_decision=CAL_LAST_DECISION)
    print(f"    calibration rows: {len(cal_rows)}")
    if not cal_rows:
        stop("missing authorized calibration data")
    x_cal = np.asarray([r[2] for r in cal_rows], dtype=np.float64)
    y_cal = np.asarray([r[3] for r in cal_rows], dtype=np.float64)
    p_raw = 1.0 / (1.0 + np.exp(-np.clip(b_a + x_cal @ w_a, -30, 30)))
    fitted = fit_platt(p_raw.tolist(), y_cal.tolist())
    a_platt, b_platt = float(fitted["intercept"]), float(fitted["slope"])

    calibration_artifact = {
        "artifact_type": fm.CALIBRATION,
        "method": "platt",
        "logit_domain": "ln(p/(1-p)) clip +-30",
        "a": a_platt,
        "b": b_platt,
        "apply": "sigmoid(a + b * logit(p_raw))",
        "fit_population": {"n": int(len(cal_rows)),
                           "window": [CAL_START, CAL_END]},
        "fit_time_boundary": CAL_END,
        "binding": {
            "model_id": fm.FROZEN_MODEL_ID,
            "model_version": sha_a,
            "model_variant": VARIANT,
            "feature_set_id": fm.FROZEN_FEATURE_SET_ID,
        },
    }
    cal_bytes = fm.canonical_bytes(calibration_artifact)
    cal_sha = fm.sha256_hex(cal_bytes)
    (OUT_DIR / "CALIBRATION.json").write_bytes(cal_bytes)
    cal_manifest = {
        "artifact_type": fm.CALIBRATION,
        "artifact_id": "p13o-forward-model/CALIBRATION",
        "artifact_sha256": cal_sha,
        "calibration_id": "p13o-forward-platt",
        "calibration_version": cal_sha,
        "method": "platt",
        "a": a_platt, "b": b_platt,
        "fit_population": calibration_artifact["fit_population"],
        "fit_time_boundary": CAL_END,
        "binding": calibration_artifact["binding"],
        "provenance": {"fitter": "scripts/run_p13q_analysis.py::fit_platt (accepted P13-Q numerical protocol)"},
        "created_at": None,
        "freeze_status": "FROZEN",
    }
    cal_manifest_bytes = fm.canonical_bytes(cal_manifest)
    cal_manifest_sha = fm.sha256_hex(cal_manifest_bytes)
    (OUT_DIR / "CALIBRATION_MANIFEST.json").write_bytes(cal_manifest_bytes)

    print("[7] bind calibration into the MODEL_APPLICATION manifest")
    manifest["calibration_binding"] = {
        "calibration_id": cal_manifest["calibration_id"],
        "calibration_version": cal_sha,
        "calibration_manifest_sha256": cal_manifest_sha,
    }
    manifest_bytes = fm.canonical_bytes(manifest)
    manifest_sha = fm.sha256_hex(manifest_bytes)
    (OUT_DIR / "MODEL_APPLICATION_MANIFEST.json").write_bytes(manifest_bytes)

    print("[8] identity verification (G21-G30)")
    failures = fm.verify_artifact(art_a, manifest)
    failures += fm.verify_calibration_binding(cal_manifest, model_version=sha_a,
                                              variant=VARIANT,
                                              feature_set_id=fm.FROZEN_FEATURE_SET_ID)
    if failures:
        stop("identity verification failed: " + ", ".join(failures))

    print("[9] virgin-zone scan")
    max_decision = max(_dd(r[0]) for r in train_rows + cal_rows)
    if max_decision >= VIRGIN_START:
        stop("VIRGIN_ZONE_CONTAMINATION")
    print(f"    max decision date used anywhere: {max_decision} (< {VIRGIN_START})")

    print("[10] summary")
    print(json.dumps({
        "model_version": sha_a,
        "artifact_sha256": sha_a,
        "manifest_sha256": manifest_sha,
        "calibration_sha256": cal_sha,
        "calibration_manifest_sha256": cal_manifest_sha,
        "training_rows": len(train_rows),
        "calibration_rows": len(cal_rows),
        "weights": [float(v) for v in w_a],
        "bias": float(b_a),
        "platt": {"a": a_platt, "b": b_platt},
        "max_decision_date_used": max_decision,
    }, indent=1))


if __name__ == "__main__":
    main()
