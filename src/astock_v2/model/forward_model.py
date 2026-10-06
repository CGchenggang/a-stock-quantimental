"""P13-O Forward Model — canonical artifact serialization, manifest, verifier.

Supports P13-O-FORWARD-MODEL-EXECUTION-001: the Human-Authorized
forward-model artifact freeze. This module provides:

- canonical serialization per P13O-F-016c (UTF-8 no BOM, no trailing
  newline, sort_keys, compact separators, float64 shortest round-trip,
  negative zero -> 0.0, NaN/Infinity forbidden);
- the MODEL_APPLICATION_MANIFEST builder (P13O-F-022, explicit nulls);
- the identity verifier enforcing the frozen bindings (golden checks
  G21-G30): feature_set_id, scope hash, variant, prediction semantics,
  temporal eligibility, hash integrity, manifest/artifact consistency,
  and the historical/forward separation.

It deliberately contains NO fitting and NO R4-D apply path; training is
executed by the authorized executor script under the frozen protocol.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

MODEL_APPLICATION = "MODEL_APPLICATION"
CALIBRATION = "CALIBRATION"
HISTORICAL_OOS_PREDICTION = "HISTORICAL_OOS_PREDICTION"

FROZEN_MODEL_ID = "p13o-forward-logistic"
FROZEN_MODEL_VARIANT = "industry_5_20"
FROZEN_FEATURE_SET_ID = (
    "fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe"
)
FROZEN_UNIVERSE_ID = "universe-d8c5016b1ded0984"
FROZEN_SCOPE_SHA256 = (
    "b7d807a318996e5b4623e82d07a4575143feb8fbdc141ed5c0bd62a0e6a764c1"
)
FROZEN_FEATURE_NAMES = (
    "momentum",
    "volatility",
    "trend",
    "volume_ratio",
    "industry_relative_return_5",
    "industry_relative_return_20",
)
FROZEN_TARGET = "next trading day close-up direction"
FROZEN_HORIZON = "next_trading_day"
FROZEN_POSITIVE_CLASS = "next_return > 0"
FROZEN_TRAINING_END = "2025-01-01"
FROZEN_PROTOCOL_ID = "p13o-logistic-gd-500x0.05-v1"


def canonical_json(obj: Any) -> str:
    """P13O-F-016c canonical serialization (string form)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def _canon_float(value: float) -> float:
    """Normalize one float for canonical bytes: negative zero -> 0.0;
    NaN/Infinity forbidden (generation failure)."""
    v = float(value)
    if math.isnan(v) or math.isinf(v):
        raise ValueError("NaN/Infinity forbidden in canonical artifact")
    if v == 0.0:
        return 0.0  # collapses -0.0
    return v


def canonical_bytes(obj: Any) -> bytes:
    """Exact canonical artifact bytes (hash input). Floats are
    canonicalized (negative zero -> 0.0) BEFORE serialization; nested
    lists of weights pass through the same rule."""
    def _clean(o):
        if isinstance(o, bool) or o is None or isinstance(o, str):
            return o
        if isinstance(o, float):
            return _canon_float(o)
        if isinstance(o, int):
            return o
        if isinstance(o, list):
            return [_clean(x) for x in o]
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items()}
        raise TypeError(f"non-canonical type: {type(o)!r}")

    return canonical_json(_clean(obj)).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def serialize_model_application(*, model_family: str,
                                feature_names: list[str],
                                weights: list[float], bias: float) -> tuple[bytes, str, str]:
    """Build the canonical MODEL_APPLICATION artifact (parameters ONLY —
    execution metadata lives in the manifest, P13O-F-016c). Returns
    (bytes, artifact_sha256, model_version)."""
    artifact = {
        "artifact_type": MODEL_APPLICATION,
        "bias": float(bias),
        "feature_names": list(feature_names),
        "model_family": model_family,
        "weights": [float(w) for w in weights],
    }
    data = canonical_bytes(artifact)
    digest = sha256_hex(data)
    return data, digest, digest  # model_version == artifact sha256 (full)


