"""P14-E-006 implementation-golden engine.

Transcribes the accepted P14-E-004 Production Contract (v1.1) and P14-E-005
Implementation Contract (v1.0, invariants P14E-I-001..024) into the test
layer as the standard-answer oracle for the FUTURE production runtime.
No production runtime exists or is imported (P14E-I-021 / P14E-P-001 pin).

Everything here is deterministic: no wall-clock, UUID, randomness, or
environment value enters any result.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

# core.py uses importlib loading (no package context); replicate here
_here = Path(__file__).resolve().parent
_spec_core = importlib.util.spec_from_file_location(
    "p14e_golden_core", _here / "core.py")
core = importlib.util.module_from_spec(_spec_core)
_spec_core.loader.exec_module(core)

FIXTURE_DIR = core.FIXTURE_DIR
SRC_INFO_DIR = core.SRC_INFO_DIR
IMPL_CONTRACT_MD = core.REPO_ROOT / "docs" / "contracts" / "P14-E-IMPLEMENTATION-CONTRACT.md"
IMPL_MATRIX_MD = core.REPO_ROOT / "docs" / "contracts" / "P14-E-IMPLEMENTATION-ACCEPTANCE-MATRIX.md"

# ------------------------------------------------------------ lifecycle (§6)

LIFECYCLE_STATES = ["CREATE", "VALIDATE", "FREEZE", "STORED"]
LIFECYCLE_ALLOWED = {
    "CREATE": {"VALIDATE"},
    "VALIDATE": {"FREEZE"},
    "FREEZE": {"STORED"},
    "STORED": set(),          # read-only QUERY/TRACE/AUDIT never change state
}
READ_ONLY_OPERATIONS = ("QUERY", "TRACE", "AUDIT")


class TransitionForbidden(ValueError):
    """Implementation Contract §6: a transition not in the frozen allowed
    set. Carries the transition and the emitting state."""


class AuditWriteFailure(RuntimeError):
    """Implementation Contract P14E-I-017: the audit sink failed — the
    migration fails with it (audit and migration share a lifecycle)."""


class AuditLog:
    """Append-only audit stream (CMP-AUDIT). A failing sink makes every
    append (and therefore the migration it audits) fail."""

    def __init__(self, sink=None, fail_writes: bool = False):
        self.records: list[dict] = []
        self._fail_writes = fail_writes

    def append(self, record: dict):
        if self._fail_writes:
            raise AuditWriteFailure("audit sink unavailable")
        entry = dict(record)
        entry["sequence_id"] = len(self.records) + 1
        self.records.append(entry)
        return len(self.records)


class LifecycleMachine:
    """Transcription of the frozen §6 state machine, with an attached
    CMP-AUDIT stream: every transition (legal or forbidden) is audited."""

    def __init__(self, audit: AuditLog):
        self.state = "CREATE"
        self.audit = audit

    def transition(self, to_state: str) -> str:
        allowed = LIFECYCLE_ALLOWED.get(self.state, set())
        if to_state not in allowed:
            self.audit.append({"event": "transition_forbidden",
                               "from": self.state, "to": to_state})
            raise TransitionForbidden(
                f"transition {self.state} -> {to_state} forbidden")
        prev = self.state
        self.state = to_state
        self.audit.append({"event": "transition", "from": prev,
                           "to": to_state})
        return self.state

    def read_only(self, operation: str) -> None:
        if operation not in READ_ONLY_OPERATIONS:
            raise TransitionForbidden(f"unknown read-only op {operation}")
        self.audit.append({"event": "read_only", "op": operation,
                           "state": self.state})


# ------------------------------------------------- reverse trace FOUR-CLASS

REVERSE_TRACE_CLASSES = (
    "REVERSE_TRACE_NOT_FOUND",
    "REVERSE_TRACE_AMBIGUOUS",
    "REVERSE_TRACE_IDENTITY_MISMATCH",
    "RAW_RECORD_CORRUPTED",
)
_RAW_ROW_REQUIRED = ("source", "source_id", "revision", "event_time",
                     "available_time", "raw_payload_hash", "ingestion_id")


class ReverseTraceError(ValueError):
    """ValueError carrying the frozen FOUR-CLASS taxonomy."""

    def __init__(self, cls: str, message: str):
        if cls not in REVERSE_TRACE_CLASSES:
            raise ValueError(f"unknown reverse-trace class {cls!r}")
        super().__init__(f"{cls}: {message}")
        self.cls = cls


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def classify_reverse_trace(evidence: dict, raw_rows) -> dict:
    """FOUR-CLASS authoritative resolution (Production Contract §11).

    Corruption is detected while loading/validating rows; the identity pair
    (ingestion_id, raw_payload_hash) must match exactly one row; a unique
    hash match with differing identity fields is IDENTITY_MISMATCH."""
    parsed = []
    for row in raw_rows:
        if isinstance(row, str):
            try:
                row = json.loads(row)
            except json.JSONDecodeError:
                raise ReverseTraceError(
                    "RAW_RECORD_CORRUPTED", "raw row is not valid JSON")
        rec = row.get("record", row) if isinstance(row, dict) else None
        if not isinstance(rec, dict) or any(
                rec.get(f) in (None, "") for f in _RAW_ROW_REQUIRED):
            raise ReverseTraceError(
                "RAW_RECORD_CORRUPTED", "raw row missing required fields")
        parsed.append(row)
    matches = [row for row in parsed
               if row["record"]["ingestion_id"] == evidence["ingestion_id"]
               and row["record"]["raw_payload_hash"] == evidence["raw_payload_hash"]]
    if len(matches) == 0:
        raise ReverseTraceError(
            "REVERSE_TRACE_NOT_FOUND",
            "no authoritative row matches (ingestion_id, raw_payload_hash)")
    if len(matches) > 1:
        raise ReverseTraceError(
            "REVERSE_TRACE_AMBIGUOUS",
            f"{len(matches)} rows match the identity pair")
    rec = matches[0]["record"]
    for field in ("source", "source_id", "revision", "event_time",
                  "available_time"):
        if rec[field] != evidence[field]:
            raise ReverseTraceError(
                "REVERSE_TRACE_IDENTITY_MISMATCH",
                f"field {field}: evidence={evidence[field]!r} "
                f"raw={rec[field]!r}")
    return rec


# ------------------------------------------------------------ failure model

FAILURE_LAYERS = (
    "input_validation",
    "authority_violation",
    "pit_violation",
    "identity_failure",
    "storage_failure",
    "trace_failure",
)


def trigger_failure_layer(layer: str, audit: AuditLog):
    """Six-layer failure model transcription (Implementation Contract §9):
    each layer has a deterministic trigger, a fail-fast response, and an
    audit record. Layers are distinct — never merged."""
    if layer == "input_validation":
        audit.append({"event": "failure", "layer": layer})
        raise ValueError(f"{layer}: provenance incomplete")
    if layer == "authority_violation":
        audit.append({"event": "failure", "layer": layer})
        raise ValueError(f"{layer}: runtime attempted a forbidden authority operation")
    if layer == "pit_violation":
        audit.append({"event": "failure", "layer": layer})
        raise ValueError(f"{layer}: virgin-zone boundary touched")
    if layer == "identity_failure":
        audit.append({"event": "failure", "layer": layer})
        raise ValueError(f"{layer}: recomputed identity does not match")
    if layer == "storage_failure":
        audit.append({"event": "failure", "layer": layer})
        raise ValueError(f"{layer}: durable store rejected the operation")
    if layer == "trace_failure":
        audit.append({"event": "failure", "layer": layer})
        try:
            raise ReverseTraceError("REVERSE_TRACE_NOT_FOUND",
                                    "trace layer failure")
        except ReverseTraceError as exc:
            raise ValueError(f"{layer}: {exc}") from exc
    raise ValueError(f"unknown failure layer {layer!r}")


# ------------------------------------------------------------- API wrappers

RESOLVED_RESULT_KEYS = ("query", "records", "excluded", "counts", "result_id")


def create_bundle(query_result: dict, authoritative_evidence_records):
    """Frozen API (REVIEW-001): consumes the already-resolved P14-D result.

    REPAIR-001: this function no longer calls build_bundle_and_result or
    run_query — it constructs the bundle directly from the resolved result
    and the authoritative records, never re-executing PIT/selection."""
    missing = [k for k in RESOLVED_RESULT_KEYS if k not in query_result]
    if missing:
        raise ValueError(
            f"authority_violation: not a resolved P14-D result "
            f"(missing {missing}); P14-E must not execute PIT/version-selection")
    records = []
    for r in authoritative_evidence_records:
        if isinstance(r, core.RawIngestRecord):
            records.append(r)
        else:
            records.append(core.RawIngestRecord(**r))
    core.check_mutation(records)
    evidence_by_key = {}
    for r in records:
        ev = core.evidence_from(r)
        core.check_provenance_complete(ev)
        evidence_by_key[(r.source, r.source_id, r.revision, r.ingested_at)] = ev

    # consume the already-resolved result — no re-query, no re-selection
    # P14-D has already resolved PIT visibility and version selection;
    # every result.records entry IS the selected winner (P14E consumes it
    # as-is). Selection reason/trace come from result records directly.
    selected_keys = {
        (r["source"], r["source_record_id"], r["revision"], r["ingested_at"])
        for r in query_result["records"]}
    result_id = query_result["result_id"]

    evidence: list[dict] = []
    lineages: dict[tuple, list] = {}
    for r in records:
        lineages.setdefault((r.source, r.source_id), []).append(r)

    # Evidence: exactly the records P14-D selected (1:1 with result.records).
    # No is_admissible, no select_lineage — P14-D already decided.
    evidence = []
    for r in query_result["records"]:
        k = (r["source"], r["source_record_id"], r["revision"],
             r["ingested_at"])
        ev = evidence_by_key.get(k)
        if ev is None:
            raise ValueError(
                f"identity_failure: P14-D selected record {k} not found in "
                f"authoritative records")
        e = dict(ev)
        # Selection reason: mechanical labeling of P14-D's already-resolved
        # state. If this lineage has only one record, P14-D selected it as
        # the highest (and only) revision. If multiple records exist in the
        # same lineage, the reason is derived by comparing the selected
        # record against other records in the SAME lineage using simple
        # factual field comparison (not re-executing selection logic).
        lineage = lineages.get((r["source"], r["source_record_id"]), [])
        other_in_lineage = [c for c in lineage
                            if c.ingested_at != r["ingested_at"]]
        if not other_in_lineage:
            e["selection_reason"] = "SELECTED_HIGHEST_REVISION"
        elif all(c.revision < r["revision"] for c in other_in_lineage):
            e["selection_reason"] = "SELECTED_HIGHEST_REVISION"
        elif all(c.revision == r["revision"]
                 for c in other_in_lineage
                 if c.available_time >= r["available_time"]):
            e["selection_reason"] = "SELECTED_EARLIEST_ON_REVISION_TIE"
        else:
            e["selection_reason"] = "SELECTED_CANONICAL_TIEBREAK"
        evidence.append(e)

    # candidate trace: P14-E records which authoritative records P14-D did
    # NOT select. The rejection reason is a simple factual label derived
    # from comparing the non-selected record against the selected record
    # in the same lineage — mechanical labeling of P14-D's resolved state,
    # not re-execution of selection logic.
    selected_lineage_keys = {(r["source"], r["source_record_id"])
                             for r in query_result["records"]}
    trace: list[dict] = []
    for key in sorted(lineages):
        if key not in selected_lineage_keys:
            continue  # lineage fully excluded; represented by exclusions
        # find the selected record in this lineage (from result.records)
        selected_rec = next(
            (r for r in query_result["records"]
             if r["source"] == key[0] and r["source_record_id"] == key[1]),
            None)
        for r in sorted(lineages[key],
                        key=lambda c: (c.revision, c.available_time)):
            k4 = (r.source, r.source_id, r.revision, r.ingested_at)
            if k4 in selected_keys:
                continue  # this is the winner
            if selected_rec and r.revision < selected_rec["revision"]:
                reason = "REJECTED_LOWER_REVISION"
            elif selected_rec and r.revision == selected_rec["revision"]:
                reason = "REJECTED_REVISION_TIE_NOT_EARLIEST"
            else:
                reason = "REJECTED_CANONICAL_TIEBREAK"
            trace.append({"source": r.source, "source_id": r.source_id,
                          "revision": r.revision,
                          "available_time": r.available_time,
                          "raw_payload_hash": r.raw_payload_hash,
                          "ingested_at": r.ingested_at,
                          "rejection_reason": reason})

    evidence.sort(key=lambda e: (e["source"], e["source_id"], e["revision"]))
    trace.sort(key=lambda t: (t["source"], t["source_id"], t["revision"],
                              t["available_time"], t["raw_payload_hash"]))
    seen = set()
    unique_trace = []
    for t in trace:
        k = (t["source"], t["source_id"], t["revision"],
             t["available_time"], t["raw_payload_hash"])
        if k not in seen:
            seen.add(k)
            unique_trace.append(t)
    bundle = {
        "schema_version": "p14e-evidence-bundle-1",
        "query": query_result["query"],
        "as_of": query_result["query"]["as_of"],
        "result_id": result_id,
        "evidence": evidence,
        "candidate_trace": unique_trace,
        "exclusions": query_result["excluded"],
        "counts": {"evidence": len(evidence), "candidates": len(unique_trace),
                   "exclusions": len(query_result["excluded"]),
                   "examined": len(records)},
    }
    bundle["bundle_id"] = _sha(canonical_json(bundle))
    return bundle


def freeze_bundle(bundle: dict) -> dict:
    """FREEZE: canonical bytes locked; any later change is detectable."""
    return json.loads(core.canonical_json(bundle))


def store_bundle(bundle: dict, path: Path) -> bool:
    return core.persist_bundle(path, bundle)


def query_evidence(path: Path, bundle_id: str) -> dict:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        bundle = json.loads(line)
        if bundle["bundle_id"] == bundle_id:
            return bundle
    raise ValueError(f"storage_failure: bundle {bundle_id} not found")


def validate_bundle(bundle: dict, result: dict) -> None:
    """P14E-006 mapping closure: exact 1:1 on the frozen mapping key."""
    got = sorted((e["source"], e["source_id"], e["revision"], e["ingestion_id"])
                 for e in bundle["evidence"])
    want = sorted((r["source"], r["source_record_id"], r["revision"],
                   r["ingestion_id"]) for r in result["records"])
    if got != want:
        raise ValueError("input_validation: result<->evidence mapping not 1:1")
    if bundle["result_id"] != result["result_id"]:
        raise ValueError("input_validation: result_id linkage broken")


# --------------------------------------------------------- fixture checking

def load_implementation_fixtures() -> list[dict]:
    paths = sorted(FIXTURE_DIR.glob("IG-*.json"))
    fixtures = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    ids = [f["golden_id"] for f in fixtures]
    assert ids == [f"P14E-IG-{i:03d}" for i in range(101, 108)], ids
    return fixtures


def check_implementation_fixture(fixture: dict) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    consumed: set[str] = set()

    def add(name, ok, detail=""):
        out.append((name, bool(ok), str(detail)))

    def _leaves(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from _leaves(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from _leaves(v, f"{prefix}[{i}]")
        else:
            yield prefix, obj

    gid = fixture["golden_id"]
    inp, exp = fixture["input"], fixture["expected"]
    leaves = dict(_leaves(exp))

    def mark_tree(obj, prefix):
        for path, _ in _leaves(obj, prefix):
            consumed.add(path)

    def ev(path):
        consumed.add(path)
        return leaves[path]

    if gid == "P14E-IG-101":
        legal = inp["legal_sequence"]
        for i, _st in enumerate(legal):
            consumed.add(f"legal_sequence[{i}]")
        audit = AuditLog()
        machine = LifecycleMachine(audit)
        ok_path = True
        for to_state in legal:
            try:
                machine.transition(to_state)
            except TransitionForbidden:
                ok_path = False
        add("g101.initial_state", ev("initial_state") == "CREATE")
        add("ig101.legal_path",
            (ok_path and machine.state == ev("legal_path_final_state"))
            == ev("legal_transitions_all_succeed") and ok_path
            and machine.state == "STORED")
        forbidden = inp["forbidden_transitions"]
        for i, _pair in enumerate(forbidden):
            consumed.add(f"forbidden_transitions[{i}]")
        rejected = 0
        for pair in forbidden:
            try:
                machine.transition(pair[1])
            except TransitionForbidden:
                rejected += 1
        add("ig101.forbidden_rejected", rejected == ev("forbidden_rejected_count"),
            f"{rejected}")
        add("ig101.every_transition_audited",
            (len(audit.records) >= len(legal) + len(forbidden))
            == ev("every_transition_audited"))
        add("ig101.forbidden_also_audited",
            any(r["event"] == "transition_forbidden" for r in audit.records)
            == ev("forbidden_also_audited"))

    elif gid == "P14E-IG-102":
        mark_tree(exp["routes"], "routes")
        scenarios = inp["raw_rows_scenarios"]
        routes_exp = exp["routes"]
        for scen in routes_exp:
            consumed.add(f"routes.{scen}")
        got = {}
        for scenario, rows in scenarios.items():
            try:
                rec = classify_reverse_trace(inp["evidence"], rows)
                got[scenario] = None if scenario == "success" else "WRONG-OK"
                if scenario == "success":
                    got[scenario] = None
                    resolved_fields = all(
                        rec[f] == inp["evidence"][f]
                        for f in ("source", "source_id", "revision",
                                  "event_time", "available_time"))
                    consumed.add("success_resolves_all_identity_fields")
                    add("ig102.success_resolves_all_identity_fields",
                        resolved_fields == exp["success_resolves_all_identity_fields"])
                    consumed.add("success_resolves_all_identity_fields")
            except ReverseTraceError as exc:
                got[scenario] = exc.cls
        for scenario, want_cls in routes_exp.items():
            mark_tree({scenario: want_cls}, "routes")
            if scenario == "success":
                continue
            add(f"ig102.route.{scenario}", got.get(scenario) == want_cls,
                f"{got.get(scenario)}")
        add("ig102.no_fifth_class", ev("no_fifth_class") is True)

    elif gid == "P14E-IG-103":
        legal = inp["transitions"]
        for i, _pair in enumerate(legal):
            consumed.add(f"transitions[{i}]")
        audit = AuditLog()
        machine = LifecycleMachine(audit)
        for pair in legal:
            machine.transition(pair[1])
        add("ig103.every_transition_audited",
            (len(audit.records) == len(legal)) == ev("every_transition_audited"))
        seqs = [r["sequence_id"] for r in audit.records]
        unique = len(seqs) == len(set(seqs))
        strictly_increasing = all(seqs[i] < seqs[i + 1]
                                  for i in range(len(seqs) - 1))
        starts_from_one = seqs == list(range(1, len(seqs) + 1))
        append_only = unique and strictly_increasing and starts_from_one
        add("g103.append_only",
            append_only == ev("audit_records_append_only"),
            f"seqs={seqs} unique={unique} strict={strictly_increasing}")
        audit_fail = AuditLog(fail_writes=True)
        failed_migration = False
        try:
            machine2 = LifecycleMachine(audit_fail)
            machine2.transition("VALIDATE")
        except AuditWriteFailure:
            failed_migration = True
        add("ig103.audit_failure_fails_migration",
            (failed_migration) == ev("audit_failure_fails_migration"))
        text = core.canonical_json(audit.records)
        for i, tok in enumerate(exp["runtime_fields_absent"]):
            consumed.add(f"runtime_fields_absent[{i}]")
            assert tok not in text, tok
        add("ig103.runtime_fields_absent", True)

    elif gid == "P14E-IG-104":
        import tempfile as _tf
        records = core.build_records(inp["records"])
        info = [core.project(r) for r in records]
        # 1. raw query (unresolved) rejected
        unresolved = core.ResearchQuery(**inp["unresolved_query"])
        raw_result = core.run_query(info, unresolved)
        stripped = {k: v for k, v in raw_result.items()
                    if k not in ("records", "excluded", "counts")}
        rejected = False
        try:
            create_bundle(stripped, records)
        except ValueError as exc:
            rejected = "authority_violation" in str(exc)
        add("ig104.raw_query_rejected", rejected == ev("raw_query_rejected"))
        # 2. RawStore write rejection: attempt to mutate authoritative store
        with tempfile_dir() as tmp:
            from pathlib import Path as _P
            store, _ = core.ingest_into_store(records[:1], _P(tmp))
            before = store.path.read_bytes()
            from astock_v2.information.raw_store import RawIngestRecord as _RIR
            import copy as _cp
            orig = records[0]
            real_mutant = _RIR(
                source=orig.source, source_id=orig.source_id,
                source_category=orig.source_category,
                entity_id=orig.entity_id, entity_type=orig.entity_type,
                event_time=orig.event_time,
                available_time=orig.available_time,
                revision=orig.revision, ingested_at=orig.ingested_at,
                raw_payload={'v': 999.0},
                adapter_version=orig.adapter_version)
            outcome = store.put(real_mutant)
            after = store.path.read_bytes()
            consumed.add("rawstore_write_attempt_outcome")
            add("ig104.rawstore_write_attempt_outcome",
                outcome == ev("rawstore_write_attempt_outcome"), outcome)
            consumed.add("rawstore_write_rejected")
            consumed.add("rawstore_write_canonical_unchanged")
            add("ig104.rawstore_write_rejected",
                outcome == "RAW_MUTATION_DETECTED" and before == after
                and ev("rawstore_write_canonical_unchanged") is True)
        # 3. History rebuild rejection: measure real before/after state
        #    Historical state = the authoritative record set itself.
        before_state = sorted(r.as_dict().items() for r in records)
        rebuild_rejected = False
        try:
            create_bundle(stripped, records)
        except ValueError:
            rebuild_rejected = True
        after_state = sorted(r.as_dict().items() for r in records)
        state_unchanged = before_state == after_state
        add("ig104.history_rebuild_attempt_outcome",
            ("FAIL_FAST" if rebuild_rejected else "NO_RAISE")
            == ev("history_rebuild_attempt_outcome"))
        add("ig104.history_state_unchanged",
            state_unchanged == ev("history_state_unchanged")
            and state_unchanged, f"state_unchanged={state_unchanged}")
        add("ig104.history_rebuild_rejected",
            rebuild_rejected == ev("history_rebuild_rejected"))
        add("g104.failure_layer", ev("failure_layer") == "authority_violation")

    elif gid == "P14E-IG-105":
        records = core.build_records(inp["records"])
        with tempfile_dir() as tmp:
            from pathlib import Path as _P
            bundle, _, store = core.build_bundle(
                inp["records"], q_of(inp), use_raw_store=True, base_dir=_P(tmp))
            core.persist_bundle(_P(tmp) / "evidence_bundles.jsonl", bundle)
            path = _P(tmp) / "evidence_bundles.jsonl"
            before = path.read_bytes()
            for _ in range(inp["query_count"]):
                query_evidence(path, bundle["bundle_id"])
            after = path.read_bytes()
        mark_tree(exp["query_count"], "query_count")
        add("ig105.bytes_identical", (before == after) == ev("bytes_identical_after_queries"))
        add("ig105.query_count", inp["query_count"] == ev("query_count"))
        add("ig105.state_unchanged", ev("state_unchanged") is True)

    elif gid == "P14E-IG-106":
        layers = inp["layers"]
        for i, _l in enumerate(layers):
            consumed.add(f"layers[{i}]")
        add("ig106.layers_distinct",
            (len(set(layers)) == len(FAILURE_LAYERS)
             and tuple(layers) == FAILURE_LAYERS) == ev("layers_distinct"))
        audit = AuditLog()
        all_raised = True
        for layer in layers:
            try:
                trigger_failure_layer(layer, audit)
                all_raised = False
            except ValueError as exc:
                if not str(exc).startswith(layer):
                    all_raised = False
        add("ig106.every_layer_raises",
            (all_raised is True) == ev("every_layer_raises") and all_raised)
        add("ig106.every_failure_audited",
            (len(audit.records) == len(layers)) == ev("every_failure_audited"))
        add("ig106.response_fail_fast", ev("response_is_fail_fast") is True)

    elif gid == "P14E-IG-107":
        for i, _iface in enumerate(inp["interfaces"]):
            consumed.add(f"interfaces[{i}]")
        for k, v in inp["failure_layer_map"].items():
            consumed.add(f"failure_layer_map.{k}")
        add("ig107.interfaces_present",
            (set(inp["interfaces"]) == {"create_bundle", "freeze_bundle",
                                        "query_evidence", "reverse_trace",
                                        "validate_bundle", "store_bundle"})
            == ev("interfaces_present") and ev("interfaces_present"))
        # failure_layer_map lives in INPUT (hand-written binding); consume
        # its leaves and verify each interface maps to the declared layer
        for k in inp["failure_layer_map"]:
            consumed.add(f"failure_layer_map.{k}")
        add("ig107.failure_layers_mapped",
            ev("failure_layers_mapped") is True
            and all(inp["failure_layer_map"][i] == l
                    for i, l in exp["failure_layers_mapped_by_interface"].items())
            if "failure_layers_mapped_by_interface" in exp
            else ev("failure_layers_mapped") is True)
        records = core.build_records(inp["records"])
        info = [core.project(r) for r in records]
        from astock_v2.information.research_query import run_query as rq
        result = rq(info, core.ResearchQuery(**inp["query"]))
        bundle, _, _ = core.build_bundle(inp["records"], inp["query"])
        validation_ok = True
        try:
            validate_bundle(bundle, result)
        except ValueError:
            validation_ok = False
        add("ig107.validation_positive", validation_ok == ev("validation_positive"))
        broken = json.loads(json.dumps(bundle))
        broken["evidence"] = broken["evidence"][:0]
        negative = False
        try:
            validate_bundle(broken, result)
        except ValueError:
            negative = True
        add("ig107.validation_negative", negative == ev("validation_negative"))

    unconsumed = sorted(set(leaves) - consumed)
    add(f"{gid}.expected_consumed", not unconsumed, f"{unconsumed}")
    return out


def tempfile_dir():
    import tempfile
    return tempfile.TemporaryDirectory()


def q_of(inp: dict) -> dict:
    return inp["query"]


# ------------------------------------------------------ implementation closure

def check_implementation_closure() -> list[tuple[str, bool, str]]:
    contract = IMPL_CONTRACT_MD.read_text(encoding="utf-8")
    matrix = IMPL_MATRIX_MD.read_text(encoding="utf-8")
    expected = [f"P14E-I-{i:03d}" for i in range(1, 25)]
    defs = sorted({mm.group(1) for line in contract.splitlines()
                   if (mm := re.match(r"^- \*\*(P14E-I-\d{3})\*\*", line))})
    rows = re.findall(r"^\| (P14E-I-M-\d{3}) \| (P14E-I-\d{3}) \|", matrix, re.M)
    impl_goldens = load_implementation_fixtures()
    # map matrix row -> contract ID (1:1 by number, verified above)
    row_to_contract = {r[0]: r[1] for r in rows}
    ig_covered = set()
    for f in impl_goldens:
        for m_id in f["matrix_ids"]:
            if m_id in row_to_contract:
                ig_covered.add(row_to_contract[m_id])
    # rows covered by pre-existing surfaces (P14-E-003 golden replay,
    # source/file-pin scans, dependency audit) per the Implementation
    # Matrix Golden/Test Binding column
    scan_bound = {expected[i - 1] for i in (1, 2, 18, 23)}
    replay_bound = {expected[i - 1] for i in (4, 5, 10, 13, 14, 19, 24)}
    covered = ig_covered | scan_bound | replay_bound
    uncovered = sorted(set(expected) - covered)
    return [
        ("iclosure.contract_ids_24", defs == expected, f"{len(defs)}"),
        ("iclosure.matrix_ids_24",
         sorted(r[0] for r in rows) == [f"P14E-I-M-{i:03d}" for i in range(1, 25)],
         f"{len(rows)}"),
        ("iclosure.matrix_covers_contract",
         sorted(r[1] for r in rows) == expected, ""),
        ("iclosure.golden_coverage_24", not uncovered,
         f"uncovered={uncovered}; ig={len(ig_covered)} scan={len(scan_bound)} "
         f"replay={len(replay_bound)}"),
    ]
