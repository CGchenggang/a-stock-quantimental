"""P14-C Contract Acceptance Harness.

Machine-verifiable governance audit of the P14-C Design Contract
(docs/contracts/P14-C-DESIGN-CONTRACT.md) against the Acceptance Matrix
(docs/contracts/P14-C-ACCEPTANCE-MATRIX.md).

Hard checks (each violation => harness FAIL, exit code 1):
  E001 malformed_p14c_id            P14C-* token that is not a canonical ID
  E002 alias_invariant_id           bare domain IDs (REV-001, INV-*, ...)
  E003 orphan_matrix_row            matrix row with no contract definition
  E004 orphan_contract_invariant    contract invariant with no matrix row
  E005 duplicate_matrix_row         same Contract ID in >1 matrix row
  E006 duplicate_matrix_section     same "## " section header twice
  E007 section_numbering            "## N." gaps / "### N.M" parent mismatch
  E008 fixture_control_field        banned test-control field inside the
                                    EXPECTED_CONTRACT structure block
  E009 nine_dimensions_mismatch     dimension table != frozen 9 / report JSON
                                    keys != table
  E010 boundary_constant_violation  RESEARCH_END / VIRGIN_START / STOPPED
  E011 self_acceptance_status       status header not "DRAFT - awaiting
                                    independent contract review"
  E012 stale_traceability_claim     matrix's orphan-count claim != computed
  E013 duplicate_invariant_content  two invariants, same domain, same text
  E014 malformed_matrix_row         row not exactly 6 cells
  E015 missing_prohibition          EXPECTED_CONTRACT fixture-field
                                    prohibition absent
  E016 missing_e2e_or_ci_mark       matrix row without E2E/CI check mark
  E017 malformed_invariant_format   invariant written as bold text outside
                                    the canonical "- **P14C-...**:" list form
Soft checks (report-only drift suspects):
  W001 duplicate_invariant_content  identical text across domains
  W002 semantic_drift_suspect       matrix requirement shares no content
                                    token with its contract invariant

This harness validates CONTRACT DOCUMENTS ONLY. It never inspects src/ or
tests/, and it must never be "made to pass" by editing implementation code:
if it reports violations, the findings are the deliverable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT = REPO_ROOT / "docs" / "contracts" / "P14-C-DESIGN-CONTRACT.md"
DEFAULT_MATRIX = REPO_ROOT / "docs" / "contracts" / "P14-C-ACCEPTANCE-MATRIX.md"

CANONICAL_ID = re.compile(r"^P14C-[A-Z]+(?:-[A-Z]+)?-\d{3}$")
ANY_P14C_TOKEN = re.compile(r"\bP14C-[A-Za-z0-9*\-]+")
BARE_ALIAS_IN_TEXT = re.compile(
    r"(?<!P14C-)\b(REV|TS|DUP|SH|COMP|EVID|FRESH|RR|DET|EXP|MISS|BND|RECON|PROV|INV)-\d{3}\b"
)
BARE_ALIAS_HEADING = re.compile(r"^###\s+\d+(?:\.\d+)?\s+([A-Z]{2,}-\d{3})\s*[:：]\s*(.*)$")
BOLD_INVARIANT = re.compile(r"^-\s+\*\*(P14C-[A-Z]+(?:-[A-Z]+)?-\d{3})\*\*\s*[:：]\s*(.*)$")
MALFORMED_INVARIANT = re.compile(
    r"^(?!-)\s*\*\*(P14C-[A-Z]+(?:-[A-Z]+)?-\d{3})\*\*\s*[:：]\s*(.*)$")
CANON_HEADING = re.compile(r"^###\s+(P14C-[A-Z]+(?:-[A-Z]+)?-\d{3})\s*[:：]\s*(.*)$")
H2_HEADING = re.compile(r"^##\s+(\d+)\.\s+")
H3_NUMBERED = re.compile(r"^###\s+(\d+)\.(\d+)")
FENCE = re.compile(r"^```")

NINE_DIMENSIONS = [
    "completeness",
    "validity",
    "timeliness",
    "freshness",
    "consistency",
    "revision_integrity",
    "provenance_integrity",
    "pit_admissibility",
    "source_health",
]

FIXTURE_CONTROL_FIELDS = [
    "expected_empty",
    "broken_source",
    "force_source_error",
    "fixture_mode",
]

BOUNDARY_CONSTANTS = [
    "RESEARCH_END = 2026-09-22",
    "VIRGIN_START = 2026-09-23",
]

DRAFT_STATUS_MARKERS = ("DRAFT",)
SELF_ACCEPTANCE_MARKERS = ("PASS", "ACCEPTED")

LATIN_TOKEN = re.compile(r"[a-z][a-z0-9_]{1,}")
CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
STOPWORDS = {
    "the", "and", "not", "must", "for", "when", "with", "from",
    "不得", "必须", "只能", "允许", "应当", "本文件",
}


def _tokens(text: str) -> set:
    out = set()
    for m in LATIN_TOKEN.finditer(text.lower()):
        tok = m.group(0).strip("_")
        for part in tok.split("_"):
            if len(part) >= 2 and part not in STOPWORDS:
                out.add(part)
    for run in CJK_RUN.findall(text):
        run_bigrams = [run] if len(run) == 1 else [run[k:k + 2] for k in range(len(run) - 1)]
        for bg in run_bigrams:
            if bg not in STOPWORDS:
                out.add(bg)
    return out


def _domain_of(contract_id: str) -> str:
    return contract_id[len("P14C-"):].rsplit("-", 1)[0]


class _Finder:
    """Shared line-walking helpers for one document."""

    def __init__(self, text: str):
        self.lines = text.splitlines()

    def fenced_block_after(self, start_line: int) -> tuple[int, str]:
        """Return (closing-fence index, block text) of the first fenced block
        at/after start_line."""
        i = start_line
        while i < len(self.lines):
            if FENCE.match(self.lines[i]):
                buf = []
                j = i + 1
                while j < len(self.lines) and not FENCE.match(self.lines[j]):
                    buf.append(self.lines[j])
                    j += 1
                return j, "\n".join(buf)
            i += 1
        return -1, ""


def extract_contract_invariants(text: str):
    """Return (defs, aliases, malformed): defs maps canonical ID -> invariant
    text; aliases maps bare ID (e.g. REV-001) -> text; malformed maps
    canonical ID -> text for invariants written outside the canonical
    "- **P14C-...**:" list form."""
    defs: dict[str, str] = {}
    aliases: dict[str, str] = {}
    malformed: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = BOLD_INVARIANT.match(line)
        if m:
            cid, buf = m.group(1), [m.group(2)]
            j = i + 1
            while j < len(lines) and lines[j].startswith("  ") and not BOLD_INVARIANT.match(lines[j]):
                buf.append(lines[j].strip())
                j += 1
            defs.setdefault(cid, " ".join(part for part in buf if part))
            i = j
            continue
        m = MALFORMED_INVARIANT.match(line)
        if m:
            cid, buf = m.group(1), [m.group(2)]
            j = i + 1
            while j < len(lines) and lines[j].startswith("  ") and not MALFORMED_INVARIANT.match(lines[j]):
                buf.append(lines[j].strip())
                j += 1
            malformed.setdefault(cid, " ".join(part for part in buf if part))
            i = j
            continue
        m = CANON_HEADING.match(line)
        if m:
            cid, buf = m.group(1), [m.group(2)]
            j = i + 1
            while j < len(lines) and not lines[j].startswith("#") \
                    and not lines[j].startswith("---") \
                    and not BOLD_INVARIANT.match(lines[j]) \
                    and not MALFORMED_INVARIANT.match(lines[j]):
                if lines[j].strip():
                    buf.append(lines[j].strip())
                j += 1
            defs.setdefault(cid, " ".join(buf))
            i = j
            continue
        m = BARE_ALIAS_HEADING.match(line)
        if m:
            aid, buf = m.group(1), [m.group(2)]
            j = i + 1
            while j < len(lines) and not lines[j].startswith("#") \
                    and not lines[j].startswith("---") \
                    and not BOLD_INVARIANT.match(lines[j]) \
                    and not MALFORMED_INVARIANT.match(lines[j]):
                if lines[j].strip():
                    buf.append(lines[j].strip())
                j += 1
            aliases.setdefault(aid, " ".join(buf))
            i = j
            continue
        i += 1
    return defs, aliases, malformed


def parse_matrix(text: str):
    """Return (rows, sections). rows carry id/requirement/e2e/ci/line."""
    rows, sections = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            sections.append((line[3:].strip(), ln))
            continue
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and CANONICAL_ID.match(cells[0]):
            rows.append({
                "id": cells[0],
                "requirement": cells[1] if len(cells) > 1 else "",
                "e2e": cells[-2] if len(cells) >= 2 else "",
                "ci": cells[-1] if len(cells) >= 2 else "",
                "ncells": len(cells),
                "line": ln,
            })
    return rows, sections


def run_harness(contract_path: Path, matrix_path: Path) -> dict:
    findings: list[dict] = []

    def add(check: str, severity: str, detail: str, **extra):
        item = {"check": check, "severity": severity, "detail": detail}
        item.update(extra)
        findings.append(item)

    contract_text = contract_path.read_text(encoding="utf-8")
    matrix_text = matrix_path.read_text(encoding="utf-8")

    defs, aliases, malformed = extract_contract_invariants(contract_text)
    rows, matrix_sections = parse_matrix(matrix_text)

    contract_ids = set(defs)
    matrix_ids = {r["id"] for r in rows}

    # --- E001 malformed P14C-* tokens (both documents) --------------------
    for doc_name, text in (("contract", contract_text), ("matrix", matrix_text)):
        for m in ANY_P14C_TOKEN.finditer(text):
            token = m.group(0)
            if "*" in token or token == "P14C-":
                continue  # meta-reference such as "全部 P14C-* Contract ID"
            if not CANONICAL_ID.match(token):
                add("E001", "hard",
                    f"{doc_name}: non-canonical P14C-* token {token!r}")

    # --- E002 alias invariant IDs -----------------------------------------
    alias_hits: dict[str, str] = {}
    for doc_name, text in (("contract", contract_text), ("matrix", matrix_text)):
        for m in BARE_ALIAS_IN_TEXT.finditer(text):
            alias_hits.setdefault(m.group(0), doc_name)
    for aid, doc_name in sorted(alias_hits.items()):
        add("E002", "hard",
            f"{doc_name}: bare alias invariant ID {aid!r} "
            f"(canonical form is P14C-{aid})", alias=aid)

    # --- E003/E004 bidirectional closure ----------------------------------
    matrix_only = sorted(matrix_ids - contract_ids)
    contract_only = sorted(contract_ids - matrix_ids)
    for cid in matrix_only:
        if cid in malformed:
            continue  # root cause reported as E017; not a missing definition
        add("E003", "hard",
            f"matrix row {cid} has no invariant definition in the design contract",
            id=cid)
    for cid in contract_only:
        add("E004", "hard",
            f"contract invariant {cid} has no Acceptance Matrix row", id=cid)

    # --- E017 malformed invariant format -----------------------------------
    for cid in sorted(malformed):
        add("E017", "hard",
            f"invariant {cid} is written as bare bold text instead of the "
            f"canonical '- **{cid}**:' list form; its Acceptance Matrix row "
            f"is therefore untraceable", id=cid)

    # --- E005 duplicate rows / E014 malformed rows / E016 marks ------------
    seen_ids: dict[str, int] = {}
    for row in rows:
        if row["id"] in seen_ids:
            add("E005", "hard",
                f"matrix row {row['id']} duplicated: line {seen_ids[row['id']]} "
                f"and line {row['line']}", id=row["id"])
        else:
            seen_ids[row["id"]] = row["line"]
        if row["ncells"] != 6:
            add("E014", "hard",
                f"matrix row {row['id']} (line {row['line']}) has "
                f"{row['ncells']} cells, expected 6")
        if row["e2e"] != "✅" or row["ci"] != "✅":
            add("E016", "hard",
                f"matrix row {row['id']} (line {row['line']}) missing E2E/CI "
                f"check mark (e2e={row['e2e']!r}, ci={row['ci']!r})")

    # --- E006 duplicate matrix section headers ----------------------------
    seen_sections: dict[str, int] = {}
    for title, ln in matrix_sections:
        if title in seen_sections:
            add("E006", "hard",
                f"matrix section header {title!r} duplicated: "
                f"line {seen_sections[title]} and line {ln}")
        else:
            seen_sections[title] = ln

    # --- E007 contract section numbering ----------------------------------
    contract_lines = contract_text.splitlines()
    h2_nums = [int(m.group(1)) for m in map(H2_HEADING.match, contract_lines) if m]
    for prev, curr in zip(h2_nums, h2_nums[1:]):
        if curr != prev + 1:
            add("E007", "hard",
                f"contract section numbering gap: §{prev} followed by §{curr}")
    current_h2 = None
    for line in contract_lines:
        m = H2_HEADING.match(line)
        if m:
            current_h2 = int(m.group(1))
            continue
        m = H3_NUMBERED.match(line)
        if m and current_h2 is not None and int(m.group(1)) != current_h2:
            add("E007", "hard",
                f"contract subsection §{m.group(1)}.{m.group(2)} does not match "
                f"enclosing section §{current_h2}")

    # --- E008/E015 EXPECTED_CONTRACT structure and prohibition -------------
    cf = _Finder(contract_text)
    struct_idx = next((i for i, l in enumerate(cf.lines)
                       if re.match(r"^###\s+\d+\.\d+.*结构", l)), None)
    if struct_idx is None:
        add("E008", "hard", "contract has no EXPECTED_CONTRACT structure subsection")
    else:
        _, block = cf.fenced_block_after(struct_idx)
        banned = [f for f in FIXTURE_CONTROL_FIELDS if f in block]
        if banned:
            add("E008", "hard",
                f"EXPECTED_CONTRACT structure block contains fixture-control "
                f"fields: {banned}", fields=banned)
        for required in ("expected_entities", "expected_dates"):
            if required not in block:
                add("E008", "hard",
                    f"EXPECTED_CONTRACT structure block missing {required!r}")
    section8_start = next((i for i, l in enumerate(cf.lines)
                           if re.match(r"^##\s+\d+\.\s+Expected Contract", l)), None)
    prohibition_zone = "\n".join(cf.lines[section8_start:section8_start + 30]) \
        if section8_start is not None else ""
    if "禁止" not in prohibition_zone or not all(
            f in prohibition_zone for f in FIXTURE_CONTROL_FIELDS):
        add("E015", "hard",
            "contract does not prohibit fixture-control fields "
            f"{FIXTURE_CONTROL_FIELDS} in the Expected Contract section")

    # --- E009 nine dimensions ----------------------------------------------
    dim_table_rows: list[str] = []
    report_block_keys: list[str] = []
    contract_lines = contract_text.splitlines()
    for i, line in enumerate(contract_lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].isdigit() and re.fullmatch(r"[a-z_]+", cells[1]):
            dim_table_rows.append(cells[1])
        if line.strip().startswith('"dimensions"'):
            open_fence = max(
                (k for k in range(i) if FENCE.match(contract_lines[k])), default=None)
            if open_fence is None:
                add("E009", "hard",
                    '"dimensions" block is not inside a fenced code block')
            else:
                _, block = cf.fenced_block_after(open_fence)
                tail = block[block.index('"dimensions"'):]
                report_block_keys = [
                    dim for dim in NINE_DIMENSIONS if f'"{dim}":' in tail]
    if sorted(set(dim_table_rows)) != sorted(NINE_DIMENSIONS) or \
            sorted(set(report_block_keys)) != sorted(NINE_DIMENSIONS):
        add("E009", "hard",
            "nine-dimension mismatch: "
            f"table={sorted(set(dim_table_rows))} report={sorted(set(report_block_keys))} "
            f"expected={sorted(NINE_DIMENSIONS)}")

    # --- E010 boundary constants --------------------------------------------
    for constant in BOUNDARY_CONSTANTS:
        if constant not in contract_text:
            add("E010", "hard", f"contract missing frozen boundary constant {constant!r}")
    if "STOPPED" not in contract_text:
        add("E010", "hard", "contract missing frozen P13-T STOPPED statement")
    for constant in BOUNDARY_CONSTANTS:
        if constant not in matrix_text:
            add("E010", "hard", f"matrix missing frozen boundary constant {constant!r}")

    # --- E011 governance status ---------------------------------------------
    for doc_name, text in (("contract", contract_text), ("matrix", matrix_text)):
        status_line = next((l for l in text.splitlines()[:15] if "状态" in l), "")
        if not any(marker in status_line for marker in DRAFT_STATUS_MARKERS):
            add("E011", "hard",
                f"{doc_name} status header is not a DRAFT/awaiting-review "
                f"status: {status_line.strip()!r}")
        elif any(marker in status_line for marker in SELF_ACCEPTANCE_MARKERS):
            add("E011", "hard",
                f"{doc_name} status header self-declares acceptance: "
                f"{status_line.strip()!r}")

    # --- E012 stale traceability claim --------------------------------------
    m = re.search(
        r"orphan_contract_invariants\s*=\s*(\d+)\s*,\s*orphan_matrix_rows\s*=\s*(\d+)",
        matrix_text)
    if m:
        claimed = (int(m.group(1)), int(m.group(2)))
        actual = (len(contract_only), len(matrix_only))
        if claimed != actual:
            add("E012", "hard",
                f"matrix claims orphan_contract_invariants={claimed[0]}, "
                f"orphan_matrix_rows={claimed[1]} but harness computed "
                f"{actual[0]} / {actual[1]}")

    # --- E013/W001 duplicate invariant content -------------------------------
    by_normalized: dict[str, list[str]] = {}
    for cid, text in defs.items():
        key = re.sub(r"[\s*：:。，、（）()【】\[\]/\"']", "", text).lower()
        by_normalized.setdefault(key, []).append(cid)
    for cids in by_normalized.values():
        if len(cids) < 2:
            continue
        domains = {_domain_of(c) for c in cids}
        if len(domains) == 1:
            add("E013", "hard",
                f"invariants {cids} share identical content within domain "
                f"{sorted(domains)[0]}", ids=sorted(cids))
        else:
            add("W001", "soft",
                f"invariants {cids} share identical content across domains "
                f"{sorted(domains)}", ids=sorted(cids))

    # --- W002 semantic drift suspects ----------------------------------------
    for row in rows:
        cid = row["id"]
        contract_inv = defs.get(cid) or malformed.get(cid) or aliases.get(cid[len("P14C-"):])
        if contract_inv is None:
            continue  # orphan; already reported as E003
        if not (_tokens(row["requirement"]) & _tokens(contract_inv)):
            add("W002", "soft",
                f"matrix row {cid} requirement shares no content token with "
                f"its contract invariant",
                requirement=row["requirement"], invariant=contract_inv, id=cid)

    hard = [f for f in findings if f["severity"] == "hard"]
    soft = [f for f in findings if f["severity"] == "soft"]
    return {
        "status": "FAIL" if hard else "PASS",
        "contract": str(contract_path),
        "matrix": str(matrix_path),
        "hard_count": len(hard),
        "soft_count": len(soft),
        "findings": findings,
        "stats": {
            "contract_invariants": len(contract_ids),
            "matrix_rows": len(rows),
            "contract_only": contract_only,
            "matrix_only": matrix_only,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    args = parser.parse_args(argv)
    result = run_harness(Path(args.contract), Path(args.matrix))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
