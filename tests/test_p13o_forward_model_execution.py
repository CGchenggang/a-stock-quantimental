"""P13-O-FORWARD-MODEL-EXECUTION-001 golden checks (G21-G30).

The committed artifacts (docs/artifacts/p13o-forward-model/) are the
audit subjects: positive tests verify the frozen identity chain from
the repository bytes; negative tests mutate copies and prove every
guard FAILS CLOSED. All checks run against the exact committed bytes —
no fixture regeneration.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from astock_v2.model import forward_model as fm

ART_DIR = Path(__file__).resolve().parents[1] / "docs" / "artifacts" / \
    "p13o-forward-model"
FROZEN_MODEL_VERSION = \
    "97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664"
FROZEN_MANIFEST_SHA = \
    "e1993c3f9dd0ed1bbc8fa8e405c386b63ee5fac1f0652fa7116775d0aeab6dd4"
FROZEN_CAL_SHA = \
    "6e341fcd906bfbb72a34e3e33fadc7a1c152051e571a2ab90726c55d68142bc9"
FROZEN_CAL_MANIFEST_SHA = \
    "b758015ade2d6ee1dfe8dfb8d00fd0eb169b589cb932b67414ebeebc5d3f5d7c"


def _load(name: str) -> tuple[bytes, dict]:
    data = (ART_DIR / name).read_bytes()
    return data, json.loads(data.decode("utf-8"))


def test_artifact_files_exist():
    for name in ("MODEL_APPLICATION.json", "MODEL_APPLICATION_MANIFEST.json",
                 "CALIBRATION.json", "CALIBRATION_MANIFEST.json"):
        assert (ART_DIR / name).is_file(), name


# ------------------------------------------------- positive identity chain

def test_artifact_sha256_and_model_version():
    data, _ = _load("MODEL_APPLICATION.json")
    digest = fm.sha256_hex(data)
    assert digest == FROZEN_MODEL_VERSION
    # canonical form: no trailing newline, no BOM, compact
    assert not data.startswith(b"\xef\xbb\xbf")
    assert not data.endswith(b"\n")
    assert b", " not in data and b'": ' not in data


def test_manifest_chain_closed():
    _, manifest = _load("MODEL_APPLICATION_MANIFEST.json")
    data, _ = _load("MODEL_APPLICATION.json")
    assert fm.sha256_hex(fm.canonical_bytes(manifest)) == FROZEN_MANIFEST_SHA
    assert manifest["artifact_sha256"] == fm.sha256_hex(data)
    assert manifest["model_version"] == FROZEN_MODEL_VERSION
    artifact = json.loads(data.decode("utf-8"))
    assert manifest["weights_sha256"] == fm.sha256_hex(
        fm.canonical_bytes(artifact["weights"]))


def test_positive_verification_passes():
    data, _ = _load("MODEL_APPLICATION.json")
    _, manifest = _load("MODEL_APPLICATION_MANIFEST.json")
    assert fm.verify_artifact(data, manifest,
                              as_of="2025-01-02") == []


def test_calibration_chain_and_binding():
    cal_data, cal = _load("CALIBRATION.json")
    assert fm.sha256_hex(cal_data) == FROZEN_CAL_SHA
    _, cal_manifest = _load("CALIBRATION_MANIFEST.json")
    assert fm.sha256_hex(fm.canonical_bytes(cal_manifest)) == FROZEN_CAL_MANIFEST_SHA
    assert cal_manifest["artifact_sha256"] == FROZEN_CAL_SHA
    binding = cal_manifest["binding"]
    assert fm.verify_calibration_binding(cal_manifest, model_version=FROZEN_MODEL_VERSION,
                                         variant=fm.FROZEN_MODEL_VARIANT,
                                         feature_set_id=fm.FROZEN_FEATURE_SET_ID) == []
    assert binding["model_variant"] == "industry_5_20"
    assert binding["feature_set_id"] == fm.FROZEN_FEATURE_SET_ID
    assert cal_manifest["method"] == "platt"
    assert cal_manifest["fit_population"]["window"] == ["2025-01-01", "2025-07-01"]


def test_frozen_identity_fields():
    _, manifest = _load("MODEL_APPLICATION_MANIFEST.json")
    assert manifest["model_id"] == "p13o-forward-logistic"
    assert manifest["model_variant"] == "industry_5_20"
    assert manifest["feature_set_id"] == fm.FROZEN_FEATURE_SET_ID
    assert manifest["feature_names"] == list(fm.FROZEN_FEATURE_NAMES)
    assert manifest["scope"]["universe_id"] == fm.FROZEN_UNIVERSE_ID
    assert manifest["scope_sha256"] == fm.FROZEN_SCOPE_SHA256
    assert manifest["training_protocol_id"] == "p13o-logistic-gd-500x0.05-v1"
    assert manifest["seed"] == 20260929
    assert manifest["preprocessing"] == "identity"
    assert manifest["target"] == "next trading day close-up direction"
    assert manifest["horizon"] == "next_trading_day"
    assert manifest["positive_class"] == "next_return > 0"
    assert manifest["training_start"] == "2020-01-02"
    assert manifest["training_end"] == "2025-01-01"
    assert manifest["validation_end"] == "2026-09-22"
    assert manifest["research_end"] == "2026-09-22"


# ------------------------------------------------- negative: fail closed

def _mutated_manifest(**changes):
    _, manifest = _load("MODEL_APPLICATION_MANIFEST.json")
    manifest.update(changes)
    return manifest


def test_g21_wrong_feature_set_id_fails_closed():
    data, _ = _load("MODEL_APPLICATION.json")
    manifest = _mutated_manifest(feature_set_id="fs-" + "0" * 64)
    failures = fm.verify_artifact(data, manifest)
    assert "feature_set_id_mismatch" in failures


def test_g22_wrong_scope_hash_fails_closed():
    data, _ = _load("MODEL_APPLICATION.json")
    manifest = _mutated_manifest(scope_sha256="0" * 64,
                                 scope={"universe_id": "universe-" + "0" * 16,
                                        "symbols": [], "scope_sha256": "0" * 64})
    assert "scope_mismatch" in fm.verify_artifact(data, manifest)


def test_g23_wrong_variant_fails_closed():
    data, _ = _load("MODEL_APPLICATION.json")
    manifest = _mutated_manifest(model_variant="baseline")
    assert "model_variant_mismatch" in fm.verify_artifact(data, manifest)


def test_g24_wrong_prediction_semantics_fails_closed():
    data, _ = _load("MODEL_APPLICATION.json")
    manifest = _mutated_manifest(target="5-day forward return",
                                 horizon="next_5_days")
    assert "prediction_semantics_mismatch" in fm.verify_artifact(data, manifest)


def test_g25_training_end_at_or_after_as_of_ineligible():
    data, _ = _load("MODEL_APPLICATION.json")
    _, manifest = _load("MODEL_APPLICATION_MANIFEST.json")
    # as_of == training_end -> ineligible (strict <)
    assert "temporal_ineligible" in fm.verify_artifact(
        data, manifest, as_of="2025-01-01")
    # as_of before training_end -> ineligible
    assert "temporal_ineligible" in fm.verify_artifact(
        data, manifest, as_of="2024-06-01")
    # strict inequality: first day AFTER training_end is eligible
    assert fm.verify_artifact(data, manifest, as_of="2025-01-02") == []


def test_g27_artifact_sha_mismatch_fails_closed():
    data, _ = _load("MODEL_APPLICATION.json")
    manifest = _mutated_manifest(artifact_sha256="0" * 64,
                                 model_version="0" * 64)
    failures = fm.verify_artifact(data, manifest)
    assert "artifact_hash_mismatch" in failures
    assert "model_version_mismatch" in failures


def test_g28_manifest_artifact_mismatch_fails_closed():
    data, _ = _load("MODEL_APPLICATION.json")
    manifest = _mutated_manifest(bias=0.5)  # artifact says otherwise
    assert "manifest_artifact_bias_mismatch" in fm.verify_artifact(data, manifest)
    manifest = _mutated_manifest(feature_names=list(fm.FROZEN_FEATURE_NAMES)[:5])
    assert "manifest_artifact_feature_mismatch" in fm.verify_artifact(
        data, manifest)


def test_g29_double_fit_determinism():
    """Same authorized inputs -> identical canonical bytes -> identical
    sha256; different inputs -> different bytes (the comparison is real)."""
    import numpy as np
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from run_p13o_forward_model_fit import fit_forward_model
    from run_p13o_forward_model_fit import FEATURE_NAMES

    rng_x = np.linspace(0.01, 0.05, 600).reshape(100, 6)
    y = (np.linspace(0, 1, 100) > 0.5).astype(float)
    w1, b1 = fit_forward_model(rng_x, y)
    w2, b2 = fit_forward_model(rng_x, y)
    art1, sha1, _ = fm.serialize_model_application(
        model_family="t", feature_names=FEATURE_NAMES,
        weights=[float(v) for v in w1], bias=float(b1))
    art2, sha2, _ = fm.serialize_model_application(
        model_family="t", feature_names=FEATURE_NAMES,
        weights=[float(v) for v in w2], bias=float(b2))
    assert art1 == art2 and sha1 == sha2
    # different inputs -> different bytes (the double-fit check bites)
    w3, b3 = fit_forward_model(rng_x * 1.01, y)
    art3, sha3, _ = fm.serialize_model_application(
        model_family="t", feature_names=FEATURE_NAMES,
        weights=[float(v) for v in w3], bias=float(b3))
    assert art3 != art1 and sha3 != sha1


def test_g30_historical_oos_predictions_rejected():
    fake = json.dumps({
        "artifact_type": "HISTORICAL_OOS_PREDICTION",
        "predictions": [{"symbol": "000001", "p": 0.5}],
    }).encode("utf-8")
    manifest = {"artifact_sha256": fm.sha256_hex(fake),
                "model_version": fm.sha256_hex(fake),
                "model_id": "x", "model_variant": fm.FROZEN_MODEL_VARIANT,
                "feature_set_id": fm.FROZEN_FEATURE_SET_ID,
                "feature_names": [], "weights_sha256": None, "bias": None,
                "scope": {"universe_id": fm.FROZEN_UNIVERSE_ID},
                "scope_sha256": fm.FROZEN_SCOPE_SHA256,
                "target": fm.FROZEN_TARGET, "horizon": fm.FROZEN_HORIZON,
                "positive_class": fm.FROZEN_POSITIVE_CLASS,
                "training_end": "2025-01-01"}
    failures = fm.verify_artifact(fake, manifest)
    assert "historical_prediction_substituted" in failures


def test_g17_g18_missing_parameters_fail_closed():
    artifact = json.dumps({"artifact_type": "MODEL_APPLICATION",
                           "feature_names": list(fm.FROZEN_FEATURE_NAMES),
                           "model_family": "t"}).encode("utf-8")
    manifest = {"artifact_sha256": fm.sha256_hex(artifact),
                "model_version": fm.sha256_hex(artifact),
                "feature_names": list(fm.FROZEN_FEATURE_NAMES),
                "weights_sha256": None, "bias": None,
                "model_variant": fm.FROZEN_MODEL_VARIANT,
                "feature_set_id": fm.FROZEN_FEATURE_SET_ID,
                "scope": {"universe_id": fm.FROZEN_UNIVERSE_ID},
                "scope_sha256": fm.FROZEN_SCOPE_SHA256,
                "target": fm.FROZEN_TARGET, "horizon": fm.FROZEN_HORIZON,
                "positive_class": fm.FROZEN_POSITIVE_CLASS,
                "training_end": "2025-01-01"}
    failures = fm.verify_artifact(artifact, manifest)
    assert "missing_weights" in failures
    assert "missing_bias" in failures


def test_g26_virgin_boundaries_frozen():
    """The executor's frozen exclusion rules keep every window decision
    date strictly before the virgin boundary."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import run_p13o_forward_model_fit as ex
    assert ex.VIRGIN_START == "2026-09-23"
    assert ex.RESEARCH_END == "2026-09-22"
    assert ex.TRAIN_LAST_DECISION < ex.VIRGIN_START
    assert ex.CAL_LAST_DECISION < ex.VIRGIN_START
    assert ex.VAL_END == "2026-09-22" < ex.VIRGIN_START
    # the committed artifacts only bind windows ending before the boundary
    _, manifest = _load("MODEL_APPLICATION_MANIFEST.json")
    assert manifest["training_end"] < manifest["research_end"] < ex.VIRGIN_START


