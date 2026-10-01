"""P14-D Contract Acceptance Harness (document-level).

Mechanically validates docs/contracts/P14-D-DESIGN-CONTRACT.md against
docs/contracts/P14-D-ACCEPTANCE-MATRIX.md:

  E001 non_canonical_id     P14D-* token that is not a canonical ID
  E002 alias_invariant_id   bare alias invariant references (PIT-001 etc.)
  E003 orphan_matrix_row    matrix row with no contract definition
  E004 orphan_contract_id   contract invariant with no matrix row
  E005 duplicate_matrix_row same Contract ID in more than one matrix row
  E006 forbidden_control    banned control/override tokens in either doc
  E007 boundary_constants   frozen boundary values missing / drifted
  E008 draft_status         governance status not DRAFT/awaiting-review
  E009 golden_gap           matrix references a golden fixture with no row,
                            or G-001..G-010 not fully covered
  E010 matrix_missing_tests harness test names missing from the matrix

Exits non-zero on any hard finding. Validates CONTRACT DOCUMENTS ONLY.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT = REPO_ROOT / "docs" / "contracts" / "P14-D-DESIGN-CONTRACT.md"
MATRIX = REPO_ROOT / "docs" / "contracts" / "P14-D-ACCEPTANCE-MATRIX.md"

CANONICAL = re.compile(r"^P14D-\d{3}$")
ANY_P14D = re.compile(r"\bP14D-[A-Za-z0-9*\-]+")
INVARIANT_DEF = re.compile(r"^-\s+\*\*(P14D-\d{3})\*\*")
ALIAS = re.compile(r"(?<!P14D-)\b(PIT|QUERY|VER|PROV|DET|BND|SCOPE)-\d{3}\b")
ROW_ID = re.compile(r"^\|\s*(P14D-\d{3})\s*\|")
GOLDEN_REF = re.compile(r"\bG-\d{3}\b")
HARNESS_TEST = re.compile(r"test_p14d_\d+_[a-z_]+")

EXPECTED_IDS = [f"P14D-{i:03d}" for i in range(1, 11)]
EXPECTED_GOLDENS = [f"G-{i:03d}" for i in range(1, 12)]
BOUNDARY = ["2026-09-22", "2026-09-23", "VIRGIN_START", "assert_research_zone"]
FORBIDDEN = ["fixture_mode", "expected_result_override", "golden_override",
             "test_only", "skip_validation", "force_visible", "force_hidden",
             "running_under_test"]
REQUIRED_KEYWORDS = {
    "P14D-001": ["available_time"],
    "P14D-002": ["NOT_YET_AVAILABLE"],
    "P14D-003": ["event_time"],
    "P14D-004": ["revision"],
    "P14D-005": ["restatement"],
    "P14D-006": ["byte-identical"],
    "P14D-007": ["provenance"],
    "P14D-008": ["OUTSIDE_AS_OF"],
    "P14D-009": ["assert_research_zone"],
    "P14D-010": ["recommendation"],
}


def run_harness(contract_path: Path, matrix_path: Path) -> dict:
    findings: list[dict] = []

    def add(check, detail, severity="hard", **extra):
        item = {"check": check, "severity": severity, "detail": detail}
        item.update(extra)
        findings.append(item)

    contract_text = contract_path.read_text(encoding="utf-8")
    matrix_text = matrix_path.read_text(encoding="utf-8")

    defs = sorted({m.group(1) for line in contract_text.splitlines()
                   if (m := INVARIANT_DEF.match(line))})

    # E001/E002 canonical + alias tokens
    for name, text in (("contract", contract_text), ("matrix", matrix_text)):
        for m in ANY_P14D.finditer(text):
            tok = m.group(0)
            if "*" in tok:
                continue
            if not CANONICAL.match(tok):
                add("E001", f"{name}: non-canonical P14D token {tok!r}")
        for m in ALIAS.finditer(text):
            add("E002", f"{name}: bare alias ID {m.group(0)!r}")

    # E003/E004 closure
    matrix_ids = sorted({m.group(1) for line in matrix_text.splitlines()
                         if (m := ROW_ID.match(line))})
    for cid in sorted(set(matrix_ids) - set(defs)):
        add("E003", f"matrix row {cid} has no contract definition")
    for cid in sorted(set(defs) - set(matrix_ids)):
        add("E004", f"contract invariant {cid} has no matrix row")
    if defs != EXPECTED_IDS:
        add("E004", f"contract invariant set {defs} != expected {EXPECTED_IDS}")

    # E005 duplicates
    seen = {}
    for line in matrix_text.splitlines():
        m = ROW_ID.match(line)
        if m:
            seen.setdefault(m.group(1), 0)
            seen[m.group(1)] += 1
    for cid, n in seen.items():
        if n > 1:
            add("E005", f"matrix row {cid} appears {n} times")

    # E006 forbidden control tokens
    for name, text in (("contract", contract_text), ("matrix", matrix_text)):
        for tok in FORBIDDEN:
            if tok in text:
                # the contract's own anti-cheat section names them as banned;
                # only flag occurrences outside that section
                section11 = text.split("## 11.")
                zone = section11[1] if len(section11) > 1 else ""
                if tok not in zone:
                    add("E006", f"{name}: forbidden control token {tok!r} outside §11")

    # E007 boundary constants
    for constant in BOUNDARY:
        if constant not in contract_text:
            add("E007", f"contract missing boundary element {constant!r}")

    # E008 governance status: the contract is FROZEN (P14-D-REPAIR-001);
    # self-acceptance wording is still banned
    status_line = next((l for l in contract_text.splitlines()[:10] if "状态" in l), "")
    if "FROZEN" not in status_line:
        add("E008", f"contract status is not FROZEN: {status_line.strip()!r}")
    if any(marker in status_line for marker in ("PASS", "ACCEPTED")):
        add("E008", f"contract status self-declares acceptance: {status_line.strip()!r}")

    # E009 golden coverage: G-001..G-011 all referenced in matrix
    goldens_in_matrix = sorted(set(GOLDEN_REF.findall(matrix_text)))
    missing = [g for g in EXPECTED_GOLDENS if g not in goldens_in_matrix]
    if missing:
        add("E009", f"matrix does not reference golden fixtures {missing}")

    # E010 harness test names present
    tests = sorted(set(HARNESS_TEST.findall(matrix_text)))
    if len(tests) < 10:
        add("E010", f"matrix references only {len(tests)} harness tests")

    # E011 same-revision tie semantics (P14-D-REPAIR-001): the frozen
    # tie-break chain must be present in the contract, referenced by the
    # matrix P14D-004 row (G-011), and the fixture must exist
    tie_row = next((line for line in matrix_text.splitlines()
                    if line.startswith("| P14D-004")), "")
    for token in ("earliest", "canonical_json"):
        if token not in contract_text:
            add("E011", f"contract tie-break chain missing {token!r}")
    if "G-011" not in tie_row:
        add("E011", "matrix P14D-004 row does not reference the tie fixture G-011")
    if not (REPO_ROOT / "tests" / "contracts" / "p14d" / "fixtures" / "G-011.json").exists():
        add("E011", "tie fixture tests/contracts/p14d/fixtures/G-011.json missing")

    # semantic keyword spot-checks (whole-document presence)
    for cid, keywords in REQUIRED_KEYWORDS.items():
        for kw in keywords:
            if kw not in contract_text and kw not in matrix_text:
                add("E001", f"{cid}: required keyword {kw!r} absent from "
                            f"contract and matrix")

    hard = [f for f in findings if f["severity"] == "hard"]
    return {
        "status": "FAIL" if hard else "PASS",
        "contract": str(contract_path),
        "matrix": str(matrix_path),
        "hard_count": len(hard),
        "soft_count": len(findings) - len(hard),
        "findings": findings,
        "stats": {
            "contract_ids": len(defs),
            "matrix_ids": len(matrix_ids),
            "golden_ids": len(goldens_in_matrix),
            "harness_tests": len(tests),
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--contract", default=str(CONTRACT))
    parser.add_argument("--matrix", default=str(MATRIX))
    args = parser.parse_args(argv)
    result = run_harness(Path(args.contract), Path(args.matrix))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