def build_manifest(*, artifact_sha256: str, model_family: str,
                   variant: str, feature_set_id: str,
                   feature_names: list[str], weights: list[float],
                   bias: float, windows: dict, protocol_id: str,
                   seed: int, scope: dict, calibration_binding: dict | None,
                   provenance: dict, source_commit: str) -> tuple[bytes, str, dict]:
    """Build MODEL_APPLICATION_MANIFEST per P13O-F-022 (explicit nulls,
    execution metadata confined to non-identity fields). Returns
    (manifest canonical bytes, manifest sha256, manifest dict)."""
    manifest = {
        "artifact_type": MODEL_APPLICATION,
        "artifact_id": "p13o-forward-model/MODEL_APPLICATION",
        "artifact_sha256": artifact_sha256,
        "model_id": FROZEN_MODEL_ID,
        "model_version": artifact_sha256,
        "model_family": model_family,
        "model_variant": variant,
        "feature_set_id": feature_set_id,
        "feature_names": list(feature_names),
        "preprocessing": "identity",
        "target": FROZEN_TARGET,
        "horizon": FROZEN_HORIZON,
        "positive_class": FROZEN_POSITIVE_CLASS,
        "training_start": windows["training_start"],
        "training_end": windows["training_end"],
        "calibration_start": windows["calibration_start"],
        "calibration_end": windows["calibration_end"],
        "validation_start": windows["validation_start"],
        "validation_end": windows["validation_end"],
        "research_end": windows["research_end"],
        "training_protocol_id": protocol_id,
        "seed": seed,
        "weights_sha256": sha256_hex(canonical_bytes(weights)),
        "bias": float(bias),
        "scope": scope,
        "scope_sha256": scope.get("scope_sha256"),
        "calibration_binding": calibration_binding,
        "provenance": provenance,
        "source_commit": source_commit,
        "created_at": None,
        "freeze_status": "FROZEN",
    }
    data = canonical_bytes(manifest)
    return data, sha256_hex(data), manifest


def verify_artifact(artifact_bytes: bytes, manifest: dict, *,
                    expected_feature_set_id: str = FROZEN_FEATURE_SET_ID,
                    expected_scope_sha256: str = FROZEN_SCOPE_SHA256,
                    expected_variant: str = FROZEN_MODEL_VARIANT,
                    as_of: str | None = None) -> list[str]:
    """Identity verifier — golden checks G21-G30. Returns the list of
    violations; empty list = PASS. Failing callers MUST fail closed."""
    failures: list[str] = []

    # G02/G27: artifact hash integrity (bytes are the source of truth)
    digest = sha256_hex(artifact_bytes)
    if manifest.get("artifact_sha256") != digest:
        failures.append("artifact_hash_mismatch")
    if manifest.get("model_version") != digest:
        failures.append("model_version_mismatch")

    try:
        artifact = json.loads(artifact_bytes.decode("utf-8"))
    except Exception:
        return failures + ["artifact_unreadable"]

    # G19: manifest/artifact parameter consistency
    if artifact.get("feature_names") != manifest.get("feature_names"):
        failures.append("manifest_artifact_feature_mismatch")
    if artifact.get("weights") != manifest.get("weights_sha256") and \
            sha256_hex(canonical_bytes(artifact.get("weights"))) != \
            manifest.get("weights_sha256"):
        failures.append("manifest_artifact_weights_mismatch")
    if artifact.get("bias") != manifest.get("bias"):
        failures.append("manifest_artifact_bias_mismatch")

    # G21: feature_set_id binding
    if manifest.get("feature_set_id") != expected_feature_set_id:
        failures.append("feature_set_id_mismatch")
    # G22: scope binding
    scope = manifest.get("scope") or {}
    if manifest.get("scope_sha256") != expected_scope_sha256 or \
            scope.get("universe_id") != FROZEN_UNIVERSE_ID:
        failures.append("scope_mismatch")
    # G23: variant binding
    if manifest.get("model_variant") != expected_variant:
        failures.append("model_variant_mismatch")
    # G24: prediction semantics binding
    if (manifest.get("target") != FROZEN_TARGET
            or manifest.get("horizon") != FROZEN_HORIZON
            or manifest.get("positive_class") != FROZEN_POSITIVE_CLASS):
        failures.append("prediction_semantics_mismatch")
    # G25: temporal eligibility
    if as_of is not None:
        if not (manifest.get("training_end", "9999") < as_of):
            failures.append("temporal_ineligible")
    # G17/G18: parameters present
    if not isinstance(artifact.get("weights"), list) or \
            not artifact.get("weights"):
        failures.append("missing_weights")
    if artifact.get("bias") is None:
        failures.append("missing_bias")
    # G30: historical OOS predictions are not a MODEL_APPLICATION
    if artifact.get("artifact_type") != MODEL_APPLICATION:
        failures.append("historical_prediction_substituted")
    return failures


def verify_calibration_binding(calibration: dict, *,
                               model_version: str,
                               variant: str,
                               feature_set_id: str) -> list[str]:
    """G12/G13/G14: calibration must be bound to the exact model."""
    binding = calibration.get("binding") or {}
    failures = []
    if binding.get("model_version") != model_version:
        failures.append("calibration_model_mismatch")
    if binding.get("model_variant") != variant:
        failures.append("calibration_variant_mismatch")
    if binding.get("feature_set_id") != feature_set_id:
        failures.append("calibration_feature_mismatch")
    return failures
