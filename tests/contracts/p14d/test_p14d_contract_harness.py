"""P14-D Acceptance Harness — document-level mechanical checks.

Validates the frozen P14-D contract documents, the golden fixture set,
and the production module's anti-cheat surface. Behavioral checks live in
test_p14d_harness.py; golden fixtures are exercised in test_p14d_golden.py.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "audit_p14d_contract.py"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
QUERY_MODULE = REPO_ROOT / "src" / "astock_v2" / "information" / "research_query.py"

_spec = importlib.util.spec_from_file_location("audit_p14d_contract", AUDIT_SCRIPT)
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

VIRGIN_START = "2026-09-23"
SYNTHETIC_FUTURE_CUTOFF = "2028-01-01"  # anything later is unmistakably synthetic


def _findings(result, code):
    return [f for f in result["findings"] if f["check"] == code]


def test_contract_audit_pass():
    result = audit.run_harness(audit.CONTRACT, audit.MATRIX)
    assert result["status"] == "PASS", result["findings"]
    assert result["hard_count"] == 0
    assert result["stats"]["contract_ids"] == 10
    assert result["stats"]["matrix_ids"] == 10
    assert result["stats"]["golden_ids"] == 11
    assert result["stats"]["harness_tests"] == 11


def test_contract_status_frozen_not_self_accepted():
    header = audit.CONTRACT.read_text(encoding="utf-8").splitlines()[:10]
    status = next(line for line in header if "状态" in line)
    assert "FROZEN" in status
    assert "PASS" not in status and "ACCEPTED" not in status


def test_golden_fixture_ids_dense():
    paths = sorted(FIXTURE_DIR.glob("G-*.json"))
    ids = [json.loads(p.read_text(encoding="utf-8"))["golden_id"] for p in paths]
    assert ids == [f"P14D-G-{i:03d}" for i in range(1, 12)]
    for path in paths:
        fx = json.loads(path.read_text(encoding="utf-8"))
        assert set(fx) >= {"golden_id", "title", "contract_ids", "input", "expected"}
        assert fx["contract_ids"], fx["golden_id"]


def test_no_real_virgin_zone_dates_in_fixtures():
    """P14D-009: fixture inputs may never consume the real virgin window.
    Anything at/after virgin_start must be unmistakably synthetic
    (>= 2028)."""
    for path in sorted(FIXTURE_DIR.glob("G-*.json")):
        text = path.read_text(encoding="utf-8")
        for date in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text):
            if VIRGIN_START <= date:
                assert date >= SYNTHETIC_FUTURE_CUTOFF, (path.name, date)


def test_production_module_has_no_control_switches():
    """Golden anti-cheat: the production query module contains no test-only
    switches, overrides, or behavior branches (line-based scan)."""
    import_line = re.compile(r"^\s*(#|from|import|[A-Z_]+ =)")
    banned = ["fixture_mode", "expected_result_override", "golden_override",
              "test_only", "skip_validation", "force_visible", "force_hidden",
              "running_under_test"]
    for line in QUERY_MODULE.read_text(encoding="utf-8").splitlines():
        if import_line.match(line) and "#" in line:
            continue  # comments may name the banned tokens as prohibitions
        for token in banned:
            assert token not in line, (token, line)


def test_production_module_is_infrastructure_only():
    """P14D-010: the query layer exposes retrieval only — no ranking,
    recommendation, or trading surface."""
    import sys
    sys.path.insert(0, str(REPO_ROOT / "src"))
    import astock_v2.information.research_query as rq
    public = [name for name in vars(rq) if not name.startswith("_")]
    forbidden = ("recommend", "predict", "rank", "trade", "portfolio",
                 "alpha", "score", "select_stock", "signal")
    for name in public:
        for token in forbidden:
            assert token not in name.lower(), name
    assert hasattr(rq, "run_query")
    assert hasattr(rq, "ResearchQuery")
