"""Meta-tests for the P14-C Contract Acceptance Harness.

Each test feeds the harness synthetic well-formed or mutated contract /
matrix documents and asserts the harness verdict. The final test is a
characterization snapshot of the REAL contract documents at harness
introduction time (2026-09-30): it asserts the specific findings the
harness reports today, so any future contract edit that changes the
finding set is forced through a conscious snapshot update rather than
silently passing.

These tests validate the HARNESS, not src/ or tests/ implementation code.
Per the P14-C repair mandate, harness findings on the real documents are
report-only: they must never be resolved by editing implementation code.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_p14c_contract.py"
REAL_CONTRACT = REPO_ROOT / "docs" / "contracts" / "P14-C-DESIGN-CONTRACT.md"
REAL_MATRIX = REPO_ROOT / "docs" / "contracts" / "P14-C-ACCEPTANCE-MATRIX.md"

_spec = importlib.util.spec_from_file_location("audit_p14c_contract", SCRIPT_PATH)
harness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(harness)

GOOD_CONTRACT = """\
# P14-C Design Contract (synthetic)

> 状态：DRAFT — awaiting independent contract review

## 1. Missingness Contract

- **P14C-MISS-001**: 六类互斥分类，任何 observation 只能属于一类。
- **P14C-MISS-002**: SOURCE_EMPTY 不能被重新解释为 EXPECTED_ABSENCE。

## 2. Expected Contract

### 2.1 Authority 来源

EXPECTED_CONTRACT 独立于 actual payload。
禁止在 EXPECTED_CONTRACT 中包含测试控制字段
（expected_empty / broken_source / force_source_error / fixture_mode）。

### 2.2 结构

```python
EXPECTED_CONTRACT = {
    source_id: {
        "expected_entities": [str, ...],
        "expected_dates": [str, ...],
    }
}
```

## 3. Revision Integrity Contract

- **P14C-REV-001**: revision gap 被检测并报告为 ANOMALY。

## 4. Nine Quality Dimensions（冻结）

| # | dimension_id | 名称 |
|---|-------------|------|
| 1 | completeness | 完整性 |
| 2 | validity | 有效性 |
| 3 | timeliness | 时效性 |
| 4 | freshness | 新鲜度 |
| 5 | consistency | 一致性 |
| 6 | revision_integrity | 修订完整性 |
| 7 | provenance_integrity | 溯源完整性 |
| 8 | pit_admissibility | PIT 准入 |
| 9 | source_health | 来源健康 |

最终 quality_report 的 dimensions 块：

```json
{
  "dimensions": {
    "completeness": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "validity": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "timeliness": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "freshness": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "consistency": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "revision_integrity": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "provenance_integrity": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "pit_admissibility": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] },
    "source_health": { "status": "PASS", "reasons": [], "metrics": {}, "evidence": [] }
  }
}
```

## 5. Research Boundary Contract

- **P14C-BND-001**: RESEARCH_END = 2026-09-22（冻结）。
- **P14C-BND-002**: VIRGIN_START = 2026-09-23（冻结）。
- P13-T = STOPPED / NOT EXECUTED。
"""

GOOD_MATRIX = """\
# P14-C Acceptance Matrix (synthetic)

> 状态：DRAFT — awaiting independent contract review
>
> Bidirectional closure verified: orphan_contract_invariants = 0, orphan_matrix_rows = 0

## Missingness

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-MISS-001 | 六类互斥分类，任何 observation 只能属于一类 | mutual_exclusion/ | 单一分类 | ✅ | ✅ |
| P14C-MISS-002 | SOURCE_EMPTY 不能被重新解释为 EXPECTED_ABSENCE | empty_vs_absence/ | 不混淆 | ✅ | ✅ |

## Revision

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-REV-001 | revision gap 检测 | revision_gap/ | revision_gap issue | ✅ | ✅ |

## Boundary

| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |
|-------------|------------|---------------|-----------------|-----|---|
| P14C-BND-001 | RESEARCH_END = 2026-09-22 | N/A | 常量不变 | ✅ | ✅ |
| P14C-BND-002 | VIRGIN_START = 2026-09-23 | N/A | 常量不变 | ✅ | ✅ |
"""


def _run(tmp_path, contract_text: str, matrix_text: str) -> dict:
    contract = tmp_path / "contract.md"
    matrix = tmp_path / "matrix.md"
    contract.write_text(contract_text, encoding="utf-8")
    matrix.write_text(matrix_text, encoding="utf-8")
    return harness.run_harness(contract, matrix)


def _replace(text: str, old: str, new: str) -> str:
    assert old in text, f"mutation anchor not found: {old!r}"
    assert text.count(old) == 1, f"mutation anchor not unique: {old!r}"
    return text.replace(old, new)


def _findings(result: dict, code: str) -> list[dict]:
    return [f for f in result["findings"] if f["check"] == code]


def _finding_ids(result: dict, code: str) -> set:
    return {f.get("id") for f in _findings(result, code) if f.get("id")}


def test_wellformed_docs_pass(tmp_path):
    result = _run(tmp_path, GOOD_CONTRACT, GOOD_MATRIX)
    assert result["status"] == "PASS"
    assert result["hard_count"] == 0
    assert result["findings"] == []


def test_exit_code(tmp_path):
    contract = tmp_path / "c.md"
    matrix = tmp_path / "m.md"
    contract.write_text(GOOD_CONTRACT, encoding="utf-8")
    matrix.write_text(GOOD_MATRIX, encoding="utf-8")
    assert harness.main(["--contract", str(contract), "--matrix", str(matrix)]) == 0
    bad_matrix = _replace(GOOD_MATRIX,
                          "| P14C-REV-001 | revision gap 检测 | revision_gap/ | "
                          "revision_gap issue | ✅ | ✅ |", "")
    matrix.write_text(bad_matrix, encoding="utf-8")
    assert harness.main(["--contract", str(contract), "--matrix", str(matrix)]) == 1


def test_orphan_matrix_row_and_stale_claim(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "- **P14C-MISS-002**: SOURCE_EMPTY 不能被重新解释为"
                   " EXPECTED_ABSENCE。\n", "")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert "P14C-MISS-002" in _finding_ids(result, "E003")
    assert _findings(result, "E012"), "stale 0/0 claim must be flagged"


def test_orphan_contract_invariant(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "- **P14C-REV-001**: revision gap 被检测并报告为 ANOMALY。",
                   "- **P14C-REV-001**: revision gap 被检测并报告为 ANOMALY。\n"
                   "- **P14C-MISS-009**: 额外不变量，矩阵中无对应行。")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert "P14C-MISS-009" in _finding_ids(result, "E004")


def test_duplicate_matrix_row_and_section(tmp_path):
    dup_block = (
        "\n## Revision\n\n"
        "| Contract ID | Requirement | Golden Fixture | Expected Result | E2E | CI |\n"
        "|-------------|------------|---------------|-----------------|-----|---|\n"
        "| P14C-REV-001 | revision gap 检测 | revision_gap/ | revision_gap issue "
        "| ✅ | ✅ |\n")
    result = _run(tmp_path, GOOD_CONTRACT, GOOD_MATRIX + dup_block)
    assert "P14C-REV-001" in _finding_ids(result, "E005")
    assert any("Revision" in f["detail"] for f in _findings(result, "E006"))


def test_alias_invariant_id(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "- **P14C-REV-001**: revision gap 被检测并报告为 ANOMALY。",
                   "- **P14C-REV-001**: revision gap 被检测并报告为 ANOMALY"
                   "（参见 REV-009）。")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert any(f["alias"] == "REV-009" for f in _findings(result, "E002"))


def test_malformed_invariant_format(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "- **P14C-MISS-002**: SOURCE_EMPTY 不能被重新解释为"
                   " EXPECTED_ABSENCE。",
                   "**P14C-MISS-002**: SOURCE_EMPTY 不能被重新解释为"
                   " EXPECTED_ABSENCE。")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert "P14C-MISS-002" in _finding_ids(result, "E017")
    assert "P14C-MISS-002" not in _finding_ids(result, "E003"), \
        "E017 is the root cause; E003 must be suppressed for the same id"


def test_fixture_control_field_in_expected_contract(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   '        "expected_dates": [str, ...],',
                   '        "expected_dates": [str, ...],\n'
                   '        "expected_empty": [],')
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert any("expected_empty" in f["detail"] for f in _findings(result, "E008"))


def test_boundary_constant_drift(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "RESEARCH_END = 2026-09-22", "RESEARCH_END = 2026-12-31")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert _findings(result, "E010")


def test_section_numbering_gap(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "## 5. Research Boundary Contract", "## 6. Research Boundary Contract")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert any("§4" in f["detail"] and "§6" in f["detail"]
               for f in _findings(result, "E007"))


def test_self_acceptance_claim(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "> 状态：DRAFT — awaiting independent contract review",
                   "> 状态：PASS — 已通过验收")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    assert _findings(result, "E011")


def test_semantic_drift_suspect(tmp_path):
    bad = _replace(GOOD_MATRIX,
                   "| P14C-REV-001 | revision gap 检测 |",
                   "| P14C-REV-001 | quality_score 评分 |")
    result = _run(tmp_path, GOOD_CONTRACT, bad)
    assert "P14C-REV-001" in _finding_ids(result, "W002")


def test_near_duplicate_invariants(tmp_path):
    bad = _replace(GOOD_CONTRACT,
                   "- **P14C-REV-001**: revision gap 被检测并报告为 ANOMALY。",
                   "- **P14C-REV-001**: revision gap 被检测并报告为 ANOMALY。\n"
                   "- **P14C-REV-002**: revision gap 被检测并报告为 ANOMALY"
                   "（无 resolved_value 字段）。")
    result = _run(tmp_path, bad, GOOD_MATRIX)
    near_dups = [f for f in _findings(result, "W003")
                 if f["ids"] == ["P14C-REV-001", "P14C-REV-002"]]
    assert near_dups, "near-duplicate pair must be flagged as W003"


def test_real_docs_characterization():
    """Snapshot of harness findings on the real documents.

    History: at harness introduction (2026-09-30, pre-R4) the documents
    produced 18 hard + 18 soft findings — duplicate Source Health matrix
    block, unnumbered Boundary section, off-by-one subsection numbering,
    bare-bold SH-001..003 invariants, RECON/DUP duplicated invariant text,
    and 12 matrix↔contract semantic drift suspects. The R4 documentation
    repair (driven by independent acceptance verdict 54d6b6e) resolved all
    of them; the harness now reports a clean PASS.

    This test deliberately pins the CLEAN state: any future contract edit
    that reintroduces a governance defect fails here, forcing a conscious
    snapshot update alongside independent review.
    """
    result = harness.run_harness(REAL_CONTRACT, REAL_MATRIX)

    assert result["status"] == "PASS"
    assert result["hard_count"] == 0
    assert result["soft_count"] == 0
    assert result["findings"] == []
    # Mechanical criteria from the R3 acceptance verdict (54d6b6e)
    stats = result["stats"]
    assert stats["contract_unique_ids"] == 61
    assert stats["matrix_unique_ids"] == 61
    assert stats["matrix_rows"] == 61  # 61 rows, no duplicates
    assert stats["contract_invariants_malformed_form"] == 0
    assert stats["contract_only"] == []
    assert stats["matrix_only"] == []