def test_g12_g13_g14_calibration_misbinding_fails_closed():
    _, cal_manifest = _load("CALIBRATION_MANIFEST.json")
    assert "calibration_model_mismatch" in fm.verify_calibration_binding(
        cal_manifest, model_version="0" * 64,
        variant=fm.FROZEN_MODEL_VARIANT, feature_set_id=fm.FROZEN_FEATURE_SET_ID)
    assert "calibration_variant_mismatch" in fm.verify_calibration_binding(
        cal_manifest, model_version=FROZEN_MODEL_VERSION, variant="baseline",
        feature_set_id=fm.FROZEN_FEATURE_SET_ID)
    assert "calibration_feature_mismatch" in fm.verify_calibration_binding(
        cal_manifest, model_version=FROZEN_MODEL_VERSION,
        variant=fm.FROZEN_MODEL_VARIANT, feature_set_id="fs-" + "0" * 64)


def test_negative_zero_and_nan_canonicalization():
    art, sha, _ = fm.serialize_model_application(
        model_family="t", feature_names=["a"],
        weights=[-0.0], bias=float("-0.0"))
    assert b"-0.0" not in art
    assert json.loads(art)["weights"] == [0.0]
    with pytest.raises(ValueError):
        fm.serialize_model_application(model_family="t", feature_names=["a"],
                                       weights=[float("nan")], bias=0.0)
    with pytest.raises(ValueError):
        fm.serialize_model_application(model_family="t", feature_names=["a"],
                                       weights=[float("inf")], bias=0.0)
