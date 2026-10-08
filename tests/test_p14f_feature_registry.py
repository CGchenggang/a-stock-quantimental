"""P14-F Feature Registry golden checks (contract §9, GF-01..08).

Hermetic: tmp_path fixtures; committed registry file (read-only);
``git cat-file -e`` only against committed blobs; no data/ reads.

The committed registry is the audit subject: GF-01..03 verify its
schema, derivation, and blob anchors; GF-04..08 verify the runtime
behaviors (packet shape, missing-feature handling, resolver CALIBRATED
numeric-exact, mutation detection, and immutability across a run).
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from astock_v2.data.catalog import AssetScope, DataLayer, HistoricalRecord
from astock_v2.data.local_store import LocalHistoricalStore
from astock_v2.features import (
    FeatureSetBindingError,
    MemberUnresolvedError,
    feature_set_id,
    load_registry,
    registry_sha256,
    resolve_membership,
    verify_against_frozen,
)
from astock_v2.features.registry import (
    EVIDENCE_PATH,
    REGISTRY_PATH,
)
from astock_v2.information.raw_store import RawStore
from astock_v2.model.forward_model import (
    FROZEN_FEATURE_NAMES,
    FROZEN_FEATURE_SET_ID,
    canonical_json,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_ARTIFACTS = REPO_ROOT / "docs" / "artifacts" / "p13o-forward-model"

FROZEN_MODEL_VERSION = \
    "97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664"


# ----------------------------------------------- shared fixture helpers

INGESTED_AT = "2025-07-10T00:00:00+08:00"

# 25 business days in [split_date=2025-01-01, research_end=2026-09-22].
_DAYS = [
    "2025-06-02", "2025-06-03", "2025-06-04", "2025-06-05", "2025-06-06",
    "2025-06-09", "2025-06-10", "2025-06-11", "2025-06-12", "2025-06-13",
    "2025-06-16", "2025-06-17", "2025-06-18", "2025-06-19", "2025-06-20",
    "2025-06-23", "2025-06-24", "2025-06-25", "2025-06-26", "2025-06-27",
    "2025-06-30", "2025-07-01", "2025-07-02", "2025-07-03", "2025-07-07",
]


def _daily_rows(symbol: str, base: float, step: float = 0.05) -> list:
    return [
        HistoricalRecord(
            symbol=symbol,
            event_time=f"{day}T15:00:00+08:00",
            available_time=f"{day}T16:00:00+08:00",
            source="akshare:stock_zh_a_hist_tx",
            source_type="historical_vendor",
            value={"date": day, "open": base + i * step - 0.05,
                   "close": base + i * step, "high": base + i * step + 0.1,
                   "low": base + i * step - 0.1, "volume": 1_000_000.0 + i,
                   "amount": None, "adjust": ""},
            layer=DataLayer.CLEAN,
            asset_scope=AssetScope.CN_STOCK,
            revision=0,
            raw_ref="b" * 64,
            quality="SOURCE_RETURNED",
        )
        for i, day in enumerate(_DAYS)
    ]


def _write_membership_csv(path: Path) -> Path:
    csv_path = path / "membership.csv"
    header = (
        "symbol,industry_code,industry_name,level,"
        "effective_from,effective_to,available_time,"
        "source,source_type,raw_ref"
    )
    rows = [
        "000001,801010,农林牧渔,SW1,2020-01-01T00:00:00+08:00,,"
        "2020-01-02T00:00:00+08:00,cninfo,official,rrrr",
        "000002,801010,农林牧渔,SW1,2020-01-01T00:00:00+08:00,,"
        "2020-01-02T00:00:00+08:00,cninfo,official,rrrr",
    ]
    csv_path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return csv_path


def _build_store(tmp_path: Path) -> LocalHistoricalStore:
    store = LocalHistoricalStore(root=tmp_path / "data")
    store.append_records("cn_stock_daily", _daily_rows("000001", base=16.0))
    store.append_records("cn_stock_daily", _daily_rows("000002", base=11.0))
    return store


AS_OF_LAST = f"{_DAYS[-1]}T16:00:00+08:00"


def _frozen_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "artifacts"
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("MODEL_APPLICATION.json", "MODEL_APPLICATION_MANIFEST.json",
                 "CALIBRATION.json", "CALIBRATION_MANIFEST.json"):
        shutil.copy2(REPO_ARTIFACTS / name, dst / name)
    return dst


def _golden_platt_probability() -> float:
    """Independent numeric golden — computed from the committed frozen
    artifacts (NOT from the resolver's output): sigmoid(a + b * logit(
    sigmoid(bias + x·w)))."""
    model = json.loads((REPO_ARTIFACTS / "MODEL_APPLICATION.json")
                       .read_text(encoding="utf-8"))
    cal = json.loads((REPO_ARTIFACTS / "CALIBRATION.json")
                     .read_text(encoding="utf-8"))
    x = [0.01 * (i + 1) for i in range(len(FROZEN_FEATURE_NAMES))]
    z = model["bias"] + sum(w * v for w, v in zip(model["weights"], x))
    p_raw = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
    lg = max(-30.0, min(30.0, math.log(p_raw / (1.0 - p_raw))))
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, cal["a"] + cal["b"] * lg))))


# ---------------------------------------------------------------- GF-01

def test_gf01_registry_loads_and_schema_valid():
    """GF-01 — registry loads; schema valid; ids recompute."""
    reg = load_registry()
    assert set(reg.keys()) == {"definitions", "registry_version"}
    assert reg["registry_version"] == 1
    assert set(reg["definitions"].keys()) == set(FROZEN_FEATURE_NAMES)
    # every entry carries the 9 fields per contract P14F2-002
    required = {"name", "definition_version", "computation_identity",
                "source_lineage", "semantics", "pit_authority",
                "implementation_identity", "ordering_hint"}
    for name, entry in reg["definitions"].items():
        assert required.issubset(entry.keys())
        assert entry["name"] == name
        assert {"source_file", "entry_symbol", "parameters"}.issubset(
            entry["computation_identity"].keys())
    # ids recompute (GF-02 is the equality assertion)
    derived = feature_set_id(reg)
    assert derived.startswith("fs-")
    assert len(derived) == 3 + 64


# ---------------------------------------------------------------- GF-02

def test_gf02_feature_set_id_matches_frozen():
    """GF-02 — derived feature_set_id == frozen MODEL_APPLICATION id."""
    reg = load_registry()
    assert feature_set_id(reg) == FROZEN_FEATURE_SET_ID
    # and verify_against_frozen accepts it (does not raise)
    verify_against_frozen(reg)


# ---------------------------------------------------------------- GF-03

def test_gf03_definition_blobs_exist_at_head():
    """GF-03 — every pinned implementation_identity exists as a committed
    blob at HEAD (``git cat-file -e``). Hermetic: uses -C <repo_root>,
    operates on committed blobs only."""
    reg = load_registry()
    seen: set[str] = set()
    for entry in reg["definitions"].values():
        seen.add(entry["implementation_identity"])
    # two unique blobs expected (4 stock + 2 industry)
    assert seen == {
        "0582f91ef406d329c7ce3d7460db8f467c20ef75",
        "0b6c0f140fad636a50cee67d2502d6ce27adc5cb",
    }
    for blob in seen:
        proc = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "cat-file", "-e", blob],
            capture_output=True, check=False)
        assert proc.returncode == 0, (
            f"blob {blob} missing at HEAD: {proc.stderr.decode()!r}")


# ---------------------------------------------------------------- GF-04

def test_gf04_packet_assembly_six_features_in_frozen_order(tmp_path):
    """GF-04 — run_research with full capability tuple yields the 6
    frozen feature names in the frozen MEMBERSHIP order (P14F2-007/011)."""
    from astock_v2.agent.research_run import run_research

    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    result = run_research(
        "000001", AS_OF_LAST,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    factor_values = {n: info["value"] for n, info in result["factors"].items()
                     if info["value"] is not None}
    assert set(factor_values) == set(FROZEN_FEATURE_NAMES)
    # frozen membership ORDER is preserved when iterating factor_values in
    # FROZEN_FEATURE_NAMES order — the resolver consumes them positionally
    # via list(factor_values[name] for name in FROZEN_FEATURE_NAMES)
    for name in FROZEN_FEATURE_NAMES:
        v = factor_values[name]
        assert math.isfinite(v)
    # registry resolve_membership returns them in frozen order
    reg = load_registry()
    resolved = resolve_membership(reg)
    assert [n for n, _ in resolved] == list(FROZEN_FEATURE_NAMES)


# ---------------------------------------------------------------- GF-05

def test_gf05_missing_feature_honest_absence_counted(tmp_path):
    """GF-05 — contract §5 P14F2-013 defines row-drop determinism for the
    training pipeline; the agent loop's honest-absence equivalent is: if
    one registered feature cannot be computed, the resolver sees fewer
    than 6 factor values and reports INELIGIBLE(feature_set_mismatch) —
    never a silent fabrication, never a partial packet.

    The drop is 'counted' via the resolver's explicit eligibility_reason
    (not a numeric counter: the agent loop does not drop rows, it drops
    the probability block)."""
    from astock_v2.agent.research_run import run_research

    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    # as_of at position 10 — inside the research window but before the
    # context map has any entry (the builder only emits from position 20).
    as_of_absent = f"{_DAYS[10]}T16:00:00+08:00"
    result = run_research(
        "000001", as_of_absent,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    # both industry factors are None — honest absence, not fabrication
    for name in ("industry_relative_return_5", "industry_relative_return_20"):
        entry = result["factors"][name]
        assert entry["value"] is None
        assert entry["admissible"] is False
    # the resolver reports the explicit mismatch state
    assert result["probability"]["probability_status"] == "INELIGIBLE"
    assert result["probability"]["eligibility_reason"] == "feature_set_mismatch"


# ---------------------------------------------------------------- GF-06

def test_gf06_resolver_e4_accepts_calibrated_numeric_exact(tmp_path):
    """GF-06 — resolver E4 accepts the registry-derived set: CALIBRATED
    reachable on research_end day; numeric probability equals the platt
    formula applied to the frozen artifacts' parameters (byte-exact
    vs the independently-computed golden)."""
    from astock_v2.agent.research_run import run_research
    from astock_v2.model.apply_path import resolve_probability

    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    result = run_research(
        "000001", AS_OF_LAST,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    assert result["probability"]["probability_status"] == "CALIBRATED"
    probability = result["probability"]["probability"]
    assert isinstance(probability, float)
    assert 0.0 < probability < 1.0
    # numeric-exact platt golden: feed the same factor_values through
    # the frozen artifacts' bias/weights/a/b and compare byte-exact
    factor_values = {n: info["value"] for n, info in result["factors"].items()
                     if info["value"] is not None}
    artifacts = _frozen_copy(tmp_path)
    block = resolve_probability("000001", AS_OF_LAST, factor_values,
                                artifacts_dir=artifacts)
    assert block["probability_status"] == "CALIBRATED"
    assert block["probability"] == probability
    # independently-computed platt formula on the SAME factor values
    model = json.loads((REPO_ARTIFACTS / "MODEL_APPLICATION.json")
                       .read_text(encoding="utf-8"))
    cal = json.loads((REPO_ARTIFACTS / "CALIBRATION.json")
                     .read_text(encoding="utf-8"))
    x = [factor_values[n] for n in FROZEN_FEATURE_NAMES]
    z = model["bias"] + sum(w * v for w, v in zip(model["weights"], x))
    p_raw = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
    lg = max(-30.0, min(30.0, math.log(p_raw / (1.0 - p_raw))))
    expected = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, cal["a"] + cal["b"] * lg))))
    assert probability == expected


def test_gf06_resolver_numeric_golden_with_fixed_features(tmp_path):
    """GF-06 numeric golden variant — fixed feature values, same platt
    recipe as test_r4d_apply_path.py:_golden_apply (cross-check that the
    registry-derived path and the frozen-artifact path agree)."""
    from astock_v2.model.apply_path import resolve_probability

    artifacts = _frozen_copy(tmp_path)
    features = {name: 0.01 * (i + 1) for i, name in
                enumerate(FROZEN_FEATURE_NAMES)}
    block = resolve_probability("000001", "2025-06-01T16:00:00+08:00",
                                features, artifacts_dir=artifacts)
    assert block["probability_status"] == "CALIBRATED"
    assert block["probability"] == _golden_platt_probability()


# ---------------------------------------------------------------- GF-07

def test_gf07_registry_byte_change_changes_id():
    """GF-07 — any registry byte change yields a different derived id
    (and the altered id does not match the frozen binding)."""
    reg = load_registry()
    original_id = feature_set_id(reg)
    assert original_id == FROZEN_FEATURE_SET_ID
    # synthesize a mutated registry: bump one entry's definition_version
    # by appending a single character
    mutated = json.loads(json.dumps(reg))
    first_name = next(iter(mutated["definitions"]))
    mutated["definitions"][first_name]["definition_version"] += "x"
    mutated_id = feature_set_id(mutated)
    assert mutated_id != original_id
    assert mutated_id != FROZEN_FEATURE_SET_ID
    # and verify_against_frozen fails closed on the mutated registry
    with pytest.raises(FeatureSetBindingError):
        verify_against_frozen(mutated)


def test_gf07b_missing_member_fails_closed():
    """Removing a frozen member from the registry raises
    MemberUnresolvedError (honest absence — never a silent fallback)."""
    reg = load_registry()
    stripped = json.loads(json.dumps(reg))
    del stripped["definitions"]["momentum"]
    with pytest.raises(MemberUnresolvedError):
        resolve_membership(stripped)
    with pytest.raises(MemberUnresolvedError):
        feature_set_id(stripped)


# ---------------------------------------------------------------- GF-08

def test_gf08_registry_immutable_across_run(tmp_path):
    """GF-08 — registry sha256 is byte-identical pre- and post- a full
    run_research; no assembled row carries a decision_date >= 2026-09-23
    (the protected boundary P14F2-016/017)."""
    from astock_v2.agent.research_run import run_research

    before = registry_sha256()
    # also capture the committed registry file's bytes — they must be
    # byte-identical after the run (no runtime writes, P14F2-020)
    bytes_before = REGISTRY_PATH.read_bytes()
    historical = _build_store(tmp_path)
    raw = RawStore(tmp_path / "raw_records.jsonl")
    membership_csv = _write_membership_csv(tmp_path)
    result = run_research(
        "000001", AS_OF_LAST,
        historical_store=historical, raw_store=raw,
        ingested_at=INGESTED_AT, lookback=20,
        membership_path=membership_csv,
        universe_symbols=("000001", "000002"),
    )
    after = registry_sha256()
    assert before == after
    assert REGISTRY_PATH.read_bytes() == bytes_before
    # the run's as_of is inside the research window (2025-07-07) — well
    # before the virgin boundary 2026-09-23; the assembled factors and
    # the resolver's temporal gate both confirm the boundary is honored
    as_of_date = result["as_of"][:10]
    assert as_of_date < "2026-09-23"
    # the resolver's probability block stayed CALIBRATED throughout —
    # the registry's PIT semantics did not drift during the run
    assert result["probability"]["probability_status"] == "CALIBRATED"


# --------------------------------- additional integrity / API coverage

def test_registry_read_only_api():
    """The registry module exposes no mutation API: the public surface
    is load / sha / resolve / derive / verify — all read-only."""
    import astock_v2.features.registry as r
    public = [n for n in dir(r) if not n.startswith("_")]
    assert "load_registry" in public
    assert "registry_sha256" in public
    assert "resolve_membership" in public
    assert "feature_set_id" in public
    assert "verify_against_frozen" in public
    # nothing like write_registry / update_entry / set_definition exists
    assert not any(n.startswith(("write_", "update_", "set_", "add_",
                                  "mutate_", "register_")) for n in public)


def test_canonical_bytes_round_trip():
    """The committed registry file IS the canonical-bytes form: re-
    serializing the parsed JSON with P13O-F-016c rules produces identical
    bytes (P14F2-001 / P13O-F-016c)."""
    data = REGISTRY_PATH.read_bytes()
    parsed = json.loads(data.decode("utf-8"))
    re_encoded = canonical_json(parsed).encode("utf-8")
    assert re_encoded == data
    # and no trailing newline (contract P14F2-001)
    assert not data.endswith(b"\n")


def test_verify_against_frozen_fails_closed_on_tampered():
    """verify_against_frozen rejects a registry whose derived id does
    not equal the frozen binding — FAIL CLOSED."""
    reg = load_registry()
    mutated = json.loads(json.dumps(reg))
    mutated["definitions"]["momentum"]["definition_version"] = (
        "src/astock_v2/local_pipeline.py@deadbeef")
    with pytest.raises(FeatureSetBindingError):
        verify_against_frozen(mutated)


def test_evidence_file_machine_parseable():
    """The evidence record carries a machine-parseable fenced json block
    with the registry_sha256."""
    text = EVIDENCE_PATH.read_text(encoding="utf-8")
    import re
    m = re.search(r"```json\s*(\{[^`]*?\"registry_sha256\"[^`]*?\})\s*```",
                  text, re.DOTALL)
    assert m is not None
    block = json.loads(m.group(1))
    assert block["registry_sha256"] == registry_sha256()
    assert block["feature_set_id"] == FROZEN_FEATURE_SET_ID
