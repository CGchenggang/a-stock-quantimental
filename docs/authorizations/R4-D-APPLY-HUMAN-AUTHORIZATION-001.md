# R4-D APPLY — Human Authorization Record

> Authorization ID: **R4-D-APPLY-HUMAN-AUTHORIZATION-001**
> Status: **GRANTED — HUMAN AUTHORIZATION**
> Granted by: project owner (Lead Agent / Independent Acceptance authority)
> Authorized baseline HEAD: `18a823539f5142a6a161baf5f1a787a5f1a46a6d`
> Recorded: 2026-10-07 (record created at the owner's instruction; this
> record transcribes the owner's authorization verbatim in scope and
> does not expand, reinterpret, or modify it)

## Authorized scope

The implementation execution agent (ZCODE) is authorized to implement
the **R4-D Calibrated Probability Apply-Path** exactly per the accepted
contract `docs/contracts/R4-D-CALIBRATED-PROBABILITY-APPLY-CONTRACT.md`
(v2, R4D-001..019) and design
`docs/design/R4-D-CALIBRATED-PROBABILITY-APPLY-DESIGN.md`:

- **A. MODEL_APPLICATION consumption** — the frozen artifact
  (`97602f4d…664`) is the forward model authority; no retraining,
  refitting, recreation, modification, parameter inference, or dynamic
  model selection.
- **B. CALIBRATION consumption** — the frozen bound calibration
  (`6e341fcd…42bc9`); no refit, no parameter search, no registry
  rewrite, no substitution.
- **C. Probability resolver** — the contract-defined probability block
  (`probability_status / probability / probability_horizon / model_id /
  model_version / calibration_id / calibration_version / policy_id /
  policy_version / feature_set_id / eligibility_reason`); `probability`
  present ONLY when `probability_status == CALIBRATED`.
- **D. Calibration formula** — `sigmoid(a + b·logit(p_raw))` with the
  contract clipping; no alternative methods.
- **E. Eligibility** — explicit states `CALIBRATED / NOT_AVAILABLE(reason)
  / INELIGIBLE(reason)`; no silent conversion.
- **F. No silent fallback** — forbidden: missing calibration → raw
  score; missing model → fabricated probability; feature mismatch →
  approximation; unknown policy → default policy; historical OOS
  prediction → p_raw.
- **G. R4-A integration** — the ONLY authorized production touch is the
  contract integration point: the legacy probability scaffold `p_up[5]`
  is replaced by the accepted R4-D probability block. No R4-A/B/C
  redesign.
- **H. Recommendation / policy integration** — frozen policy semantics
  (`threshold_platt_p50`, calibrated p ≥ 0.5 → PAPER_TEST/HOLD); no
  threshold search, no policy optimization, no alpha/performance claims.
- **I. Ledger provenance** — the full R4-D probability block in the
  ledger `input_snapshot`; provenance chain Recommendation → Probability
  → Calibration → Model → Features → ResearchPacket → P14-E evidence
  bundle → P14-D selection state remains traceable.

## Boundaries that remain in force

- **Registry READ-ONLY**: `data/industry/p13q/`, `data/industry/p13r/` —
  no registry write, promotion, threshold modification, policy
  modification, or calibration modification.
- **Forbidden phases**: P13-T (STOPPED / NOT EXECUTED), P14-F (NOT
  AUTHORIZED). Also forbidden: retraining, recalibration, new model
  creation, new calibration creation, holdout evaluation, policy
  redesign, threshold search, P14-D/E redesign, R4-A/B/C redesign.
- **Protected boundary**: `research_end = 2026-09-22`, `virgin_start =
  2026-09-23`, `universe = universe-d8c5016b1ded0984` (76 symbols);
  `assert_research_zone` preserved; no consumption of decision dates ≥
  2026-09-23 (virgin prices/labels, holdout-derived
  factors/calibration/policy, P13-T evaluation data).
- **Frozen artifacts** (MUST remain unchanged; hash post-check
  mandatory):
  - MODEL_APPLICATION `97602f4d9a794587e5e1a01357c5504c1323bcb7b73032c0f0d8db3abe8ed664`
  - MODEL_APPLICATION_MANIFEST `041c5552733b2c81586385d4ddfe40989004c6904daa4db64c2d4adab9c713a2`
  - CALIBRATION `6e341fcd906bfbb72a34e3e33fadc7a1c152051e571a2ab90726c55d68142bc9`
  - CALIBRATION_MANIFEST `b758015ade2d6ee1dfe8dfb8d00fd0eb169b589cb932b67414ebeebc5d3f5d7c`

## Governance sequence (must not be collapsed)

```text
Human Authorization (THIS RECORD)
        ↓
ZCODE Implementation
        ↓
ZCODE Verification
        ↓
ZCODE Handoff
        ↓
Lead Agent Independent Audit
        ↓
Independent Acceptance
        ↓
Only then next authorized phase
```

IMPLEMENTATION AUTHORIZED ≠ INDEPENDENT ACCEPTANCE ≠ PRODUCTION
APPROVAL. The implementation agent MUST NOT self-declare PASS /
ACCEPTED / INDEPENDENTLY ACCEPTED / PRODUCTION APPROVED / P14-F
AUTHORIZED. The next decision belongs to the Lead Agent / project owner.
