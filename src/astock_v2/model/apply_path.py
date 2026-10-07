"""R4-D Calibrated Probability Apply-Path (authorized implementation).

Implements the accepted contract
``docs/contracts/R4-D-CALIBRATED-PROBABILITY-APPLY-CONTRACT.md``
(v2, R4D-001..019) under Human Authorization
R4-D-APPLY-HUMAN-AUTHORIZATION-001.

The resolver consumes the FROZEN MODEL_APPLICATION + CALIBRATION
artifacts as read-only authorities and produces the contract-defined
probability block (R4D-009). It performs NO fitting, NO registry
writes, and NO PIT logic of its own:

- Frozen-asset integrity is a FAIL-CLOSED gate (G15/G16/G12/G13/G14):
  any hash mismatch, wrong artifact type, or binding inconsistency
  aborts with an exception — integrity disasters are never converted
  into business states.
- Run-input eligibility is an explicit business state (R4D-008):
  ``CALIBRATED`` / ``NOT_AVAILABLE(reason)`` / ``INELIGIBLE(reason)``
  for temporal (E3), scope (E5) and feature-set (E4) conditions.
- No silent fallback (R4D-010): a raw score is never surfaced as a
  calibrated probability; failures stay explicit.
- The only PIT semantics remain the accepted P14-D authority upstream;
  the temporal eligibility check here is the contract's E3 window rule
  (split_date <= as_of <= research_end), not a second visibility rule.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from .forward_model import (
    FROZEN_FEATURE_NAMES,
    FROZEN_MODEL_ID,
    FROZEN_MODEL_VARIANT,
    FROZEN_SCOPE_SHA256,
    MODEL_APPLICATION,
    canonical_bytes,
    sha256_hex,
)

DEFAULT_ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[3] / "docs" / "artifacts"
    / "p13o-forward-model"
)

# Frozen constants (R4D-003/004 — audited values, not runtime guesses)
SPLIT_DATE = "2025-01-01"
RESEARCH_END = "2026-09-22"
POLICY_ID = "threshold_platt_p50"
POLICY_VERSION = (
    "361791f8bf072778b9cbb84f3a81b6079a148471cb17c6b5953e042ddf09d16c"
)
PROBABILITY_THRESHOLD = 0.5
PROBABILITY_HORIZON = "next_trading_day"
MODEL_FAMILY = "unregularized_binary_logistic"

STATUS_CALIBRATED = "CALIBRATED"
STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
STATUS_INELIGIBLE = "INELIGIBLE"

_LOGIT_CLIP = 30.0


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid (contract D: clip ±30)."""
    z = max(-_LOGIT_CLIP, min(_LOGIT_CLIP, x))
    return 1.0 / (1.0 + math.exp(-z))


