"""P14-E golden-fixture validation engine.

Validates the FROZEN golden fixtures (G-001..G-012) against the frozen
P14-E Contract semantics, using ONLY frozen upstream authorities:

- P14-B: RawStore / RawIngestRecord / canonical identity primitives
  (raw_payload_hash, ingestion_id, DUPLICATE / RAW_MUTATION_DETECTED).
- P14-A: to_information_record projection, is_admissible /
  visible_revisions (version selection chain), parse_boundary.
- P14-D: run_query (PIT filtering, exclusions, result_id).
- P13-U: research_boundary guard.

The evidence/bundle arithmetic here is the TRANSCRIBED CONTRACT (§4/§7/§8),
living in the test layer as the standard-answer engine — it is NOT a
production runtime: this module must never be imported by src/, and no
P14-E production module may exist (mechanically asserted, P14E-016).

Deterministic: no wall-clock, UUID, randomness, or environment value
enters any result; canonical serialization is sort_keys + compact
separators throughout.
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys_path = str(REPO_ROOT / "src")
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from astock_v2.information.models import RawInformationRecord  # noqa: E402
from astock_v2.information.pit import is_admissible  # noqa: E402
from astock_v2.information.raw_store import (  # noqa: E402  P14-B authority
    RawIngestRecord,
    RawStore,
)
from astock_v2.information.research_query import (  # noqa: E402  P14-D authority
    ResearchQuery,
    run_query,
)
from astock_v2.information.raw_store import to_information_record  # noqa: E402

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
P14E_LAYER_DIR = Path(__file__).resolve().parent.parent
SRC_INFO_DIR = REPO_ROOT / "src" / "astock_v2" / "information"
CONTRACT_MD = REPO_ROOT / "docs" / "contracts" / "P14-E-DESIGN-CONTRACT.md"
MATRIX_MD = REPO_ROOT / "docs" / "contracts" / "P14-E-ACCEPTANCE-MATRIX.md"
GOLDEN_DESIGN_MD = REPO_ROOT / "docs" / "contracts" / "P14-E-GOLDEN-DESIGN.md"

# Frozen baseline: the information layer contains exactly these modules.
# A P14-E production runtime (evidence*/bundle*/...) appearing here fails
# the Harness (P14E-016: implementation NOT AUTHORIZED in this stage).
PINNED_INFO_FILES = sorted([
    "__init__.py", "adapters.py", "adapters_fixture.py", "conflict.py",
    "dedup.py", "expected_contract.py", "freshness.py", "models.py",
    "normalization.py", "pit.py", "provenance.py", "quality.py",
    "raw_store.py", "reconciliation.py", "registry.py",
    "research_boundary_guard.py", "research_query.py", "source_health.py",
])

BANNED_SRC_TOKENS = ["fixture_mode", "expected_result_override",
                     "golden_override", "test_only", "skip_validation",
                     "force_visible", "force_hidden", "running_under_test"]

IDENTITY_FIELDS = ["source", "source_id", "revision", "event_time",
                   "available_time", "adapter_version", "raw_payload_hash",
                   "ingestion_id"]
EVIDENCE_FIELDS = IDENTITY_FIELDS + ["entity_id", "information_type",
                                     "ingested_at"]
EXCLUSION_FIELD_SET = {"source", "source_id", "reason", "available_time"}
VIRGIN_START = "2026-09-23"
SYNTHETIC_FUTURE_CUTOFF = "2028-01-01"
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

SELECTED_HIGHEST = "SELECTED_HIGHEST_REVISION"
SELECTED_EARLIEST_TIE = "SELECTED_EARLIEST_ON_REVISION_TIE"
SELECTED_CANONICAL = "SELECTED_CANONICAL_TIEBREAK"
REJECTED_LOWER = "REJECTED_LOWER_REVISION"
REJECTED_TIE_NOT_EARLIEST = "REJECTED_REVISION_TIE_NOT_EARLIEST"
REJECTED_CANONICAL = "REJECTED_CANONICAL_TIEBREAK"


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------- record layer

def build_records(record_dicts: list[dict]) -> list[RawIngestRecord]:
    """P14-B authority: identity primitives computed at construction."""
    return [RawIngestRecord(**r) for r in record_dicts]


def ingest_into_store(records: list[RawIngestRecord], base_dir: Path):
    store = RawStore(base_dir / "raw_records.jsonl")
    outcomes = [store.put(r) for r in records]
    return store, outcomes


def project(record: RawIngestRecord) -> RawInformationRecord:
    return to_information_record(record)


def evidence_from(record: RawIngestRecord) -> dict:
    """Contract §4: identity + audit fields, evidence_id over the 8
    Identity fields ONLY (ingested_at is Audit-only)."""
    evidence = {
        "source": record.source,
        "source_id": record.source_id,
        "revision": record.revision,
        "event_time": record.event_time,
        "available_time": record.available_time,
        "adapter_version": record.adapter_version,
        "raw_payload_hash": record.raw_payload_hash,
        "ingestion_id": record.ingestion_id,
        "entity_id": record.entity_id,
        "information_type": record.entity_type,
        "ingested_at": record.ingested_at,
    }
    identity = {k: evidence[k] for k in IDENTITY_FIELDS}
    evidence["evidence_id"] = _sha(canonical_json(identity))
    return evidence


def check_provenance_complete(evidence: dict):
    """Contract P14E-002/P14E-011: all fields must exist; no defaults.
    revision == 0 is a legitimate value — only None / empty-string count
    as missing."""
    missing = [f for f in EVIDENCE_FIELDS
               if evidence.get(f) is None or evidence.get(f) == ""]
    if missing:
        raise ValueError(f"provenance incomplete, missing: {sorted(missing)}")


def check_mutation(records: list[RawIngestRecord]):
    """Contract P14E-012: same (source, source_id, revision) with distinct
    raw_payload_hash among candidates -> fail-fast (P14-B authority is the
    mutation detector; the bundle layer refuses to pick a winner)."""
    seen: dict[tuple, set] = {}
    for r in records:
        seen.setdefault((r.source, r.source_id, r.revision), set()).add(
            r.raw_payload_hash)
    for key, hashes in seen.items():
        if len(hashes) > 1:
            raise ValueError(
                f"mutation detected for lineage {key}: "
                f"{len(hashes)} distinct payload hashes")


def select_lineage(candidates: list[RawIngestRecord], winner) -> tuple[str, list[dict]]:
    """Frozen selection chain (P14-D/P14-A): highest revision -> earliest
    available_time -> smallest canonical_json. Returns (winner reason,
    rejection trace). Canonical text = P14-B record dict serialization."""
    def _cand_key(r: RawIngestRecord):
        return (r.revision, r.available_time, canonical_json(r.as_dict()))

    trace = []
    for cand in sorted(candidates, key=_cand_key):
        if cand is winner:
            continue
        if cand.revision < winner.revision:
            trace.append({"source": cand.source, "source_id": cand.source_id,
                          "revision": cand.revision,
                          "available_time": cand.available_time,
                          "raw_payload_hash": cand.raw_payload_hash,
                          "ingested_at": cand.ingested_at,
                          "rejection_reason": REJECTED_LOWER})
        elif cand.revision == winner.revision and \
                cand.available_time > winner.available_time:
            trace.append({"source": cand.source, "source_id": cand.source_id,
                          "revision": cand.revision,
                          "available_time": cand.available_time,
                          "raw_payload_hash": cand.raw_payload_hash,
                          "ingested_at": cand.ingested_at,
                          "rejection_reason": REJECTED_TIE_NOT_EARLIEST})
        else:
            trace.append({"source": cand.source, "source_id": cand.source_id,
                          "revision": cand.revision,
                          "available_time": cand.available_time,
                          "raw_payload_hash": cand.raw_payload_hash,
                          "ingested_at": cand.ingested_at,
                          "rejection_reason": REJECTED_CANONICAL})
    same_rev = [c for c in candidates
                if c.revision == winner.revision and c is not winner]
    if not same_rev:
        reason = SELECTED_HIGHEST
    elif all(c.available_time > winner.available_time for c in same_rev):
        reason = SELECTED_EARLIEST_TIE
    else:
        reason = SELECTED_CANONICAL
    return reason, trace


def build_bundle(record_dicts: list[dict], query_dict: dict,
                 use_raw_store: bool = False, base_dir: Path | None = None):
    """Contract §7.1 bundle construction from P14-D run_query + frozen
    §4/§6/§8 semantics. Returns (bundle, put_outcomes, store_or_None).
    When use_raw_store with base_dir=None an internal temp dir is used and
    cleaned up on return; pass base_dir to keep the store readable."""
    records = build_records(record_dicts)
    check_mutation(records)
    put_outcomes: list[str] = []
    store = None
    if use_raw_store:
        if base_dir is None:
            with tempfile.TemporaryDirectory() as tmp:
                store, put_outcomes = ingest_into_store(records, Path(tmp))
                stored = store.records()
                bundle = _assemble(stored, list(records), query_dict, put_outcomes)
                return bundle, put_outcomes, store
        store, put_outcomes = ingest_into_store(records, base_dir)
        stored = store.records()
        bundle = _assemble(stored, list(records), query_dict, put_outcomes)
        return bundle, put_outcomes, store
    stored = records
    bundle = _assemble(stored, list(records), query_dict, put_outcomes)
    return bundle, put_outcomes, store


def _assemble(stored: list[RawIngestRecord], all_records: list[RawIngestRecord],
              query_dict: dict, put_outcomes: list[str]) -> dict:
    # provenance completeness over every candidate (P14E-002/011)
    evidences_by_key = {}
    for r in stored:
        ev = evidence_from(r)
        check_provenance_complete(ev)
        evidences_by_key[(r.source, r.source_id, r.revision)] = ev
    info_records = [project(r) for r in stored]
    query = ResearchQuery(**query_dict)
    result = run_query(info_records, query)

    selected_keys = {(r["source"], r["source_record_id"], r["revision"],
                      r["ingested_at"])
                     for r in result["records"]}
    evidence: list[dict] = []
    trace: list[dict] = []
    lineages: dict[tuple, list[RawIngestRecord]] = {}
    for r in stored:
        lineages.setdefault((r.source, r.source_id), []).append(r)
    for key in sorted(lineages):
        cands = lineages[key]
        admissible = [r for r in cands if is_admissible(project(r), query.as_of)]
        winner_key = next((k for k in selected_keys
                           if (k[0], k[1]) == (key[0], key[1])), None)
        if winner_key is None:
            # every record of this lineage is excluded (NOT_YET_AVAILABLE /
            # OUTSIDE_AS_OF / UNRESOLVED) — represented solely by the P14-D
            # exclusion entry; no evidence, no candidate trace
            continue
        winner = next(r for r in admissible
                      if (r.source, r.source_id, r.revision,
                          r.ingested_at) == winner_key)
        reason, cand_trace = select_lineage(admissible, winner)
        ev = dict(evidences_by_key[(winner.source, winner.source_id,
                                    winner.revision)])
        ev["selection_reason"] = reason
        evidence.append(ev)
        trace.extend(cand_trace)
    evidence.sort(key=lambda e: (e["source"], e["source_id"], e["revision"]))
    trace.sort(key=lambda t: (t["source"], t["source_id"], t["revision"],
                              t["available_time"], t["raw_payload_hash"]))
    # P14E-008: candidate trace entries are unique by their identity key —
    # exact duplicate candidates collapse to one trace entry
    unique_trace: list[dict] = []
    seen_keys = set()
    for t in trace:
        key = (t["source"], t["source_id"], t["revision"],
               t["available_time"], t["raw_payload_hash"])
        if key not in seen_keys:
            seen_keys.add(key)
            unique_trace.append(t)
    trace = unique_trace

    bundle = {
        "schema_version": "p14e-evidence-bundle-1",
        "query": result["query"],
        "as_of": query.as_of,
        "result_id": result["result_id"],
        "evidence": evidence,
        "candidate_trace": trace,
        "exclusions": result["excluded"],
        "counts": {"evidence": len(evidence), "candidates": len(trace),
                   "exclusions": len(result["excluded"]),
                   "examined": len(stored)},
    }
    bundle["bundle_id"] = _sha(canonical_json(bundle))
    return bundle


# ------------------------------------------------------------- persistence

def persist_bundle(path: Path, bundle: dict) -> bool:
    """Contract §12: append-only JSONL; duplicate bundle_id rejected."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line)["bundle_id"] == bundle["bundle_id"]:
                return False
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(canonical_json(bundle) + "\n")
    return True


