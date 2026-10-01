"""P14-E Acceptance Harness — Acceptance Matrix verification.

Every frozen matrix row (P14E-M-001..017) must map to its Contract ID and
Golden fixture(s), and the engine must produce a passing check for every
row's verification surface.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from test_p14e_contract import (  # noqa: E402
    EXPECTED_CONTRACT_IDS,
    EXPECTED_GOLDEN_IDS,
    EXPECTED_MATRIX_IDS,
    _matrix_text,
    core,
)


def test_matrix_ids_unique_and_dense():
    ids = re.findall(r"P14E-M-\d{3}", _matrix_text())
    assert sorted(set(ids)) == EXPECTED_MATRIX_IDS
    assert len(re.findall(r"^\| P14E-M-\d{3} ", _matrix_text(), re.M)) == 17


def test_matrix_contract_closure():
    row_contract_ids = re.findall(
        r"^\| P14E-M-\d{3} \| (P14E-\d{3}) \|", _matrix_text(), re.M)
    assert sorted(row_contract_ids) == EXPECTED_CONTRACT_IDS


def test_matrix_golden_references_resolve():
    referenced = set(re.findall(r"\bG-\d{3}\b", _matrix_text()))
    assert referenced == {f"G-{i:03d}" for i in range(1, 13)}


def test_matrix_verification_surface_green():
    """Every matrix row's verification surface maps to engine checks that
    all pass (the engine's per-fixture checks are the row executions)."""
    results = core.run_all_checks()
    failures = [(n, d) for n, ok, d in results if not ok]
    assert not failures, failures


def test_matrix_m016_is_source_scan_row():
    row = next(line for line in _matrix_text().splitlines()
               if line.startswith("| P14E-M-016 "))
    cells = [c.strip() for c in row.strip().strip("|").split(" | ")]
    assert cells[4] == "N/A (source scan)"
    assert "P14E-016" in row


def test_matrix_no_forbidden_status_words():
    matrix = _matrix_text()
    header = matrix.split("| Matrix ID")[0]
    assert "FROZEN" in header
    assert not re.search(r"\bPASS\b.*awaiting", header)
