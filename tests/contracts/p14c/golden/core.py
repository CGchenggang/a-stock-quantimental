"""P14-C golden-fixture validation engine.

This module validates the FROZEN golden fixtures (the standard answers).
It never derives expected results from any P14-C production implementation.
Permitted authority imports (read-only, for cross-checking the standard
answers against frozen upstream contracts):

- P14-A: pit.is_admissible / visible_revisions, freshness.freshness_status
  + FRESHNESS_POLICIES, models.parse_boundary / RawInformationRecord
- P14-B: raw_store.RawStore / RawIngestRecord (durable ingestion semantics)
- P13-U: research_boundary (frozen boundary constants + guard)

Forbidden (anti-cheat): importing scripts/run_p14c_quality_audit or the
P14-C modules information.quality / information.reconciliation /
information.source_health / information.adapters*.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))

from astock_v2.information.freshness import freshness_status  # noqa: E402  P14-A authority
from astock_v2.information.models import RawInformationRecord  # noqa: E402
from astock_v2.information.pit import is_admissible, visible_revisions  # noqa: E402
from astock_v2.information.raw_store import (  # noqa: E402  P14-B authority
    RawIngestRecord,
    RawStore,
)
from astock_v2.information.registry import FRESHNESS_POLICIES  # noqa: E402  P14-A authority
from astock_v2.research_boundary import (  # noqa: E402  P13-U authority
    RESEARCH_END,
    VIRGIN_START,
    assert_research_zone,
)

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
GOLDEN_LAYER_DIR = Path(__file__).resolve().parent
TEST_FILE = Path(__file__).resolve().parent.parent / "test_p14c_golden.py"
CONTRACT_MD = REPO_ROOT / "docs" / "contracts" / "P14-C-DESIGN-CONTRACT.md"
MATRIX_MD = REPO_ROOT / "docs" / "contracts" / "P14-C-ACCEPTANCE-MATRIX.md"

# The contract/matrix are frozen upstream gates; their exact bytes are pinned
# here so any contract edit fails the golden layer loudly (anti-cheat D:
# expected answers may never silently track a moving contract). Re-pinned to
# the independently accepted Contract Repair v4 (441e3fa8).
PINNED_CONTRACT_SHA = {
    "P14-C-DESIGN-CONTRACT.md": "c217f6b984a27cfb6e54322e731f1fe6a381a868e319755191a68290c922167b",
    "P14-C-ACCEPTANCE-MATRIX.md": "fc99637a74b6fb08fea977a6edcb6245c3bce1c2636d9736380da4b5599a3636",
}

VIRGIN_START_FROZEN = "2026-09-23"
RESEARCH_END_FROZEN = "2026-09-22"

BANNED_FIXTURE_TOKENS = [
    "expected_empty", "broken_source", "force_source_error", "fixture_mode",
]
# Boolean/control style of declaring absence: a bare `expected_absence` key
# (e.g. "expected_absence": true). The canonical declaration channel is the
# `expected_absence_pairs` list (Contract §8.3); this is matched as an exact
# JSON key, so the canonical field itself is never flagged.
BANNED_ABSENCE_CONTROL_KEY = "expected_absence"
BANNED_GOLDEN_IMPORTS = [
    "run_p14c_quality_audit", "information.quality", "information.reconciliation",
    "information.source_health", "information.adapters",
]
DET_FORBIDDEN_PATTERNS = ["generated_at", "uuid", "C:\\", "/home/", "time.now"]
MANIFEST_KEYS = ["fixture_count", "fixture_digests", "golden_ids", "schema_version"]

OBS_OUTCOME = {
    "SOURCE_ERROR": "SOURCE_ERROR",
    "PARSE_FAILURE": "REJECTED",
    "SOURCE_EMPTY": "SOURCE_EMPTY",
}

MATRIX_ID = re.compile(r"P14C-[A-Z]+(?:-[A-Z]+)?-\d{3}")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


# --------------------------------------------------------------------- load

def load_fixtures() -> list[dict]:
    paths = sorted(FIXTURE_DIR.glob("*.json"))
    fixtures = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    ids = [f["golden_id"] for f in fixtures]
    assert len(set(ids)) == len(ids), "golden_id must be unique"
    assert ids == sorted(ids), "fixtures must sort by golden_id"
    assert ids == [f"P14C-GOLD-{i:03d}" for i in range(1, len(ids) + 1)], \
        "golden_id sequence must be dense"
    return fixtures


def fixture_digest(fixture: dict) -> str:
    canonical = json.dumps(fixture, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ------------------------------------------------------------ P14-B replay

def _replay(base_dir: Path, raw_records: list[dict], observations: list[dict]):
    store = RawStore(base_dir / "raw_records.jsonl")
    put_outcomes = [store.put(RawIngestRecord(**r)) for r in raw_records]
    for o in observations:
        store.audit_event({
            "outcome": OBS_OUTCOME[o["observation_type"]],
            "source": o["source"],
            "source_id": o.get("source_id"),
            "revision": None,
            "incoming_raw_payload_hash": None,
            "stored_raw_payload_hash": None,
            "ingestion_id": None,
            "adapter_version": o["adapter_version"],
            "error": o.get("error"),
        })
    return store, put_outcomes


def _replay_two_runs(input_: dict, sub: str):
    """Replay the same inputs into two fresh directories; return
    (store2, put_outcomes, byte_identical)."""
    with tempfile.TemporaryDirectory() as tmp:
        a, b = Path(tmp) / "a", Path(tmp) / "b"
        store_a, puts_a = _replay(a, input_.get("raw_records", []), input_.get("observations", []))
        store_b, puts_b = _replay(b, input_.get("raw_records", []), input_.get("observations", []))
        identical = (
            puts_a == puts_b
            and store_a.path.read_bytes() == store_b.path.read_bytes()
            and store_a.audit_path.read_bytes() == store_b.audit_path.read_bytes()
        )
        return store_b, puts_b, identical


# --------------------------------------------------------- record helpers

def _info_record(d: dict) -> RawInformationRecord:
    return RawInformationRecord(
        source=d["source"], source_id=d["source_id"],
        source_category=d.get("source_category", "A_SHARE_MARKET"),
        entity_id=d.get("entity_id", "600000"),
        entity_type=d.get("entity_type", "stock"),
        event_time=d["event_time"], available_time=d["available_time"],
        revision=d.get("revision", 0), ingested_at=d.get("ingested_at", d["event_time"]),
        value=d.get("value", 1.0), quality_status="OK",
        freshness_policy_id=d.get("freshness_policy_id"),
    )


# ------------------------------------------------ pure contract arithmetic

def _pairs(entities: list[str], dates: list[str]) -> set[tuple[str, str]]:
    return {(e, d) for e in entities for d in dates}


def _required_pairs(entry: dict) -> set[tuple[str, str]]:
    all_pairs = _pairs(entry["expected_entities"], entry["expected_dates"])
    absent = {tuple(p) for p in entry.get("expected_absence_pairs", [])}
    return all_pairs - absent


def compute_completeness(fixture: dict) -> dict:
    """Contract §9 arithmetic, computed only from DECLARED sets."""
    inp, exp = fixture["input"], fixture["expected"]
    entry = inp["expected_contract"][next(iter(inp["expected_contract"]))]
    required = _required_pairs(entry)
    actual = {tuple(p) for p in inp["actual_pairs"]}
    entities, dates = set(entry["expected_entities"]), set(entry["expected_dates"])
    a_ent = {e for e, _ in actual}
    a_date = {d for _, d in actual}
    return {
        "expected_count": len(required),
        "actual_count": len(actual & required),
        "missing_entities": sorted(entities - a_ent),
        "missing_dates": sorted(dates - a_date),
        "missing_pairs": sorted(required - actual),
        "coverage_ratio": 1.0 if not required else len(actual & required) / len(required),
        "absence_pairs": sorted({tuple(p) for p in entry.get("expected_absence_pairs", [])}),
    }


MISSINGNESS_ORDER = [
    "SOURCE_ERROR", "PARSE_FAILURE", "SOURCE_EMPTY",
    "EXPECTED_ABSENCE", "UNEXPECTED_MISSING", "UNRESOLVED_AVAILABILITY",
]


def compute_source_health(metrics: dict) -> str:
    """Contract §17 priority table, transcribed verbatim (frozen rules)."""
    if metrics["errors"] > 0 and metrics["accepted"] == 0:
        return "ERROR"
    if metrics["attempted"] > 0 and metrics["accepted"] == 0 and metrics["errors"] == 0:
        return "EMPTY"
    if metrics["stale"] > metrics["fresh"]:
        return "STALE"
    if (metrics["errors"] > 0 or metrics["mutations"] > 0
            or metrics["rejected"] > 0 or metrics["coverage_ratio"] < 1.0):
        return "DEGRADED"
    if metrics["attempted"] == 0 and metrics["accepted"] == 0 and metrics["errors"] == 0:
        return "UNRESOLVED"
    return "OK"


def _parse_ts(value):
    """(kind, dt) where kind in ok / malformed / timezone_missing."""
    try:
        dt = datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return "malformed", None
    if dt.tzinfo is None:
        return "timezone_missing", None
    return "ok", dt


def compute_ts_issues(fixture: dict) -> list[dict]:
    """Contract §10.1 checks, transcribed verbatim."""
    inp = fixture["input"]
    ref = _parse_ts(inp.get("reference_time") or inp["decision_time"])[1]
    issues = []
    for r in inp["ts_records"]:
        for field in ("event_time", "available_time", "ingested_at"):
            kind, dt = _parse_ts(r.get(field))
            if kind == "malformed":
                issues.append({"check": f"{field}_malformed", "key": r["key"],
                               "classification": "VIOLATION"})
            elif kind == "timezone_missing":
                issues.append({"check": "timezone_missing", "key": r["key"],
                               "classification": "VIOLATION"})
            elif dt is not None and ref is not None and dt > ref:
                issues.append({"check": f"{field}_in_future", "key": r["key"],
                               "classification": "VIOLATION"})
        # Contract §10.1: ordering that the source contract cannot attest is
        # reported as UNKNOWN, never guessed, never a VIOLATION.
        if r.get("available_after_event_declared", "n/a") is None:
            issues.append({"check": "available_vs_event_unprovable", "key": r["key"],
                           "classification": "UNKNOWN"})
    return sorted(issues, key=lambda i: (i["key"], i["check"]))


def compute_recon(fixture: dict) -> dict:
    """Contract §15 arithmetic: difference / relative_difference / status."""
    group = fixture["input"]["recon_group"]
    values = [float(e["value"]) for e in group["entries"]]
    diff = abs(max(values) - min(values))
    rel = diff / min(abs(v) for v in values) if values else 0.0
    tol = float(group["policy"]["abs_tolerance"])
    return {
        "difference": diff,
        "relative_difference": rel,
        "status": "CONSISTENT" if diff <= tol else "CONFLICT",
        "policy_id": group["policy"]["policy_id"],
        "policy_version": group["policy"]["policy_version"],
    }


# ------------------------------------------------------------ per-domain checks

def check_fixture(fixture: dict) -> list[tuple[str, bool, str]]:
    """Return [(check_name, ok, detail)] for one fixture. Every check compares
    the hand-written expected block against contract arithmetic or a frozen
    upstream authority (P14-A/P14-B/P13-U) — never a P14-C implementation."""
    out: list[tuple[str, bool, str]] = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), str(detail)))

    fx_id, inp, exp = fixture["golden_id"], fixture["input"], fixture["expected"]
    domain = fixture["domain"]

    if domain == "COMP":
        got = compute_completeness(fixture)
        exp_count = exp.get("expected_count", exp.get("required_expected_count"))
        add("comp.expected_count", got["expected_count"] == exp_count,
            f"got {got['expected_count']} expected {exp_count}")
        add("comp.actual_count", got["actual_count"] == exp["actual_count"],
            f"got {got['actual_count']}")
        add("comp.coverage_ratio", abs(got["coverage_ratio"] - exp["coverage_ratio"]) < 1e-9,
            f"got {got['coverage_ratio']}")
        for key in ("missing_entities", "missing_dates"):
            if key in exp:
                add(f"comp.{key}", got[key] == exp[key], f"got {got[key]}")
        if "missing_pairs" in exp:
            add("comp.missing_pairs", got["missing_pairs"] == [tuple(p) for p in exp["missing_pairs"]],
                f"got {got['missing_pairs']}")
        if "absence_pairs_reported" in exp:
            add("comp.absence_reported",
                got["absence_pairs"] == [tuple(p) for p in exp["absence_pairs_reported"]],
                f"got {got['absence_pairs']}")

    elif domain == "MISS":
        if "classifications" in exp:
            classes = [c["missingness"] for c in exp["classifications"]]
            add("miss.injective", len(classes) == len(set(classes)), f"{classes}")
            add("miss.domain", all(c in MISSINGNESS_ORDER for c in classes), f"{classes}")
        if exp.get("missingness") == "UNRESOLVED_AVAILABILITY" and "raw_records" in inp:
            # P14-B authority: a record without available_time is UNRESOLVED at
            # construction and can never pass PIT admissibility.
            record = RawIngestRecord(**inp["raw_records"][0])
            add("miss.unresolved_at_construction",
                record.quality_status == exp["quality_status"]
                and record.availability_status == exp["availability_status"],
                f"{record.quality_status}/{record.availability_status}")
        if "missingness" in exp and "expected_contract" in inp:
            entry = inp["expected_contract"][next(iter(inp["expected_contract"]))]
            declared = {tuple(p) for p in entry.get("expected_absence_pairs", [])}
            actual = {tuple(p) for p in inp.get("actual_pairs", [])}
            required = _required_pairs(entry)
            missing = required - actual
            undeclared_missing = missing - declared
            if exp["missingness"] == "UNEXPECTED_MISSING":
                add("miss.undeclared_missing_present", bool(undeclared_missing),
                    f"undeclared missing {sorted(undeclared_missing)}")
                add("miss.not_declared_absence", all(
                    p not in declared for p in map(tuple, exp.get("undeclared_missing_pair", []))),
                    "missing pair must not be declared intentional")

    elif domain == "EXP":
        entry = inp["expected_contract"][next(iter(inp["expected_contract"]))]
        if "expected_pairs" in exp:
            got = sorted(_pairs(entry["expected_entities"], entry["expected_dates"]))
            add("exp.cartesian", got == sorted(map(tuple, exp["expected_pairs"])), f"{got}")
        if "entities_in_expected_but_not_in_actual" in exp:
            actual_e = {p[0] for p in inp.get("actual_pairs", [])}
            diff = set(entry["expected_entities"]) - actual_e
            add("exp.expected_not_derived_from_actual", bool(diff),
                f"expected-only entities {sorted(diff)}")
        if "expected_contract_unchanged" in exp:
            add("exp.failure_invariance",
                entry["expected_entities"] == exp["expected_entities_after_failure"]
                and entry["expected_dates"] == exp["expected_dates_after_failure"])
        add("exp.single_entry_per_source", len(inp["expected_contract"])
            == exp.get("source_keys_count", len(inp["expected_contract"])))

    elif domain == "TS":
        if "issues" in exp:
            got = compute_ts_issues(fixture)
            want = sorted(exp["issues"], key=lambda i: (i["key"], i["check"]))
            add("ts.issue_set", got == want, f"got {got} want {want}")
        if "pit_admissible" in exp:
            r = inp["ts_records"][0]
            kind, avail = _parse_ts(r["available_time"])
            kind_d, dec = _parse_ts(inp["decision_time"])
            add("ts.pit_uses_available",
                avail is not None and dec is not None
                and (avail <= dec) == exp["pit_admissible"])

    elif domain == "PIT":
        decision = inp["decision_time"]
        for r in inp["info_records"]:
            want = exp["admissibility"][r["source_id"]]
            add(f"pit.{r['source_id']}", is_admissible(_info_record(r), decision) == want,
                f"P14-A is_admissible vs {want}")

    elif domain == "REV":
        if "visible_revision_at_decision" in exp:
            recs = [_info_record(r) for r in inp["info_records"]]
            visible = visible_revisions(recs, inp["decision_time"])
            for key, rev in exp["visible_revision_at_decision"].items():
                got = [r for (src, sid), r in visible.items() if sid == key]
                add(f"rev.visible.{key}",
                    len(got) == 1 and got[0].revision == rev,
                    f"P14-A visible_revisions -> {[(r.source_id, r.revision) for r in got]}")
        elif "raw_records" in inp:
            with tempfile.TemporaryDirectory() as tmp:
                store, puts = _replay(Path(tmp), inp["raw_records"],
                                      inp.get("observations", []))
                _check_rev_replay(store, puts, inp, exp, add)

    elif domain in ("EVID", "RR", "DET"):
        if domain == "DET" and not inp:
            # DET-002: this fixture's own canonical serialization carries no
            # runtime timestamp / UUID / machine path.
            if "forbidden_patterns" in exp:
                probe = dict(fixture)
                probe["expected"] = {k: v for k, v in exp.items()
                                     if k != "forbidden_patterns"}
                own = json.dumps(probe, sort_keys=True, ensure_ascii=False)
                hits = [p for p in exp["forbidden_patterns"] if p in own]
                add("det.no_runtime_patterns", not hits, f"hits {hits}")
            # DET-003: the frozen manifest schema excludes dynamic timestamps.
            if "manifest_keys" in exp:
                add("det.manifest_keys_frozen",
                    sorted(exp["manifest_keys"]) == sorted(MANIFEST_KEYS)
                    and not (set(exp["manifest_forbidden_keys"]) & set(MANIFEST_KEYS)),
                    f"{exp['manifest_keys']}")
            return out
        with tempfile.TemporaryDirectory() as tmp:
            store, puts = _replay(Path(tmp), inp.get("raw_records", []),
                                  inp.get("observations", []))
            add(f"{domain.lower()}.put_outcomes", puts == exp.get(
                "put_outcomes", exp.get("audit_outcome_sequence", puts)), f"{puts}")
            if "observation_audit_outcomes" in exp:
                got = [e["outcome"] for e in store.outcomes()
                       if e["outcome"] in ("SOURCE_ERROR", "REJECTED", "SOURCE_EMPTY")]
                add(f"{domain.lower()}.obs_outcomes", got == exp["observation_audit_outcomes"],
                    f"{got}")
            if "canonical_record_count" in exp:
                add(f"{domain.lower()}.record_count",
                    len(store.records()) == exp["canonical_record_count"])
            if "empty_event_has_raw_payload_hash" in exp:
                for e in store.outcomes():
                    if e["outcome"] == "SOURCE_EMPTY":
                        add(f"{domain.lower()}.empty_no_hash_or_id",
                            not e.get("incoming_raw_payload_hash") and not e.get("ingestion_id"),
                            f"{e}")
            if "audit_outcome_sequence_after_restart" in exp:
                reopened = RawStore(store.path)
                got = [e["outcome"] for e in reopened.outcomes()]
                add(f"{domain.lower()}.restart_recovery",
                    got == exp["audit_outcome_sequence_after_restart"], f"{got}")
                if "canonical_record_count_after_restart" in exp:
                    add(f"{domain.lower()}.restart_record_count",
                        len(reopened.records()) == exp["canonical_record_count_after_restart"])
            if exp.get("outcomes_distinct"):
                got = [e["outcome"] for e in store.outcomes()]
                add(f"{domain.lower()}.outcomes_distinguishable",
                    len(set(got)) == len(got) and got == exp["observation_audit_outcomes"], f"{got}")
            if exp.get("byte_identical_rerun"):
                _, puts2, identical = _replay_two_runs(inp, "det")
                add(f"{domain.lower()}.byte_identical_rerun", identical)

    elif domain in ("DUP", "RECON"):
        group_key = "conflict_group" if domain == "DUP" else "recon_group"
        group = inp[group_key]
        values = [e["value"] for e in group["entries"]]
        if domain == "RECON":
            got = compute_recon(fixture)
            add("recon.status", got["status"] == exp["status"], f"{got['status']}")
            if "difference" in exp:
                add("recon.difference", abs(got["difference"] - exp["difference"]) < 1e-9,
                    f"{got['difference']}")
            if "relative_difference" in exp:
                add("recon.relative_difference",
                    abs(got["relative_difference"] - exp["relative_difference"]) < 1e-9,
                    f"{got['relative_difference']}")
            if "policy_id" in exp:
                add("recon.policy_versioned",
                    got["policy_id"] == exp["policy_id"]
                    and got["policy_version"] == exp["policy_version"])
        if "conflict_detected" in exp:
            distinct = len(set(values)) > 1
            add(f"{domain.lower()}.conflict_detected", distinct == exp["conflict_detected"])
        if "preserved_values" in exp:
            add(f"{domain.lower()}.values_preserved",
                sorted(values) == sorted(exp["preserved_values"]), f"{sorted(values)}")
        if "preserved_sources" in exp:
            add(f"{domain.lower()}.sources_preserved",
                sorted(e["source"] for e in group["entries"]) == sorted(exp["preserved_sources"]))
        for field_list in ("entry_fields_required", "provenance_fields_required"):
            if field_list in exp:
                add(f"{domain.lower()}.{field_list}",
                    all(all(f in e for f in exp[field_list]) for e in group["entries"]),
                    f"fields {exp[field_list]}")
        if "group_fields_required" in exp:
            add(f"{domain.lower()}.group_fields",
                sorted(exp["group_fields_required"])
                == sorted(["difference", "relative_difference", "policy_id",
                           "policy_version", "status"]))
        if "forbidden_output_fields" in exp:
            allowed = set(exp.get("entry_fields_required", [])) | set(
                exp.get("group_fields_required", [])) | {"preserved_values"}
            add(f"{domain.lower()}.no_forbidden_fields",
                not (set(exp["forbidden_output_fields"]) & allowed),
                f"forbidden {exp['forbidden_output_fields']} vs allowed {sorted(allowed)}")
        if "status" in exp and domain == "DUP":
            add(f"{domain.lower()}.status_unresolved", exp["status"] == "CONFLICT")

    elif domain == "PROV":
        if "raw_records" in inp:
            with tempfile.TemporaryDirectory() as tmp:
                store, _ = _replay(Path(tmp), inp["raw_records"], [])
                rec = store.records()[0].as_dict()
                add("prov.type_a_fields",
                    all(f in rec for f in exp["record_provenance_fields_required"]),
                    f"missing {[f for f in exp['record_provenance_fields_required'] if f not in rec]}")
        else:
            for o in inp["observations"]:
                add("prov.type_b_no_payload_hash",
                    "raw_payload_hash" not in o and not exp["raw_payload_hash_required"])
            add("prov.type_b_fields_declared",
                set(exp["observation_provenance_fields_required"]) >= {"source", "source_id",
                                                                       "observation_type", "observed_at"})

    elif domain == "SH":
        got = compute_source_health(inp["metrics"])
        add("sh.health", got == exp["health"], f"got {got} want {exp['health']}")

    elif domain == "FRESH":
        for r in inp["info_records"]:
            want = exp["freshness"][r["source_id"]]
            got = freshness_status(_info_record(r), inp["decision_time"], FRESHNESS_POLICIES)
            add(f"fresh.{r['source_id']}", got.upper() == want, f"P14-A -> {got}, want {want}")
        for r in inp.get("unresolved_records", []):
            add(f"fresh.{r['source_id']}",
                r["available_time"] is None
                and exp["freshness"][r["source_id"]] == "UNRESOLVED")
        if "policy_id" in exp:
            add("fresh.policy_from_p14a_registry", exp["policy_id"] in FRESHNESS_POLICIES)

    elif domain == "BND":
        if "RESEARCH_END" in exp:
            add("bnd.research_end", RESEARCH_END == exp["RESEARCH_END"] == RESEARCH_END_FROZEN)
        if "VIRGIN_START" in exp:
            add("bnd.virgin_start", VIRGIN_START == exp["VIRGIN_START"] == VIRGIN_START_FROZEN)
        if exp.get("assert_research_zone_raises"):
            try:
                assert_research_zone([inp["violating_decision_date"]])
                add("bnd.guard_raises", False, "guard did not raise")
            except ValueError:
                add("bnd.guard_raises", True)
        if "factor_registry_sha256" in exp:
            from astock_v2.factors import FACTOR_REGISTRY
            reg = json.dumps({k: v.__name__ for k, v in sorted(FACTOR_REGISTRY.items())},
                             sort_keys=True)
            digest = hashlib.sha256(reg.encode()).hexdigest()
            add("bnd.factor_registry_frozen", digest == exp["factor_registry_sha256"],
                f"{digest}")
            add("bnd.factor_count", len(FACTOR_REGISTRY) == exp["factor_count"])

    return out


def _by_source_id(store: RawStore) -> dict[str, list]:
    out: dict[str, list] = {}
    for r in store.records():
        out.setdefault(r.source_id, []).append(r)
    return out


def _check_rev_replay(store, puts, inp, exp, add):
    add("rev.put_outcomes", puts == exp["put_outcomes"], f"{puts}")
    add("rev.record_count", len(store.records()) == exp["canonical_record_count"],
        f"{len(store.records())}")
    if "revision_gaps" in exp:
        for src_id, recs in _by_source_id(store).items():
            revs = sorted(r.revision for r in recs)
            gaps = [r for r in range(revs[0], revs[-1]) if r not in revs] if len(revs) > 1 else []
            want = next((g["missing_revisions"] for g in exp["revision_gaps"]
                         if g["source_id"] == src_id), [])
            add(f"rev.gap.{src_id}", gaps == want, f"got {gaps} want {want}")
    if "available_time_regressions" in exp:
        for g in exp["available_time_regressions"]:
            recs = sorted(_by_source_id(store)[g["source_id"]], key=lambda r: r.revision)
            reg = any(_parse_ts(recs[i + 1].available_time)[1]
                      < _parse_ts(recs[i].available_time)[1]
                      for i in range(len(recs) - 1))
            add(f"rev.regression.{g['source_id']}", reg is True, f"regression={reg}")
            add("rev.regression_retained",
                len(store.records()) == exp["canonical_record_count"])
    if "original_payload_preserved" in exp:
        recs = _by_source_id(store)[inp["raw_records"][0]["source_id"]]
        payloads = {r.raw_payload_hash for r in recs}
        add("rev.original_preserved", len(payloads) == 1
            and payloads == {RawIngestRecord(**inp["raw_records"][0]).raw_payload_hash})


# ------------------------------------------------------------- global gates

def check_schema(fixtures: list[dict]) -> list[tuple[str, bool, str]]:
    out = []
    for f in fixtures:
        ok = (set(f) >= {"golden_id", "domain", "title", "contract_ids",
                         "matrix_ids", "input", "expected", "evidence"}
              and f["contract_ids"] == f["matrix_ids"]
              and all(MATRIX_ID.fullmatch(c) for c in f["contract_ids"]))
        out.append((f"schema.{f['golden_id']}", ok, ""))
    return out


def check_boundary_dates(fixtures: list[dict]) -> list[tuple[str, bool, str]]:
    """Every calendar date inside any fixture input must be < VIRGIN_START.
    The single sanctioned exception is BND-003's ``violating_decision_date``
    — a date whose ONLY consumer is the guard test proving it is rejected."""
    out = []
    for f in fixtures:
        payload = {k: v for k, v in f["input"].items() if k != "violating_decision_date"}
        text = json.dumps(payload, ensure_ascii=False)
        dates = ISO_DATE.findall(text)
        bad = sorted(d for d in dates if d >= VIRGIN_START_FROZEN)
        out.append((f"boundary.{f['golden_id']}", not bad, f"virgin dates {bad}"))
    return out


def _all_keys(obj) -> list:
    if isinstance(obj, dict):
        keys = list(obj.keys())
        for v in obj.values():
            keys += _all_keys(v)
        return keys
    if isinstance(obj, list):
        keys = []
        for item in obj:
            keys += _all_keys(item)
        return keys
    return []


def check_anticheat_fixtures(fixtures: list[dict]) -> list[tuple[str, bool, str]]:
    out = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        hits = [t for t in BANNED_FIXTURE_TOKENS if t in text]
        data = json.loads(text)
        control_keys = [k for k in _all_keys(data) if k == BANNED_ABSENCE_CONTROL_KEY]
        out.append((f"anticheat.fixture.{path.name}", not hits and not control_keys,
                    f"banned tokens {hits} / control keys {control_keys}"))
    return out


def check_absence_declaration_scope(fixtures: list[dict]) -> list[tuple[str, bool, str]]:
    """Contract §8.3 rule 3: every declared expected_absence pair must lie in
    E x D for its source; out-of-scope declarations are contract structure
    errors and fail the golden layer."""
    out = []
    for f in fixtures:
        for source_id, entry in (f["input"].get("expected_contract") or {}).items():
            declared = {tuple(p) for p in entry.get("expected_absence_pairs", [])}
            scope = _pairs(entry["expected_entities"], entry["expected_dates"])
            bad = sorted(declared - scope)
            out.append((f"absence_scope.{f['golden_id']}.{source_id}", not bad,
                        f"out-of-scope declarations {bad}"))
    return out


def check_anticheat_layer() -> list[tuple[str, bool, str]]:
    """Import-statement scan of the golden layer (line-based so that the
    banned-module name list itself cannot self-match)."""
    import_line = re.compile(r"^\s*(from|import)\s")
    out = []
    for path in [TEST_FILE, *sorted(GOLDEN_LAYER_DIR.glob("*.py"))]:
        hits = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if import_line.match(line):
                hits += [t for t in BANNED_GOLDEN_IMPORTS if t in line]
        out.append((f"anticheat.layer.{path.name}", not hits, f"banned imports {hits}"))
    return out


def check_contract_pinned() -> list[tuple[str, bool, str]]:
    out = []
    for name, pinned in PINNED_CONTRACT_SHA.items():
        path = CONTRACT_MD if "DESIGN" in name else MATRIX_MD
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        out.append((f"pin.{name}", digest == pinned, f"{digest}"))
    return out


def matrix_ids() -> set[str]:
    return set(MATRIX_ID.findall(MATRIX_MD.read_text(encoding="utf-8")))


def check_coverage(fixtures: list[dict]) -> list[tuple[str, bool, str]]:
    covered = {c for f in fixtures for c in f["contract_ids"]}
    missing = sorted(matrix_ids() - covered)
    return [("coverage.matrix_closure", not missing, f"uncovered {missing}"),
            ("coverage.count", len(matrix_ids()) == 61, f"{len(matrix_ids())}")]


def check_recon_001_vs_006(fixtures: list[dict]) -> list[tuple[str, bool, str]]:
    """Mandate §26: prove RECON-001 and RECON-006 carry distinct semantics."""
    by_id = {f["golden_id"]: f for f in fixtures}
    recon1 = next(f for f in fixtures if f["contract_ids"] == ["P14C-RECON-001"])
    recon6 = next(f for f in fixtures if f["contract_ids"] == ["P14C-RECON-006"])
    distinct = (
        "classification_source" in recon1["expected"]            # tolerance semantics
        and "forbidden_output_fields" in recon6["expected"]      # schema semantics
        and recon1["expected"]["status"] == "CONSISTENT"
        and recon6["expected"]["status"] == "CONFLICT"
    )
    return [("recon.distinct_semantics", distinct,
             "RECON-001 = tolerance classification; RECON-006 = output-schema prohibition"),
            ("recon.both_present", recon1["golden_id"] in by_id and recon6["golden_id"] in by_id,
             f"{recon1['golden_id']} / {recon6['golden_id']}")]


# ------------------------------------------------------ deterministic report

def canonical_report() -> str:
    fixtures = load_fixtures()
    validations = []
    for f in fixtures:
        results = check_fixture(f)
        validations.append({
            "golden_id": f["golden_id"],
            "digest": fixture_digest(f),
            "checks": [{"check": n, "ok": ok, "detail": d} for n, ok, d in results],
            "passed": all(ok for _, ok, _ in results),
        })
    validations.sort(key=lambda v: v["golden_id"])
    manifest = {
        "schema_version": "p14c-golden-manifest-v1",
        "fixture_count": len(fixtures),
        "golden_ids": [f["golden_id"] for f in fixtures],
        "fixture_digests": {v["golden_id"]: v["digest"] for v in validations},
    }
    report = {"manifest": manifest, "validation": validations}
    return json.dumps(report, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def run_all_checks() -> list[tuple[str, bool, str]]:
    fixtures = load_fixtures()
    out: list[tuple[str, bool, str]] = []
    out += check_schema(fixtures)
    out += check_boundary_dates(fixtures)
    out += check_anticheat_fixtures(fixtures)
    out += check_absence_declaration_scope(fixtures)
    out += check_anticheat_layer()
    out += check_contract_pinned()
    out += check_coverage(fixtures)
    out += check_recon_001_vs_006(fixtures)
    for f in fixtures:
        for name, ok, detail in check_fixture(f):
            out.append((f"{f['golden_id']}.{name}", ok, detail))
    return out


def det_report_clean() -> list[tuple[str, bool, str]]:
    report = canonical_report()
    hits = [p for p in DET_FORBIDDEN_PATTERNS if p in report]
    manifest_keys = sorted(json.loads(report)["manifest"].keys())
    return [
        ("det.no_runtime_patterns", not hits, f"hits {hits}"),
        ("det.manifest_keys_frozen", manifest_keys == sorted(MANIFEST_KEYS),
         f"{manifest_keys}"),
        ("det.report_byte_identical_rerun", canonical_report() == report,
         "canonical_report() rebuilt byte-identical"),
    ]