def _logit(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError(f"logit undefined for p={p!r}")
    z = math.log(p / (1.0 - p))
    return max(-_LOGIT_CLIP, min(_LOGIT_CLIP, z))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fail_closed(message: str) -> None:
    """G15/G16/G12/G13/G14: integrity disasters abort — they are never
    converted into business states (R4D-010)."""
    raise ValueError(f"FAIL CLOSED: {message}")


def _load_frozen_artifacts(artifacts_dir: Path) -> dict:
    """E1 + integrity gates. Returns the parsed artifact set or raises
    FAIL CLOSED on any integrity problem."""
    paths = {name: artifacts_dir / name for name in (
        "MODEL_APPLICATION.json", "MODEL_APPLICATION_MANIFEST.json",
        "CALIBRATION.json", "CALIBRATION_MANIFEST.json")}
    if not all(p.is_file() for p in paths.values()):
        return None  # E1 unreadable -> business NOT_AVAILABLE upstream
    try:
        model_bytes = paths["MODEL_APPLICATION.json"].read_bytes()
        model = _read_json(paths["MODEL_APPLICATION.json"])
        manifest = _read_json(paths["MODEL_APPLICATION_MANIFEST.json"])
        calibration = _read_json(paths["CALIBRATION.json"])
        calibration_manifest = _read_json(
            paths["CALIBRATION_MANIFEST.json"])
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        _fail_closed(f"artifact unreadable: {exc}")

    # G15: frozen-artifact hash gate — bytes must match the manifest AND
    # the audited evidence values.
    digest = sha256_hex(model_bytes)
    if digest != manifest.get("artifact_sha256"):
        _fail_closed("MODEL_APPLICATION sha256 mismatch")
    if digest != manifest.get("model_version"):
        _fail_closed("model_version mismatch")
    if manifest.get("artifact_sha256") != (
            "97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664"):
        _fail_closed("MODEL_APPLICATION sha256 does not match the "
                     "audited frozen value")
    cal_digest = sha256_hex(
        paths["CALIBRATION.json"].read_bytes())
    if cal_digest != calibration_manifest.get("artifact_sha256"):
        _fail_closed("CALIBRATION sha256 mismatch")
    if cal_digest != (
            "6e341fcd906bfbb72a34e3e33fadc7a1c152051e571a2ab90726c55d68142bc9"):
        _fail_closed("CALIBRATION sha256 does not match the audited "
                     "frozen value")

    # G16: historical OOS predictions are never a forward model.
    if model.get("artifact_type") != MODEL_APPLICATION:
        _fail_closed("historical prediction artifact substituted for "
                     "MODEL_APPLICATION")
    if calibration.get("artifact_type") != "CALIBRATION":
        _fail_closed("substituted artifact is not CALIBRATION")

    # G12/G13/G14: the frozen pair must be internally consistent.
    binding = calibration.get("binding") or {}
    if binding.get("model_version") != manifest.get("model_version"):
        _fail_closed("calibration bound to another model_version")
    if binding.get("model_variant") != manifest.get("model_variant"):
        _fail_closed("calibration bound to another model_variant")
    if binding.get("feature_set_id") != manifest.get("feature_set_id"):
        _fail_closed("calibration bound to another feature_set_id")
    if manifest.get("model_variant") != FROZEN_MODEL_VARIANT:
        _fail_closed("model_variant mismatch")
    if manifest.get("model_id") != FROZEN_MODEL_ID:
        _fail_closed("model_id mismatch")
    if manifest.get("feature_set_id") != (
            "fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe"):
        _fail_closed("feature_set_id mismatch")

    scope = manifest.get("scope") or {}
    if scope.get("universe_id") != "universe-d8c5016b1ded0984" or \
            scope.get("scope_sha256") != (
            "b7d807a318996e5b4623e82d07a4575143feb8fbdc141ed5c0bd62a0e6a764c1"):
        _fail_closed("scope mismatch")
    return {"model": model, "manifest": manifest,
            "calibration": calibration,
            "calibration_manifest": calibration_manifest,
            "scope_symbols": tuple(scope.get("symbols") or ())}


def resolve_probability(symbol: str, as_of: str,
                        factor_values: Mapping[str, Any], *,
                        artifacts_dir: str | Path | None = None) -> dict:
    """Resolve the R4D-009 probability block for one (symbol, as_of).

    ``factor_values`` maps feature name -> numeric value from the
    research packet. The block carries ``probability`` ONLY when
    ``probability_status == "CALIBRATED"`` (R4D-009); integrity
    problems raise (FAIL CLOSED, R4D-010).
    """
    artifacts_dir = Path(artifacts_dir) if artifacts_dir else DEFAULT_ARTIFACTS_DIR

    identity: dict[str, Any] = {
        "model_version": None,
        "calibration_id": None,
        "calibration_version": None,
    }

    def _block(status: str, *, probability: float | None = None,
               reason: str | None = None) -> dict:
        block = {
            "probability_status": status,
            "probability": probability if status == STATUS_CALIBRATED else None,
            "probability_horizon": PROBABILITY_HORIZON,
            "model_id": FROZEN_MODEL_ID,
            "model_version": identity["model_version"],
            "calibration_id": identity["calibration_id"],
            "calibration_version": identity["calibration_version"],
            "policy_id": POLICY_ID,
            "policy_version": POLICY_VERSION,
            "feature_set_id": (
                "fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe"),
            "probability_threshold": PROBABILITY_THRESHOLD,
            "eligibility_reason": reason,
        }
        return block

    # E1: artifact readability (business state on absence)
    frozen = None
    try:
        frozen = _load_frozen_artifacts(artifacts_dir)
    except ValueError as exc:
        if "artifact unreadable" in str(exc):
            return _block(STATUS_NOT_AVAILABLE,
                          reason="model_application_artifact_unreadable")
        raise  # integrity disaster: FAIL CLOSED
    if frozen is None:
        return _block(STATUS_NOT_AVAILABLE,
                      reason="model_application_artifact_unavailable")
    model = frozen["model"]
    identity["model_version"] = frozen["manifest"]["model_version"]
    identity["calibration_id"] = (
        frozen["calibration_manifest"].get("calibration_id"))
    identity["calibration_version"] = (
        frozen["calibration_manifest"].get("calibration_version"))
    manifest = frozen["manifest"]
    calibration = frozen["calibration"]

    # E3: temporal window (split_date <= as_of <= research_end) — the
    # comparison is DATE-granular: a full timestamp on the research_end
    # day (e.g. 2026-09-22T16:00+08:00) is inside the window.
    as_of_date = as_of[:10]
    if as_of_date < SPLIT_DATE:
        return _block(STATUS_INELIGIBLE, reason="temporal_below_split")
    if as_of_date > RESEARCH_END:
        return _block(STATUS_INELIGIBLE, reason="temporal_after_research_end")

    # E5: scope
    if symbol not in frozen["scope_symbols"]:
        return _block(STATUS_INELIGIBLE, reason="symbol_out_of_scope")

    # E4: feature-set identity — the packet must carry EXACTLY the frozen
    # feature set: every frozen name present with a numeric value, and no
    # unknown names (a superset is as much a mismatch as a subset).
    if set(factor_values.keys()) != set(FROZEN_FEATURE_NAMES):
        return _block(STATUS_INELIGIBLE, reason="feature_set_mismatch")
    try:
        values = [float(factor_values[name]) for name in FROZEN_FEATURE_NAMES]
    except (TypeError, ValueError):
        return _block(STATUS_INELIGIBLE, reason="feature_set_mismatch")
    if not all(math.isfinite(v) for v in values):
        return _block(STATUS_INELIGIBLE, reason="feature_set_mismatch")

    # Forward apply: p_raw = sigmoid(bias + x·w) — the frozen model,
    # verbatim; then the bound platt calibration.
    bias = float(model["bias"])
    weights = [float(w) for w in model["weights"]]
    z = bias + sum(w * v for w, v in zip(weights, values))
    p_raw = _sigmoid(z)
    a = float(calibration["a"])
    b = float(calibration["b"])
    probability = _sigmoid(a + b * _logit(p_raw))

    return _block(STATUS_CALIBRATED, probability=probability)
