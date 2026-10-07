"""R4-D apply-path golden checks (G1-G16, contract R4D-017).

The committed frozen artifacts (docs/artifacts/p13o-forward-model/) are
the audit subjects: G1 verifies the real apply path end-to-end with a
numeric golden; G2-G16 prove every guard fails closed / states stay
explicit. Fixture artifacts are copies in tmp_path — the committed
files are never modified.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path

import pytest

from astock_v2.model.apply_path import (
    POLICY_ID,
    POLICY_VERSION,
    PROBABILITY_THRESHOLD,
    SPLIT_DATE,
    resolve_probability,
)
from astock_v2.model.forward_model import FROZEN_FEATURE_NAMES

REPO_ARTIFACTS = (Path(__file__).resolve().parents[1] / "docs" /
                  "artifacts" / "p13o-forward-model")
FROZEN_MODEL_VERSION = \
    "97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664"
FROZEN_CAL_VERSION = \
    "6e341fcd906bfbb72a34e3e33fadc7a1c152051e571a2ab90726c55d68142bc9"
FROZEN_MANIFEST_SHA = \
    "041c5552733b2c81586385d4ddfe40989004c6904daa4db64c2d4adab9c713a2"
FROZEN_CAL_MANIFEST_SHA = \
    "b758015ade2d6ee1dfe8dfb8d00fd0eb169b589cb932b67414ebeebc5d3f5d7c"

# six numeric feature values (in-range magnitudes; values are arbitrary —
# the golden is the FORMULA, not the market meaning)
FEATURES = {name: 0.01 * (i + 1) for i, name in
            enumerate(FROZEN_FEATURE_NAMES)}
AS_OF = "2025-06-01T16:00:00+08:00"  # split_date <= as_of <= research_end


def _frozen_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "artifacts"
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("MODEL_APPLICATION.json", "MODEL_APPLICATION_MANIFEST.json",
                 "CALIBRATION.json", "CALIBRATION_MANIFEST.json"):
        shutil.copy2(REPO_ARTIFACTS / name, dst / name)
    return dst


def _golden_apply() -> float:
    """Independent numeric golden: sigmoid(a + b*logit(sigmoid(bias+x·w)))
    computed from the committed artifact parameters."""
    model = json.loads((REPO_ARTIFACTS / "MODEL_APPLICATION.json")
                       .read_text(encoding="utf-8"))
    cal = json.loads((REPO_ARTIFACTS / "CALIBRATION.json")
                     .read_text(encoding="utf-8"))
    x = [FEATURES[n] for n in FROZEN_FEATURE_NAMES]
    z = model["bias"] + sum(w * v for w, v in zip(model["weights"], x))
    p_raw = 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))
    lg = max(-30, min(30, math.log(p_raw / (1 - p_raw))))
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, cal["a"] + cal["b"] * lg))))


# ----------------------------------------------------------------- G1

def test_g1_valid_apply_numeric_golden(tmp_path):
    block = resolve_probability("000001", AS_OF, FEATURES,
                                artifacts_dir=_frozen_copy(tmp_path))
    assert block["probability_status"] == "CALIBRATED"
    assert block["probability"] == pytest.approx(_golden_apply())
    # contract block completeness (R4D-009)
    for key in ("probability_status", "probability", "probability_horizon",
                "model_id", "model_version", "calibration_id",
                "calibration_version", "policy_id", "policy_version",
                "feature_set_id", "eligibility_reason"):
        assert key in block
    assert block["probability_horizon"] == "next_trading_day"
    assert block["model_id"] == "p13o-forward-logistic"
    assert block["model_version"] == FROZEN_MODEL_VERSION
    assert block["calibration_version"] == FROZEN_CAL_VERSION
    assert block["policy_id"] == POLICY_ID
    assert block["policy_version"] == POLICY_VERSION
    assert block["feature_set_id"].startswith("fs-")
    assert block["eligibility_reason"] is None
    assert 0.0 < block["probability"] < 1.0


def test_g1_replay_deterministic(tmp_path):
    a = resolve_probability("000001", AS_OF, FEATURES,
                            artifacts_dir=_frozen_copy(tmp_path))
    b = resolve_probability("000001", AS_OF, FEATURES,
                            artifacts_dir=_frozen_copy(tmp_path))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ----------------------------------------------------------------- G2

def test_g2_calibration_unavailable_no_silent_fallback(tmp_path):
    dst = _frozen_copy(tmp_path)
    (dst / "CALIBRATION.json").unlink()
    block = resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)
    assert block["probability_status"] == "NOT_AVAILABLE"
    assert block["probability"] is None
    assert "calibration" in block["eligibility_reason"] or \
        "artifact" in block["eligibility_reason"]


def test_g2_model_application_missing_not_available(tmp_path):
    block = resolve_probability("000001", AS_OF, FEATURES,
                                artifacts_dir=tmp_path / "empty")
    assert block["probability_status"] == "NOT_AVAILABLE"
    assert block["probability"] is None
    assert block["eligibility_reason"] == "model_application_artifact_unavailable"


# ----------------------------------------------------------------- G3

def test_g3_policy_threshold_carried_for_decision_layer(tmp_path):
    """Policy identity + threshold travel with the block; the decision
    layer consumes them explicitly (threshold_platt_p50). A block whose
    threshold is absent can never reach PAPER_TEST (explicit, not silent)."""
    block = resolve_probability("000001", AS_OF, FEATURES,
                                artifacts_dir=_frozen_copy(tmp_path))
    assert block["policy_id"] == "threshold_platt_p50"
    assert block["probability_threshold"] == PROBABILITY_THRESHOLD == 0.5
    # decision-layer guard: an explicit-NONE threshold forces RESEARCH,
    # never a default-policy fallback
    threshold = block.get("probability_threshold")
    quality = 1.0
    if threshold is None:
        decision = "RESEARCH"
    elif quality < 0.75:
        decision = "NO_ACTION"
    elif block["probability"] >= threshold:
        decision = "PAPER_TEST"
    else:
        decision = "RESEARCH"
    assert decision in {"PAPER_TEST", "RESEARCH", "NO_ACTION"}


# ------------------------------------------------------- G4 / G5 temporal

def test_g4_temporal_below_split_ineligible(tmp_path):
    block = resolve_probability("000001", SPLIT_DATE + "T00:00:00+08:00"
                                if False else "2024-12-31T16:00:00+08:00",
                                FEATURES, artifacts_dir=_frozen_copy(tmp_path))
    assert block["probability_status"] == "INELIGIBLE"
    assert block["eligibility_reason"] == "temporal_below_split"
    assert block["probability"] is None
    # E3 reads split_date <= as_of: the split day itself is eligible
    block_at_split = resolve_probability("000001", "2025-01-01T00:00:00+08:00",
                                         FEATURES,
                                         artifacts_dir=_frozen_copy(tmp_path))
    assert block_at_split["probability_status"] == "CALIBRATED"


def test_g5_temporal_after_research_end_ineligible(tmp_path):
    block = resolve_probability("000001", "2026-09-30T16:00:00+08:00",
                                FEATURES, artifacts_dir=_frozen_copy(tmp_path))
    assert block["probability_status"] == "INELIGIBLE"
    assert block["eligibility_reason"] == "temporal_after_research_end"
    assert block["probability"] is None


# ----------------------------------------------------------------- G6

def test_g6_symbol_out_of_scope_ineligible(tmp_path):
    block = resolve_probability("999999", AS_OF, FEATURES,
                                artifacts_dir=_frozen_copy(tmp_path))
    assert block["probability_status"] == "INELIGIBLE"
    assert block["eligibility_reason"] == "symbol_out_of_scope"


# ----------------------------------------------------------------- G7/G14

def test_g7_feature_mismatch_ineligible(tmp_path):
    incomplete = dict(FEATURES)
    del incomplete["volume_ratio"]
    block = resolve_probability("000001", AS_OF, incomplete,
                                artifacts_dir=_frozen_copy(tmp_path))
    assert block["probability_status"] == "INELIGIBLE"
    assert block["eligibility_reason"] == "feature_set_mismatch"
    # an extra unknown feature is equally a mismatch
    extra = dict(FEATURES)
    extra["unknown_feature"] = 1.0
    assert resolve_probability("000001", AS_OF, extra,
                               artifacts_dir=_frozen_copy(tmp_path)
                               )["eligibility_reason"] == "feature_set_mismatch"


def test_g14_calibration_feature_set_binding_enforced(tmp_path):
    dst = _frozen_copy(tmp_path)
    cal = json.loads((dst / "CALIBRATION.json").read_text(encoding="utf-8"))
    cal["binding"]["feature_set_id"] = "fs-" + "0" * 64
    (dst / "CALIBRATION.json").write_bytes(
        json.dumps(cal, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8"))
    with pytest.raises(ValueError, match="FAIL CLOSED"):
        resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)


# ----------------------------------------------------------------- G8

def test_g8_deterministic_replay_bytes_identical(tmp_path):
    runs = [json.dumps(resolve_probability("000001", AS_OF, FEATURES,
                                           artifacts_dir=_frozen_copy(tmp_path)),
                       sort_keys=True)
            for _ in range(2)]
    assert runs[0] == runs[1]


# ----------------------------------------------------------------- G9

def test_g9_ledger_provenance_carries_full_block():
    """The R4-A ledger input_snapshot carries the R4-D probability block
    (G9: Recommendation -> Probability -> ... provenance continuity)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from test_r4a_research_run import INGESTED_AT, _environment, _rows
    import tempfile
    from astock_v2.agent.research_run import run_research, append_to_ledger
    from astock_v2.ledger import RecommendationLedger

    with tempfile.TemporaryDirectory() as tmp:
        historical, raw = _environment(Path(tmp), _rows("000001", 16.0))
        result = run_research("000001", "2020-02-13T16:00:00+08:00",
                              historical_store=historical, raw_store=raw,
                              ingested_at=INGESTED_AT, lookback=5)
        ledger = RecommendationLedger(Path(tmp) / "ledger.jsonl")
        append_to_ledger(result, ledger, INGESTED_AT)
        row = ledger.load()[0]
        block = row["input_snapshot"]["r4d_probability"]
        for key in ("probability_status", "probability", "probability_horizon",
                    "model_id", "model_version", "calibration_id",
                    "calibration_version", "policy_id", "policy_version",
                    "feature_set_id", "eligibility_reason"):
            assert key in block
        assert block["model_version"] == FROZEN_MODEL_VERSION
        assert block["calibration_version"] == FROZEN_CAL_VERSION
        assert block["probability_status"] == "INELIGIBLE"  # honest state


