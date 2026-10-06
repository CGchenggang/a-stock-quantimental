# AI Handoff — A-Stock Quantimental Takeover Entry Point

> PURPOSE: the first document a new AI session reads. It is an INDEX and a
> rulebook — NOT a history copy. The single source of truth for full
> project history is `docs/PROJECT_STATUS.md`.
> Last consolidated: 2026-10-06 at Exact HEAD `5f61ba088a64bca2b631b1596dfe3dd283896f4a`
> (the commit that created this handoff; its predecessor
> `c9e498fa014a2761f451c777c1a597f387ca904e` is the independently accepted
> P13-O Forward Model Execution baseline).

## 1. Repository

`CGchenggang/a-stock-quantimental` (GitHub; local `E:\git-ground\a-stock-quantimental`).

## 2. Exact HEAD

`5f61ba088a64bca2b631b1596dfe3dd283896f4a` — the commit that created
this handoff document (its parent
`c9e498fa014a2761f451c777c1a597f387ca904e` is the independently accepted
P13-O Forward Model Execution state). ALWAYS re-verify with
`git rev-parse HEAD` and `git fetch` before working; never assume this
SHA is still current.

## 3. Accepted phases (all PASS / INDEPENDENTLY ACCEPTED)

P13-M · P13-N · P13-O · P13-P · P13-Q · P13-R · P13-S · P13-U ·
P14-A · P14-B · P14-C · P14-D · P14-E · R3-A · R4-A · R4-B · R4-C ·
P13-O-ARTIFACT-001 (= NOT RECOVERABLE) · P13-O-FORWARD-MODEL-001
(CONTRACT+DESIGN) · AUTHORIZATION-PRECHECK · AUTHORIZATION-CANDIDATES ·
P13-O-FORWARD-MODEL-EXECUTION-001 (+ NARROW-REPAIR-001/002) ·
P14-D→P14-E Integration Contract + implementation.

## 4. Protected phases

- **P13-T = STOPPED / NOT EXECUTED** — virgin holdout evaluation.
- **P13-U = PROTECTED** — virgin-zone integrity (decision dates ≥
  2026-09-23 are absolutely excluded from training/calibration/
  validation/research consumption).

## 5. Current phase

**R4-D = CONTRACT ACCEPTED / APPLY BLOCKED — ELIGIBLE FOR
AUTHORIZATION** (P13O-F-027 conditions C1–C12 all satisfied; the APPLY
unlock is a Human Authorization act that has NOT been granted).

## 6. Current research boundary

```text
research_end = 2026-09-22
virgin_start = 2026-09-23
universe     = universe-d8c5016b1ded0984 (76 symbols,
               data/industry/validation_universe_76.txt, committed)
```

Guard: `assert_research_zone` fail-fast — any research decision date ≥
2026-09-23 must raise, never filter-and-continue.

## 7. Frozen artifacts (exactly ONE of each; SHAs audited)

| artifact | sha256 |
|---|---|
| MODEL_APPLICATION | `97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664` |
| MODEL_APPLICATION_MANIFEST | `041c5552733b2c81586385d4ddfe40989004c6904daa4db64c2d4adab9c713a2` |
| CALIBRATION | `6e341fcd906bfbb72a34e3e33fadc7a1c152051e571a2ab90726c55d68142bc9` |
| CALIBRATION_MANIFEST | `b758015ade2d6ee1dfe8dfb8d00fd0eb169b589cb932b67414ebeebc5d3f5d7c` |

Location: `docs/artifacts/p13o-forward-model/`. Evidence:
`docs/artifacts/P13-O-FORWARD-MODEL-ARTIFACT-EVIDENCE.md`.

## 8. Frozen model identity

```text
model_id       = p13o-forward-logistic
model_version  = 97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664
model_variant  = industry_5_20
feature_set_id = fs-d1f3bdca3d9b8ba784496b63a240831d3112f1121423198f058ab9328e3a3afe
scope_sha256   = b7d807a318996e5b4623e82d07a4575143feb8fbdc141ed5c0bd62a0e6a764c1
protocol       = p13o-logistic-gd-500x0.05-v1
seed           = 20260929
prediction     = P(next trading day close-up | info visible at as_of)
```

Any byte change to the artifact = a NEW model_version under a NEW
authorization. Never edit these values in place.

## 9. R4-D status

CONTRACT ACCEPTED (v2, R4D-001..019) / APPLY BLOCKED / IMPLEMENTATION
NOT AUTHORIZED — but **ELIGIBLE FOR AUTHORIZATION** (C1–C12 satisfied).
The R4-D implementation is a single minimal integration point
(orchestrator consumes the resolver's probability block instead of the
legacy `p_up[5]` key) and requires explicit Human Authorization first.

## 10. Human Authorization status

Granted historically: P14-D→P14-E integration implementation; P13-O
forward-model parameters (FROZEN record); EXECUTION-001. NOT granted:
R4-D APPLY unlock; R4-D implementation; P14-F (NOT AUTHORIZED); P13-T
execution. Authorization decisions belong to the project owner — never
inferred from tests passing.

## 11. Required documents to read (in order)

1. `docs/AI_HANDOFF.md` (this file)
2. `docs/PROJECT_STATUS.md` — full history + current gate (search the
   LAST sections first for current state)
3. Task-relevant contracts under `docs/contracts/` (esp.
   `R4-D-CALIBRATED-PROBABILITY-APPLY-CONTRACT.md`,
   `P13-O-FORWARD-MODEL-ARTIFACT-CONTRACT.md`)
4. `docs/artifacts/P13-O-FORWARD-MODEL-HUMAN-AUTHORIZATION.md` (FROZEN)
5. `docs/artifacts/P13-O-FORWARD-MODEL-ARTIFACT-EVIDENCE.md`

## 12. Forbidden actions (standing)

- Do not modify the frozen artifacts, SHAs, or identity fields.
- Do not touch P13-T/P13-U or any decision date ≥ 2026-09-23.
- Do not retrain / recalibrate outside a new explicit authorization.
- Do not reuse the P13-Q pooled calibration or historical OOS
  predictions as forward artifacts (R4D-003c).
- Do not implement R4-D APPLY without explicit Human Authorization.
- Do not start P14-F. Do not create new governance phases ad hoc.
- Do not modify `src/astock_v2/information/pit.py` / `research_query.py`
  / `evidence.py` semantics (accepted authority chain).
- Do not self-declare PASS / ACCEPTED / AUTHORIZED.

## 13. First action for a new AI

**READ-ONLY TAKEOVER AUDIT before implementing any task**: verify
`git rev-parse HEAD` against the owner's stated baseline; `git fetch`
and check divergence; `git status --short` clean; re-verify the frozen
artifact SHAs (§7); run `python -m pytest -q` and the three audits
(`scripts/audit_p14c_contract.py`, `audit_p14d_contract.py`,
`audit_p14e_contract.py`); read the task-relevant contract sections.
Only then implement within the stated scope.

**Do not infer authorization from tests passing.** Tests verify
behavior; Human Authorization controls progression.
