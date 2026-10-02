"""P14-E Acceptance Harness — contract document closure checks.

Validates the frozen P14-E Design Contract / Acceptance Matrix /
Golden Design and the golden fixture set: IDs unique and dense, closure
17/17 at every layer, boundary and authority tokens present, statuses
correct (contract DRAFT-header preserved by its acceptance record,
matrix FROZEN, golden design DESIGN ONLY).
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
FIXTURE_DIR = HERE / "fixtures"

_spec = importlib.util.spec_from_file_location(
    "p14e_golden_core", HERE / "golden" / "core.py")
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)

EXPECTED_CONTRACT_IDS = [f"P14E-{i:03d}" for i in range(1, 18)]
EXPECTED_MATRIX_IDS = [f"P14E-M-{i:03d}" for i in range(1, 18)]
EXPECTED_GOLDEN_IDS = [f"P14E-G-{i:03d}" for i in range(1, 13)]


def _contract_text() -> str:
    return core.CONTRACT_MD.read_text(encoding="utf-8")


def _matrix_text() -> str:
    return core.MATRIX_MD.read_text(encoding="utf-8")


def _design_text() -> str:
    return core.GOLDEN_DESIGN_MD.read_text(encoding="utf-8")


def test_contract_ids_unique_and_dense():
    defs = sorted({m.group(1) for line in _contract_text().splitlines()
                   if (m := re.match(r"^- \*\*(P14E-\d{3})\*\*", line))})
    assert defs == EXPECTED_CONTRACT_IDS
    all_ids = re.findall(r"P14E-\d{3}", _contract_text())
    assert set(all_ids) == set(EXPECTED_CONTRACT_IDS)


def test_contract_statuses_consistent():
    contract = _contract_text()
    matrix = _matrix_text()
    design = _design_text()
    assert "STATUS: DRAFT" in contract          # preserved by acceptance record
    assert "v1.1: REPAIR-001" in contract
    assert "STATUS: FROZEN" in matrix
    assert "STATUS: DESIGN COMPLETE / HARNESS IMPLEMENTED / AWAITING INDEPENDENT ACCEPTANCE" in design
    # no self-acceptance anywhere
    for name, text in (("contract", contract), ("matrix", matrix),
                       ("design", design)):
        header = text.split("\n\n", 1)[0]
        assert not re.search(r"(Decision|Result|Status)\s*[:：]\s*PASS", header), name


def test_matrix_rows_unique_and_closed():
    rows = re.findall(r"^\| (P14E-M-\d{3}) \| (P14E-\d{3}) \|",
                      _matrix_text(), re.M)
    ids = [r[0] for r in rows]
    assert sorted(ids) == EXPECTED_MATRIX_IDS
    assert sorted(r[1] for r in rows) == EXPECTED_CONTRACT_IDS
    for _, cid in rows:
        assert cid in _contract_text()   # contract defines the ID


def test_matrix_columns_complete():
    for line in _matrix_text().splitlines():
        if re.match(r"^\| P14E-M-", line):
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            assert len(cells) == 7, cells[0]     # ID + Contract + 5 content
            assert all(cells), cells[0]


def test_golden_design_sections_complete():
    design = _design_text()
    gids = re.findall(r"^## (G-\d{3}) ", design, re.M)
    assert gids == [f"G-{i:03d}" for i in range(1, 13)]
    for block in re.split(r"^## G-\d{3} ", design, flags=re.M)[1:]:
        for section in ("Input", "Expected Evidence", "Expected Bundle",
                        "Expected Failure", "Contract Coverage"):
            assert section in block


def test_golden_fixtures_match_design():
    fixtures = [f for f in core.load_fixtures() if f["golden_id"].startswith("P14E-G-")]
    design = _design_text()
    for fx in fixtures:
        short_id = fx["golden_id"].replace("P14E-", "")   # design uses G-00X
        assert short_id in design
        block = re.split(r"^## " + short_id + " ",
                         design, flags=re.M)[1].split("\n## ")[0]
        for cid in fx["contract_ids"]:
            assert cid in block, (fx["golden_id"], cid)


def test_boundary_and_authority_tokens():
    text = _contract_text() + _matrix_text() + _design_text()
    for token in ("2026-09-22", "2026-09-23", "assert_research_zone",
                  "STOPPED", "PROTECTED", "P14-A", "P14-B", "P14-C", "P14-D",
                  "visible_revisions", "raw_payload_hash", "ingestion_id",
                  "NOT_YET_AVAILABLE", "OUTSIDE_AS_OF",
                  "UNRESOLVED_AVAILABILITY"):
        assert token in text, token


def test_no_real_virgin_dates_in_fixtures():
    for path in sorted(FIXTURE_DIR.glob("G-*.json")):
        for date in re.findall(r"\b\d{4}-\d{2}-\d{2}\b",
                               path.read_text(encoding="utf-8")):
            if date >= "2026-09-23":
                assert date >= "2028-01-01", (path.name, date)