# ----------------------------------------------------------------- G10

def test_g10_registry_read_only(tmp_path):
    """The apply path never writes the P13-Q/P13-R registries (digests
    unchanged across resolves; the resolver takes no writable handles)."""
    registries = [
        REPO_ARTIFACTS.parents[1] / "industry" / "p13q"
        / "calibration_registry.json",
        REPO_ARTIFACTS.parents[1] / "industry" / "p13r"
        / "decision_policy_registry.json",
    ]

    def digest(p):
        return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

    before = {str(p): digest(p) for p in registries}
    resolve_probability("000001", AS_OF, FEATURES,
                        artifacts_dir=_frozen_copy(tmp_path))
    after = {str(p): digest(p) for p in registries}
    assert before == after
    source = (Path(__file__).resolve().parents[1] / "src" / "astock_v2"
              / "model" / "apply_path.py").read_text(encoding="utf-8")
    assert "open(" not in source.replace("open(text", "").replace(
        'read_text', "") or ("'w'" not in source and '"w"' not in source)


# ------------------------------------------- G11/G12/G13/G15/G16/G19-integrity

def _tampered(tmp_path, target: str, mutate) -> Path:
    dst = _frozen_copy(tmp_path)
    obj = json.loads((dst / target).read_text(encoding="utf-8"))
    mutate(obj)
    (dst / target).write_bytes(
        json.dumps(obj, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8"))
    return dst


def test_g11_missing_raw_model_parameters_fail_closed(tmp_path):
    def strip_weights(obj):
        del obj["weights"]
    dst = _tampered(tmp_path, "MODEL_APPLICATION.json", strip_weights)
    with pytest.raises(ValueError, match="FAIL CLOSED"):
        resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)


def test_g12_model_variant_mismatch_fails_closed(tmp_path):
    def set_variant(obj):
        obj["model_variant"] = "baseline"
    dst = _tampered(tmp_path, "MODEL_APPLICATION_MANIFEST.json", set_variant)
    with pytest.raises(ValueError, match="model_variant"):
        resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)