def reload_verify(path: Path) -> list[dict]:
    """Contract §12: reload recomputes every bundle_id."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        bundle = json.loads(line)
        stored_id = bundle.pop("bundle_id")
        if _sha(canonical_json(bundle)) != stored_id:
            raise ValueError("reload verification failed")
        bundle["bundle_id"] = stored_id
        out.append(bundle)
    return out


# --------------------------------------------------------- per-fixture checks

def check_fixture(fixture: dict) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), str(detail)))

    gid = fixture["golden_id"]
    inp, exp = fixture["input"], fixture["expected"]
    q = inp["query"]

    if gid == "P14E-G-001":
        a, b, c = inp["records"]
        id_ab1 = build_bundle([a, b], q)[0]["evidence"][0]["evidence_id"]
        id_ab2 = build_bundle([b, a], q)[0]["evidence"][0]["evidence_id"]
        id_a = build_bundle([a], q)[0]["evidence"][0]["evidence_id"]
        id_c = build_bundle([c], q)[0]["evidence"][0]["evidence_id"]
        add("g001.ab_order_invariant", id_ab1 == id_ab2)
        add("g001.ab_equal", id_ab1 == id_a)
        add("g001.c_differs", id_c != id_a)
        with tempfile.TemporaryDirectory() as tmp:
            bundle_rt, _, store_rt = build_bundle([a, b], q,
                                                  use_raw_store=True,
                                                  base_dir=Path(tmp))
            raw_text = store_rt.path.read_text(encoding="utf-8")
        ev = bundle_rt["evidence"][0]
        add("g001.identity_fields",
            all(f in ev for f in exp["identity_fields"]))
        add("g001.audit_fields", all(f in ev for f in exp["audit_fields_present"]))
        add("g001.reverse_trace",
            all(ev[f] in raw_text for f in exp["reverse_trace_fields"]))

    elif gid == "P14E-G-002":
        with tempfile.TemporaryDirectory() as tmp:
            bundle, outcomes, store = build_bundle(
                inp["records"], q, use_raw_store=True)
            add("g002.put_outcomes", outcomes == exp["put_outcomes"], f"{outcomes}")
            add("g002.evidence_count", bundle["counts"]["evidence"] == exp["evidence_count"])
            ev = bundle["evidence"][0]
            add("g002.stored_ingested_at",
                ev["ingested_at"] == exp["stored_ingested_at"], ev["ingested_at"])
            single = build_bundle([inp["records"][0]], q)[0]
            add("g002.no_fork",
                ev["evidence_id"] == single["evidence"][0]["evidence_id"])
            bundle_text = canonical_json(bundle)
            add("g002.duplicate_absent",
                "2026-03-03T09:00:00+08:00" not in bundle_text)
            add("g002.stored_record_only",
                bundle["counts"]["examined"] == 1)

    elif gid == "P14E-G-003":
        bundle, _, _ = build_bundle(inp["records"], q)
        got_visible = sorted(e["source_id"] for e in bundle["evidence"])
        add("g003.visible", got_visible == sorted(exp["visible_source_ids"]),
            f"{got_visible}")
        got_excl = sorted((e["source_id"], e["reason"])
                          for e in bundle["exclusions"])
        want_excl = sorted((e["source_id"], e["reason"])
                           for e in exp["exclusions"])
        add("g003.exclusions", got_excl == want_excl, f"{got_excl}")
        for e in bundle["exclusions"]:
            add("g003.exclusion_fields",
                set(e) == EXCLUSION_FIELD_SET, f"{sorted(e)}")
        add("g003.counts", bundle["counts"] == exp["counts"],
            f"{bundle['counts']}")

    elif gid in ("P14E-G-004", "P14E-G-007"):
        bundle1, _, _ = build_bundle(inp["records"], q)
        bundle2 = None
        if gid == "P14E-G-007":
            bundle2, _, _ = build_bundle(
                inp["records"], {**q, "as_of": inp["second_query_as_of"]})
        b1_expected_revision = (exp["bundle1"]["selected_revision"]
                                if gid == "P14E-G-007"
                                else exp["selected_revision"])
        add(f"{gid}.b1_revision",
            bundle1["evidence"][0]["revision"] == b1_expected_revision)
        b1_text = canonical_json(bundle1)
        rev1 = next(r for r in inp["records"] if r["revision"] == 1)
        rev1_hash = RawIngestRecord(**rev1).raw_payload_hash
        rev1_ing = RawIngestRecord(**rev1).ingestion_id
        add(f"{gid}.rev1_hash_absent", rev1_hash not in b1_text)
        add(f"{gid}.rev1_ingid_absent", rev1_ing not in b1_text)
        add(f"{gid}.rev1_payload_absent",
            canonical_json(rev1["raw_payload"]) not in b1_text)
        lineage_source_id = next(r["source_id"] for r in inp["records"]
                                 if r["revision"] == 1)
        excl = next(e for e in bundle1["exclusions"]
                    if e["source_id"] == lineage_source_id)
        add(f"{gid}.exclusion_fields", set(excl) == EXCLUSION_FIELD_SET,
            f"{sorted(excl)}")
        add(f"{gid}.exclusion_reason", excl["reason"] == "NOT_YET_AVAILABLE")
        rev1_available = next(r["available_time"] for r in inp["records"]
                              if r["revision"] == 1)
        add(f"{gid}.exclusion_available_time",
            excl["available_time"] == rev1_available, excl["available_time"])
        if gid == "P14E-G-007":
            add("g007.b1_trace_empty", bundle1["candidate_trace"] == [])
            add("g007.b2_revision",
                bundle2["evidence"][0]["revision"]
                == exp["bundle2"]["selected_revision"])
        else:
            add("g004.trace_empty", bundle1["candidate_trace"] == [])
            add("g004.knowing_not_leaking",
                exp["knowing_existence_is_not_leaking_content"] is True)

    elif gid == "P14E-G-005":
        b1, _, _ = build_bundle(inp["records"], q)
        b2, _, _ = build_bundle(inp["records"],
                                {**q, "as_of": inp["second_query_as_of"]})
        add("g005.b1_revision",
            b1["evidence"][0]["revision"] == exp["bundle1_selected_revision"])
        add("g005.b2_revision",
            b2["evidence"][0]["revision"] == exp["bundle2_selected_revision"])
        ids1 = {e["evidence_id"] for e in b1["evidence"]}
        ids2 = {e["evidence_id"] for e in b2["evidence"]}
        add("g005.disjoint", not (ids1 & ids2))
        add("g005.bundle_ids_differ", b1["bundle_id"] != b2["bundle_id"])
        from astock_v2.information.research_query import run_query as rq
        r2 = rq([project(r) for r in build_records(inp["records"])],
                ResearchQuery(**{**q, "as_of": inp["second_query_as_of"]}))
        add("g005.result_id_linked", b2["result_id"] == r2["result_id"])

    elif gid == "P14E-G-006":
        bundle, _, _ = build_bundle(inp["records"], q)
        ev = bundle["evidence"][0]
        add("g006.selected_revision",
            ev["revision"] == exp["selected_revision"], ev["revision"])
        add("g006.selection_reason",
            ev["selection_reason"] == exp["selection_reason"],
            ev["selection_reason"])
        got = [(t["revision"], t.get("available_time"),
                t.get("ingested_at"), t["rejection_reason"])
               for t in bundle["candidate_trace"]]
        want = [(t["revision"], t.get("available_time"),
                 t.get("ingested_at"), t["reason"])
                for t in exp["trace"]]
        add("g006.trace", got == want, f"{got}")

    elif gid == "P14E-G-008":
        bundle, _, _ = build_bundle(inp["records"], q)
        add("g008.valid_fields",
            set(bundle["evidence"][0]) == set(EVIDENCE_FIELDS) | {"evidence_id",
                                                                  "selection_reason"})
        for defect in inp["defective_records"]:
            record = dict(defect["record"])
            record["raw_payload"] = record.get("raw_payload", {"v": 1.0})
            base = RawIngestRecord(**record)
            metadata = {"adapter_version": base.adapter_version,
                        "raw_payload_hash": base.raw_payload_hash,
                        "ingestion_id": base.ingestion_id}
            removed = defect["remove_metadata"]
            metadata.pop(removed)
            info = RawInformationRecord(
                source=record["source"], source_id=record["source_id"],
                source_category=record["source_category"],
                entity_id=record["entity_id"], entity_type=record["entity_type"],
                event_time=record["event_time"],
                available_time=record["available_time"],
                revision=record["revision"], ingested_at=record["ingested_at"],
                value=1.0, metadata=metadata)
            try:
                ev = {"source": info.source, "source_id": info.source_id,
                      "revision": info.revision,
                      "event_time": info.event_time,
                      "available_time": info.available_time,
                      "adapter_version": info.metadata.get("adapter_version"),
                      "raw_payload_hash": info.metadata.get("raw_payload_hash"),
                      "ingestion_id": info.metadata.get("ingestion_id"),
                      "entity_id": info.entity_id,
                      "information_type": info.entity_type,
                      "ingested_at": info.ingested_at}
                check_provenance_complete(ev)
                add(f"g008.{removed}", False, "no raise")
            except ValueError as exc:
                add(f"g008.{removed}", removed in str(exc), str(exc)[:80])
        add("g008.no_silent_default", exp["no_silent_default"])

    elif gid == "P14E-G-009":
        records = inp["records"]
        orders = [records, list(reversed(records)),
                  records[2:] + records[:2]]
        bundles = [build_bundle(order, q)[0] for order in orders]
        ids = {b["bundle_id"] for b in bundles}
        add("g009.bundle_ids_equal", len(ids) == 1, f"{ids}")
        texts = {canonical_json(b) for b in bundles}
        add("g009.byte_identical", len(texts) == 1)
        add("g009.no_runtime_fields",
            not any(tok in bundles[0]["bundle_id"] or
                    tok in canonical_json(bundles[0])
                    for tok in exp["no_runtime_fields"]))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence_bundles.jsonl"
            first = persist_bundle(path, bundles[0])
            second = persist_bundle(path, bundles[0])
            add("g009.duplicate_append_rejected",
                first is True and second is False)
            reloaded = reload_verify(path)
            add("g009.reload_bundle_id_equal",
                len(reloaded) == 1
                and reloaded[0]["bundle_id"] == bundles[0]["bundle_id"])
        from astock_v2.information.research_query import run_query as rq
        info = [project(r) for r in build_records(records)]
        r1 = rq(info, ResearchQuery(**q))
        r2 = rq(list(reversed(info)), ResearchQuery(**q))
        add("g009.result_id_stable", r1["result_id"] == r2["result_id"])

    elif gid == "P14E-G-010":
        bundle, _, _ = build_bundle(inp["records"], q)
        add("g010.evidence_count",
            bundle["counts"]["evidence"] == exp["evidence_count"],
            f"{bundle['counts']}")
        ids = [e["evidence_id"] for e in bundle["evidence"]]
        add("g010.unique_evidence_ids", len(ids) == len(set(ids)))
        keys = [(t["source"], t["source_id"], t["revision"],
                 t["available_time"], t["raw_payload_hash"])
                for t in bundle["candidate_trace"]]
        add("g010.trace_unique", len(keys) == len(set(keys)))

    elif gid == "P14E-G-011":
        records = build_records(inp["records"])
        with tempfile.TemporaryDirectory() as tmp:
            _, outcomes = ingest_into_store(records, Path(tmp))
            add("g011.put_outcomes", outcomes == exp["put_outcomes"],
                f"{outcomes}")
        raised = False
        detail = ""
        try:
            build_bundle(inp["records"], q)
        except ValueError as exc:
            raised = True
            detail = str(exc)
        add("g011.bundle_raises", raised and exp["bundle_raises"], detail)
        add("g011.error_mentions_lineage", "q-mut" in detail, detail[:80])
        add("g011.p14b_authority", exp["p14b_authority_not_reimplemented"])

    elif gid == "P14E-G-012":
        raised, detail = False, ""
        try:
            ResearchQuery(**q)
        except ValueError as exc:
            raised = True
            detail = str(exc)
        add("g012.raises", raised and exp["raises"])
        add("g012.match", exp["match"] in detail, detail[:60])
        add("g012.synthetic_only", exp["synthetic_date_only"])

    return out


# ------------------------------------------------------------- global gates

def load_fixtures() -> list[dict]:
    paths = sorted(FIXTURE_DIR.glob("G-*.json"))
    fixtures = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    ids = [f["golden_id"] for f in fixtures]
    assert ids == [f"P14E-G-{i:03d}" for i in range(1, 13)], ids
    return fixtures


def check_closure() -> list[tuple[str, bool, str]]:
    """17 contract defs <-> 17 matrix rows <-> 12 goldens covering 17/17."""
    contract_ids = sorted(set(re.findall(r"^### P14E-\d{3}|^- \*\*(P14E-\d{3})\*\*",
                                         CONTRACT_MD.read_text(encoding="utf-8"), re.M)))
    contract_text = CONTRACT_MD.read_text(encoding="utf-8")
    contract_ids = sorted({mm.group(1) for mm in
                           (re.match(r"- \*\*(P14E-\d{3})\*\*", l)
                            for l in contract_text.splitlines()) if mm})
    matrix_text = MATRIX_MD.read_text(encoding="utf-8")
    matrix_ids = sorted({mm.group(1) for line in matrix_text.splitlines()
                         if (mm := re.match(r"^\|\s*(P14E-M-\d{3})\s*\|", line))})
    row_contract_ids = sorted({mm.group(1) for line in matrix_text.splitlines()
                               if (mm := re.match(r"^\|\s*P14E-M-\d{3}\s*\|\s*(P14E-\d{3})\s*\|", line))})
    expected = [f"P14E-{i:03d}" for i in range(1, 18)]
    fixtures = load_fixtures()
    fixture_ids = [f["golden_id"].replace("P14E-", "") for f in fixtures]
    golden_ids = [f"G-{i:03d}" for i in range(1, 13)]
    design_goldens = sorted(set(re.findall(r"^## (G-\d{3}) ",
                                           GOLDEN_DESIGN_MD.read_text(encoding="utf-8"), re.M)))
    covered = set()
    for block in re.split(r"^## G-\d{3} ", GOLDEN_DESIGN_MD.read_text(encoding="utf-8"), flags=re.M)[1:]:
        covered |= set(re.findall(r"P14E-\d{3}", block.split("Contract Coverage 断言")[0]))
    covered |= set(re.findall(r"P14E-\d{3}",
                              re.search(r"## 机械源码扫描.*", GOLDEN_DESIGN_MD.read_text(encoding="utf-8"), re.S).group(0)))
    return [
        ("closure.contract_ids_17", contract_ids == expected, f"{len(contract_ids)}"),
        ("closure.matrix_ids_17", matrix_ids == [f"P14E-M-{i:03d}" for i in range(1, 18)], f"{len(matrix_ids)}"),
        ("closure.matrix_covers_contract", row_contract_ids == expected, ""),
        ("closure.golden_files_12", fixture_ids == golden_ids, f"{fixture_ids[:3]}..."),
        ("closure.design_goldens_12", design_goldens == golden_ids, ""),
        ("closure.golden_coverage_17", covered == set(expected), f"{len(covered)}"),
    ]


def check_virgin_scan() -> list[tuple[str, bool, str]]:
    out = []
    for path in sorted(FIXTURE_DIR.glob("G-*.json")):
        text = path.read_text(encoding="utf-8")
        bad = [d for d in ISO_DATE.findall(text)
               if VIRGIN_START <= d < SYNTHETIC_FUTURE_CUTOFF]
        out.append((f"virgin.{path.name}", not bad, f"{bad}"))
    return out


def check_source_scan() -> list[tuple[str, bool, str]]:
    """P14E-016: no P14-E production runtime exists; banned tokens absent.
    The control-field DECLARATION in expected_contract.py (the tuple of
    fields it rejects) is exempted — naming a banned field in order to
    reject it is the sanctioned pattern."""
    out = []
    actual = sorted(p.name for p in SRC_INFO_DIR.glob("*.py"))
    out.append(("scan.info_files_pinned", actual == PINNED_INFO_FILES,
                f"unexpected: {sorted(set(actual) - set(PINNED_INFO_FILES))}"))
    for path in SRC_INFO_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        # docstrings and the CONTROL_FIELDS declaration name banned fields
        # in order to reject them — sanctioned prohibition contexts
        text = re.sub(r'^"""(?:.|"|"(?!"))*?"""', "", text, flags=re.S | re.M)
        text = re.sub(r"CONTROL_FIELDS\s*=\s*\([^)]*\)", "()", text,
                      flags=re.S)
        hits = [t for t in BANNED_SRC_TOKENS if t in text]
        out.append((f"scan.tokens.{path.name}", not hits, f"{hits}"))
    return out


def check_anticheat_layer() -> list[tuple[str, bool, str]]:
    out = []
    # usage patterns only — bare mentions in the banned-list declarations
    # of the anti-cheat tests themselves are sanctioned prohibitions
    banned_usage = ["pytest.skip(", "@pytest.mark.xfail",
                    "pytest.importorskip(",
                    "expected = run_query", "expected = build_bundle"]
    for path in sorted(P14E_LAYER_DIR.glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        # strip string literals: a banned usage pattern inside quotes is a
        # sanctioned prohibition declaration, not a call
        text = re.sub(r'"[^"]*"|' + chr(39) + '[^' + chr(39) + ']*' + chr(39), '""', text)
        hits = [t for t in banned_usage if t in text]
        out.append((f"anticheat.{path.name}", not hits, f"{hits}"))
    return out


def canonical_report() -> str:
    fixtures = load_fixtures()
    validation = []
    for f in fixtures:
        results = check_fixture(f)
        validation.append({
            "golden_id": f["golden_id"],
            "checks": [{"check": n, "ok": ok} for n, ok, _ in results],
            "passed": all(ok for _, ok, _ in results),
        })
    validation.sort(key=lambda v: v["golden_id"])
    report = {
        "phase": "P14-E",
        "schema": "p14e-harness-report-1",
        "contract_ids": 17,
        "matrix_ids": 17,
        "golden_ids": len(fixtures),
        "validation": validation,
    }
    return json.dumps(report, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def run_all_checks() -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    out += check_closure()
    out += check_virgin_scan()
    out += check_source_scan()
    out += check_anticheat_layer()
    for f in load_fixtures():
        for name, ok, detail in check_fixture(f):
            out.append((f"{f['golden_id']}.{name}", ok, detail))
    return out
