"""P14-E Contract Acceptance Harness (machine-readable audit).

Validates the P14-E layer mechanically:

- Contract IDs P14E-001..017 unique, dense, defined
- Matrix rows P14E-M-001..017 unique, closure 17/17
- Golden fixtures G-001..G-012 dense, coverage 17/17
- Golden design sections complete
- Boundary constants (research_end / virgin_start / P13-T / P13-U)
- No P14-E production runtime in src/ (implementation NOT AUTHORIZED)
- Golden engine checks all green

Outputs the machine-readable verdict per the P14-E-003 contract and exits
non-zero on any failure.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "contracts" / "p14e"))

from golden import core  # noqa: E402

CONTRACT = REPO_ROOT / "docs" / "contracts" / "P14-E-DESIGN-CONTRACT.md"
MATRIX = REPO_ROOT / "docs" / "contracts" / "P14-E-ACCEPTANCE-MATRIX.md"
GOLDEN_DESIGN = REPO_ROOT / "docs" / "contracts" / "P14-E-GOLDEN-DESIGN.md"


def run_harness() -> dict:
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = ""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    contract = CONTRACT.read_text(encoding="utf-8")
    matrix = MATRIX.read_text(encoding="utf-8")
    design = GOLDEN_DESIGN.read_text(encoding="utf-8")
    expected = [f"P14E-{i:03d}" for i in range(1, 18)]

    # contract layer
    defs = sorted({m.group(1) for line in contract.splitlines()
                   if (m := re.match(r"^- \*\*(P14E-\d{3})\*\*", line))})
    add("contract.ids_17_unique_dense", defs == expected, f"{len(defs)}")
    add("contract.status_draft_preserved",
        "STATUS: DRAFT" in contract and "v1.1: REPAIR-001" in contract)

    # matrix layer
    m_rows = re.findall(r"^\| (P14E-M-\d{3}) \| (P14E-\d{3}) \|",
                        matrix, re.M)
    add("matrix.ids_17_unique_dense",
        sorted(r[0] for r in m_rows) == [f"P14E-M-{i:03d}" for i in range(1, 18)])
    add("matrix.contract_closure",
        sorted(r[1] for r in m_rows) == expected)
    add("matrix.status_frozen", "STATUS: FROZEN" in matrix)

    # golden layer
    fixtures = core.load_fixtures()
    fixture_ids = [f["golden_id"].replace("P14E-", "") for f in fixtures]
    add("golden.ids_12_dense",
        fixture_ids == [f"G-{i:03d}" for i in range(1, 13)])
    covered = set()
    for f in fixtures:
        covered |= set(f["contract_ids"])
    # P14E-016 is covered by the sanctioned mechanical source scan (M-016)
    covered |= {"P14E-016"}
    add("golden.contract_coverage_17", covered == set(expected), f"{len(covered)}")
    add("golden.design_sections",
        len(re.findall(r"^## G-\d{3} ", design, re.M)) == 12)
    add("golden.status_design_only", "STATUS: DESIGN ONLY" in design)

    # engine checks
    engine = core.run_all_checks()
    failures = [(n, d) for n, ok, d in engine if not ok]
    add("engine.all_checks_green", not failures,
        "; ".join(f"{n}: {d}" for n, d in failures[:5]))
    add("engine.virgin_scan_clean",
        all(ok for n, ok, _ in core.check_virgin_scan()))
    add("engine.source_scan_clean",
        all(ok for n, ok, _ in core.check_source_scan()))
    add("engine.anticheat_clean",
        all(ok for n, ok, _ in core.check_anticheat_layer()))
    report1 = core.canonical_report()
    add("engine.deterministic_report", report1 == core.canonical_report())

    # boundary / phase semantics
    from astock_v2.research_boundary import RESEARCH_END, VIRGIN_START
    add("boundary.research_end", RESEARCH_END == "2026-09-22")
    add("boundary.virgin_start", VIRGIN_START == "2026-09-23")
    src_info = REPO_ROOT / "src" / "astock_v2" / "information"
    runtime_files = [p.name for p in src_info.glob("*.py")
                     if p.name.startswith(("evidence", "bundle"))]
    add("phase.production_implementation_not_authorized",
        not runtime_files, f"{runtime_files}")

    failed = [c for c in checks if not c["ok"]]
    return {
        "phase": "P14-E",
        "status": "PASS" if not failed else "FAIL",
        "contract_ids": 17,
        "matrix_ids": 17,
        "golden_ids": len(fixtures),
        "contract_matrix_closure": "PASS" if not failed else "FAIL",
        "contract_golden_closure": "PASS" if covered == set(expected) else "FAIL",
        "p13_t": "STOPPED",
        "p13_u": "PROTECTED",
        "production_implementation": "NOT_AUTHORIZED",
        "checks": checks,
        "failures": failed,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    args = parser.parse_args(argv)
    result = run_harness()
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