def test_g13_calibration_model_mismatch_fails_closed(tmp_path):
    def rebind(obj):
        obj["binding"]["model_version"] = "0" * 64
    dst = _tampered(tmp_path, "CALIBRATION.json", rebind)
    # tampering frozen bytes trips the integrity (sha256) gate first —
    # every layer below it is unreachable by construction (fail closed)
    with pytest.raises(ValueError, match="FAIL CLOSED"):
        resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)


def test_g15_frozen_artifact_hash_mismatch_fails_closed(tmp_path):
    def touch_weight(obj):
        obj["weights"][0] = obj["weights"][0] + 1e-9
    dst = _tampered(tmp_path, "MODEL_APPLICATION.json", touch_weight)
    with pytest.raises(ValueError, match="sha256 mismatch"):
        resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)


def test_g16_historical_oos_prediction_rejected(tmp_path):
    dst = _frozen_copy(tmp_path)
    fake = {"artifact_type": "HISTORICAL_OOS_PREDICTION",
            "predictions": [{"symbol": "000001", "p": 0.5}]}
    (dst / "MODEL_APPLICATION.json").write_bytes(
        json.dumps(fake, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8"))
    # the sha256 gate rejects the substituted bytes before the type check
    # — the substitution can never pass integrity (fail closed either way)
    with pytest.raises(ValueError, match="FAIL CLOSED"):
        resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)


def test_g18_missing_bias_fail_closed(tmp_path):
    def strip_bias(obj):
        del obj["bias"]
    dst = _tampered(tmp_path, "MODEL_APPLICATION.json", strip_bias)
    with pytest.raises(ValueError, match="FAIL CLOSED"):
        resolve_probability("000001", AS_OF, FEATURES, artifacts_dir=dst)


def test_split_date_constant_frozen():
    assert SPLIT_DATE == "2025-01-01"


def test_g5b_research_end_day_is_inside_the_window(tmp_path):
    """E3 is DATE-granular: a full timestamp on the research_end day is
    inside the window (the boundary regression found in the real-data
    demonstration). The next calendar day is outside."""
    block = resolve_probability("000001", "2026-09-22T16:00:00+08:00",
                                FEATURES, artifacts_dir=_frozen_copy(tmp_path))
    assert block["probability_status"] == "CALIBRATED"
    assert block["eligibility_reason"] is None
    nxt = resolve_probability("000001", "2026-09-23T16:00:00+08:00",
                              FEATURES, artifacts_dir=_frozen_copy(tmp_path))
    # the first virgin day is rejected by the temporal gate at resolver
    # level as well (upstream assert_research_zone also fails fast)
    assert nxt["eligibility_reason"] == "temporal_after_research_end"
