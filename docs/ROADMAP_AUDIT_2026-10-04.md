# Project Roadmap Audit — 2026-10-04

> Audit agent: ZCODE (implementation/repository audit only — not product owner, not architecture
> authority, not independent acceptance authority). No PASS/ACCEPTED/AUTHORIZED is self-declared.
> Scope: evidence-based inventory of what the repository actually has today, mapped onto the
> R0–R5 product roadmap. No implementation was performed.

---

## 1. Executive Summary

The repository contains a **dual-structure quantitative research codebase**:

1. **A production-shaped research stack in `src/` (7,532 LOC)** — data stores/providers, PIT
   adapters, 8 factors, model/risk/regime primitives, backtest/OOS/leakage primitives, a
   research-agent orchestrator (53 LOC), recommendation-ledger primitives, and the complete
   P14 information/evidence authority chain (P14-A/B/C/D/E, independently accepted).
2. **A research + operations layer in `scripts/` (15,118 LOC)** — the P13-M/O/P/Q/R/S research
   pipeline that produced a real 94,760-row OOS baseline over a frozen 76-stock universe, plus
   a full V1-era operational toolset (pre-market pipeline, morning/mid-day collectors, Feishu
   reports, Xueqiu/EastMoney sentiment, macro event monitor, global liquidity radar, calendars).

Tests: 10,353 LOC, 583 collected tests, all green (§20 evidence). CI runs full pytest + P14-C/D/E
contract audits + P13-M regression per push.

**The single most important structural finding**: the P13/P14 work built two parallel worlds that
are not yet joined — the **P13 research path** (legacy local store → provider adapters → factors →
76-stock OOS → calibration → policies) and the **P14 information path** (RawStore → normalization →
query → evidence, currently **fixture-source-only**). The agent (`agent/orchestrator.py`) consumes
the legacy provider path, not P14 evidence. The shortest credible path to a first usable
Research/Recommendation Agent is **bridging these two worlds with one real source adapter and
one evidence-backed packet wiring**, not building new architecture.

Phase completion ≠ product completion: a usable agent loop exists in pieces; no end-to-end
evidence-backed loop is wired today.

## 2. Current HEAD

`4ff243c66b1906a4b0a8ddbfc082413b9b9f893f` (matches the task-stated accepted P14-E HEAD).
origin/main in sync (0/0). Working tree clean. 569 commits total.

Commit chain (most recent): `4ff243c` (contract STATUS lifecycle sync, docs-only) ← `d100d01`
(status sync) ← `69cfe2a` (P14-D→P14-E integration implementation, 7 files +318/−181) ←
`3ec2b86` (Human Authorization record) ← `0067807` (contract Independent Acceptance record) ←
`51a769f` (Contract v2).

## 3. Accepted Baseline

Independently accepted (per PROJECT_STATUS.md and repo records): P13-M/N/O/P/Q/R/S PASS;
P13-T STOPPED / NOT EXECUTED; P13-U PASS / PROTECTED (ACCUMULATING); P14-A/B/C/D PASS;
P14-E-004/005/006 PASS; P14-D→P14-E Integration Contract v2 PASS / INDEPENDENTLY ACCEPTED
(`0067807`); Human Authorization GRANTED (`3ec2b86`); integration implementation delivered
(`69cfe2a`). P14-F NOT AUTHORIZED.

Live evidence at audit time: full pytest **583 passed / 2 warnings / 0 failed**; P14-C audit
exit 0 (61/61/61 closure); P14-D audit exit 0; P14-E audit exit 0 (17/17 + 26/26 golden checks);
P13-M pooled regression 3 passed; exact-head CI run `37189305728` (HEAD `d100d01`) and
`37190466113` (HEAD `4ff243c`) both completed/success with all steps green.

## 4. PROJECT_STATUS Consistency

**DRIFT FOUND — one item.**

| # | Expected (per task/owner) | Actual (repo) | Evidence | Recommended correction |
|---|---|---|---|---|
| 1 | "P14-E INDEPENDENTLY ACCEPTED" | PROJECT_STATUS records "INTEGRATION IMPLEMENTED — PENDING INDEPENDENT ACCEPTANCE"; no implementation-acceptance record commit exists on main | `docs/PROJECT_STATUS.md` Current Phase; `git log` (no acceptance commit after `4ff243c`) | The acceptance authority should record the implementation Independent Acceptance in PROJECT_STATUS + an acceptance-record commit (outside this audit). Until recorded, the repo's own status remains "PENDING". |

Everything else checked **CONSISTENT**: Current Commit convention (newest content commit
`69cfe2a`, docs-only commits on top), research boundary (research_end 2026-09-22 /
virgin_start 2026-09-23), P13-T STOPPED, P13-U PROTECTED, P14-F NOT AUTHORIZED, accepted-phase
table, CI evidence records. One cosmetic markdown nit: an unbalanced `**` at the end of the
Current Commit section's second paragraph (no factual impact).

## 5. R0 Foundation Inventory

| Capability | Status | Files | Tests | Evidence / Limitation |
|---|---|---|---|---|
| Local A-share daily/index historical store | IMPLEMENTED | `data/local_store.py` (144), `data/clean/{cn_stock_daily,cn_index_daily}` (71 MB local), `data/raw` (34 MB); `scripts/download_cn_stock_history.py` (196) | `test_local_store.py`, `test_historical_loader.py` | Atomic, reproducible store; 76-stock daily history present locally |
| Data provider abstraction + legacy adapters | IMPLEMENTED | `data/providers.py` (ABC), `legacy_provider.py`, `legacy_market_provider(_impl).py`, `legacy_adapter.py`, `legacy_runtime.py` | `test_legacy_*` (7 files), `test_p8f_provider_equivalence.py` | V1-era providers battle-tested; equivalence test locks behavior |
| PIT handling (legacy research path) | IMPLEMENTED | `data/pit_adapter.py` (139), `data/pit_store.py`, `data/legacy_cache.py` | `test_pit.py`, `test_pit_adapter.py`, `test_pit_adapter_daily.py`, `test_legacy_cache_pit.py` | Decision-time visibility semantics enforced; note `data/pit/` dir is empty (runtime store lives under `data/clean`) |
| Industry membership (multi-source) | IMPLEMENTED | `scripts/import_sw_industry_membership.py` (212, AKShare/official XLS), `import_cninfo_*`, `import_tushare_*`; `data/industry/sw_official_sw1_membership_all.csv` (+ cninfo/raw variants) | `test_import_sw/cninfo/tushare_industry_membership.py` | Historical (point-in-time) membership imported; feeds P13-M pooled context |
| Industry-relative factor context | IMPLEMENTED | `industry_relative.py` (599), `industry_loader.py`, `relative_context.py` | `test_industry_relative.py` (CI P13-M regression), `test_industry.py` | P13-M pooled context ~32× optimized, byte-identical outputs |
| Freshness | IMPLEMENTED | `data/freshness.py`, `information/freshness.py` | `test_freshness.py` | Explicit per-source policies |
| P14 raw evidence authority (P14-B) | IMPLEMENTED | `information/raw_store.py` (262), durable `raw_ingestion_audit.jsonl` | `test_p14b_raw_store.py` | Append-only, idempotent, mutation-detecting |
| P14 source reconciliation/quality (P14-C) | IMPLEMENTED | `information/quality.py` (276), `reconciliation.py`, `source_health.py` | `test_p14c_*` (4 files + e2e) | 9-dimension quality report; expected-contract completeness |
| P14 PIT/query/version authority (P14-D) | IMPLEMENTED | `information/pit.py` (125), `research_query.py` (192), `research_boundary.py` | P14-D harness + golden (11 fixtures) | Single selection authority `visible_revisions`/`resolve_selection`; virgin guard |
| P14 evidence/provenance consumer (P14-E) | IMPLEMENTED | `information/evidence.py` (351), `evidence_store.py` | `test_p14e_production_impl.py` (27 tests) | Pure verbatim consumer of resolved selection state; mandatory RawStore reverse trace |
| Real external source adapters | **MISSING** | — (only `adapters_fixture.py`, 4 fixture adapters) | — | P14-A known limitation #8; the P14 chain runs on fixtures today |
| News / policy / geopolitical sources | **MISSING** | — | — | Nothing in the P14 layer |

**Authority chain verified**: P14-B (raw identity) → P14-C (reconciliation) → P14-D (PIT/
selection/version authority — `visible_revisions` + `resolve_selection` in `pit.py`, sole
classification point, sole caller `run_query`) → P14-E (consumer). Repo-wide scan confirms no
downstream module re-derives selection semantics (`evidence.py` contains zero comparison
machinery after `69cfe2a`; no other src module imports selection primitives for deciding).

## 6. R1 Research Engine Inventory

| Capability | Status | Files | Evidence |
|---|---|---|---|
| Factor engine | IMPLEMENTED | `factors/__init__.py` (175): momentum, volatility, trend, volume_ratio, close_to_high, close_to_low, range_ratio, close_location + winsorize/zscore/correlation/decorrelate; df-variants in `factors/technical.py`, `fundamental.py`, `events.py` | `test_factors.py` |
| Feature construction (PIT dataset) | IMPLEMENTED | `local_pipeline.py` (226, PIT-safe factor/label dataset), `factor_inputs.py`, `factor_contracts.py`, `industry_relative.py` | `test_local_pipeline.py`, `test_factor_inputs.py`, `test_factor_contracts.py` |
| Market regime | IMPLEMENTED | `regime.py` (72, multi-input classifier); `scripts/market_regime_check.py`, `monthly_regime.py`; P13-O `regime_analysis.json` | `test_regime.py` |
| Probability model | PARTIAL | `model/probability.py` (30 LOC primitives), `probability_inputs.py`; real predictions live in the P13-M/O pipeline over local data | `test_probability.py`, `test_probability_inputs.py` |
| Calibration | PARTIAL (src) / IMPLEMENTED (research) | src: `calibration.py` (62 diagnostics), `model/calibration.py` (16, brier only). Research: `scripts/run_p13q_analysis.py` (639: ECE, slope-IRLS, Platt-Newton, Isotonic-PAVA) with fitted artifacts in `data/industry/p13q/` (13 files) | `test_calibration.py`, `test_p13q_calibration.py` (byte-identical artifacts), `test_model_evaluation.py` |
| Risk model | PARTIAL | `risk/engine.py`, `decision.py` (14-line gate glue); P13-R risk filters are research-side | `test_p8d_orchestration.py` |
| Research signal generation | IMPLEMENTED (research-only) | `scripts/run_p13r_analysis.py` (697): 8 frozen decision policies over calibrated P13-Q outputs; `data/industry/p13r/decision_policy_registry.json` (research_only) | `test_p13r_recommendation.py` |

Key research facts already established (P13-Q/P13-R, independently accepted): raw probabilities
are directionally sound but slope-compressed (~0.17) → Platt calibration validated; **no policy's
net return / hit rate significantly beat hold-all** (cluster bootstrap CIs contain 0); coverage
reduction and medium costs (10+10 bp) eat tactical turnover. This directly shapes what a "first
usable agent" may honestly claim (research/paper-test posture, not alpha claims).

## 7. R2 Validation Engine Inventory

| Capability | Status | Files | Evidence |
|---|---|---|---|
| Backtest | PARTIAL (primitive engine) | `backtest/engine.py` (60), `execution.py` (143), CLI `backtest` subcommand | `test_backtest.py`, `test_trading_costs.py` |
| Walk-forward | PARTIAL (primitives) | `backtest/walk_forward.py` (14 LOC `Fold`), `validation.py` (46 LOC) | `test_validation.py` |
| OOS evaluation | IMPLEMENTED | `oos.py` + the real P13-O pipeline: `scripts/run_p13o_analysis.py` produced `data/industry/p13o/oos_predictions_76.json` (94,760 rows) + bootstrap/time/symbol/industry stability + cost sensitivity (16 artifact files) | `test_p13p_analysis.py` |
| Holdout | STOPPED / PROTECTED | `scripts/run_p13u_gate.py` (314), frozen boundary `research_boundary.py` | `test_p13u_holdout_gate.py`; virgin zone = 2 trading days (2026-09-23/24), P13-T STOPPED |
| Leakage detection | IMPLEMENTED | `leakage.py` (41) | `test_leakage.py`; per-phase PIT audit docs (`P13Q_PIT_AUDIT.md` etc.) |
| Robustness / sensitivity | IMPLEMENTED (research-side) | P13-O bootstrap/cost artifacts; P13-P factor redundancy | P13O/P13P acceptance docs |
| Stress testing | **MISSING** | — | — |
| Reproducibility | IMPLEMENTED | byte-identical double-run culture, deterministic manifests, golden engines, `--collect-only` diagnostics in CI | acceptance docs; CI workflow |
| Research/Validation/OOS/Holdout separation | IMPLEMENTED (governance) | `research_boundary.py` single source; `assert_research_zone` fail-fast in P13-Q/R entries + P14 `select_asof`; research_only registries | P13-U gate + P14 tests |

**Boundary check (R2)**: no contamination found. Calibrators fitted on discovery OOS rows
(< 2025-01-01) and evaluated on validation rows (≥ 2025-01-01) — fixed a priori in
`run_p13q_analysis.py`/`run_p13r_analysis.py`; the virgin zone (2026-09-23+) is guarded by
`assert_research_zone` fail-fasts and the P13-U consumption audit. No BOUNDARY_RISK to report.
Tests do distinguish research vs validation vs holdout artifacts (P13-Q/R windows, P13-U gate,
golden fixtures use synthetic dates 2026-03/2099-01).

## 8. R3 Information + Evidence Inventory

| Capability | Status | Data source / files | Notes |
|---|---|---|---|
| Information contract, ingestion, dedup/conflict, normalization | IMPLEMENTED | `information/*` (P14-A/B) | 7 source categories, 9 **fixture** sources |
| Company announcements | SCAFFOLD_ONLY | fixture adapter `company_announcement` | No real feed |
| Macro (PMI) | SCAFFOLD_ONLY + standalone tool | fixture `macro_pmi_cn`; `scripts/macro_event_monitor.py` (229, v0.2, standalone) | Not wired to P14 layer |
| Overseas market info | SCAFFOLD_ONLY + standalone tool | fixture `us_index_daily`; `scripts/global_liquidity_radar.py` (standalone) | Not wired |
| Sentiment | PARTIAL (standalone) | `scripts/xueqiu_sentiment.py` (230, Xueqiu+EastMoney multi-source) | V1-era tool; no PIT/evidence integration |
| News | **MISSING** | — | No source, adapter, or query path |
| Policy / geopolitical | **MISSING** (in information layer) | `macro_event_monitor.py` partially covers macro events | No PIT-safe policy source |
| Industry information | IMPLEMENTED | SW/cninfo/tushare membership imports + P13-M industry context | Real data, PIT-safe via historical membership |
| Company events | PARTIAL | `factors/events.py`, `data/events.py`, `scripts/earnings_calendar.py`, `event_calendar_builder.py`, `unlock_calendar.py` | Calendar-level, not evidence-integrated |
| Query interface (as-of) | IMPLEMENTED | P14-D `run_query` / `select_asof` (virgin-guarded) | Fixture-data-bound today |
| Evidence handling + provenance + reverse trace | IMPLEMENTED | P14-E bundle/reverse-trace/P14-B anchoring | — |

**Conclusion**: R3's *infrastructure* is complete and independently accepted; its *content* is
fixture-bound. The fastest R3 win is admitting the **local historical store as the first real
source** (it already exists, is PIT-safe, and powers the P13 pipeline), then the standalone
collectors (macro/sentiment/overseas) as subsequent adapters.

## 9. R4 Agent + Recommendation Inventory

| Capability | Status | Files | Evidence |
|---|---|---|---|
| Research Agent (packet) | PARTIAL | `agent/orchestrator.py` (53 LOC): `ResearchPacket` (9 sections) + `ResearchOrchestrator` (build / build_from_provider / recommendation_record / research_state) | `test_recommendation_orchestrator.py`, `test_agent_ledger.py`, `test_p8d_research_bridge.py` |
| Decision rule | PARTIAL (simple, conservative) | quality < 0.75 → NO_ACTION; calibrated ∧ p5 ≥ 0.60 → PAPER_TEST; else RESEARCH; actions map PAPER_TEST→HOLD, else NO_ACTION — **no BUY/SELL generation** | consistent with P13-R findings |
| Research query orchestration | PARTIAL | P14-D `run_query`/`select_asof` exist; **no agent-level loop wiring P14-E evidence into packets** | — |
| Evidence retrieval | IMPLEMENTED (infrastructure) / **NOT WIRED** to agent | P14-E bundle + reverse trace | — |
| Factor/model integration | PARTIAL | `provider_research.py` bridges provider→packet; `local_pipeline.py` builds PIT datasets; model layer thin | — |
| Candidate comparison | IMPLEMENTED (research-side) | P13-M pooled industry-relative study (78 per-symbol artifacts + 76-stock run file); P13-R policies | — |
| Risk-aware analysis | PARTIAL | `risk/engine.py` + `decision.py` gate | — |
| Recommendation policy | IMPLEMENTED (research-side, frozen registry) | `data/industry/p13r/decision_policy_registry.json` (research_only) | P13-R acceptance |
| Recommendation generation | PARTIAL | orchestrator → `RecommendationRecord`; P13-S deterministic report layer (`run_p13s_report.py`, 442 LOC, verbatim passthrough) | `test_p13s_research_agent.py` |
| Recommendation Ledger | IMPLEMENTED | `ledger.py` (81, append-only + outcome merge), `recommendation.py` (47, record/review primitives) | `test_ledger_append_only.py`, `test_ledger_metrics.py`, `test_p7_integration.py` |
| Replay / retrospective | PARTIAL | `postmortem.py`, `review.py`, `LedgerReview.close_review` | `test_postmortem.py`, `test_review.py` |

The agent layer is a **real but minimal prototype**: packet → conservative decision → ledger —
not a demo, but far from production-capable (no evidence integration, no model wiring, no
multi-symbol loop in src).

## 10. R5 Production Inventory

| Capability | Status | Files | Evidence |
|---|---|---|---|
| Scheduled execution | PARTIAL (external) | `scripts/pre_market_pipeline.py` (199), `morning_collector.py`, `mid_day_collector.py`, `fetch_latest.py` | V1-era manual/cron operation; no repo-managed scheduler |
| Data freshness monitoring | IMPLEMENTED (primitive) | `data/freshness.py`, `information/source_health.py` | `test_freshness.py`, `test_p14c_source_health.py` |
| Drift monitoring | PARTIAL | `monitoring.py` (72, drift primitives) | `test_monitoring.py` |
| Recovery | **MISSING** | — | — |
| Observability | PARTIAL | `scripts/feishu_pusher.py` (53, Feishu reports), deterministic artifacts | — |
| Deployment | **MISSING** | — | `pip install -e .` only |
| Continuous validation | PARTIAL | CI: full pytest + P14-C/D/E audits + P13-M per push | `.github/workflows/tests.yml` |
| 76-stock validation | IMPLEMENTED (local) | see §11 | — |

## 11. 76-Stock Validation Status

- **Universe exists**: `data/industry/validation_universe_76.txt` — 76 symbols (UTF-8-BOM;
  readers use `utf-8-sig` — known gotcha, handled).
- **Can it run now? YES (proven during this audit)**: smoke run of
  `scripts/run_local_industry_relative_oos.py --symbol 000001` completed in seconds, producing
  1,340 OOS predictions × 4 pooled variants (baseline / industry_5 / industry_20 / industry_5_20)
  with accuracy/Brier/LogLoss vs baseline.
- **Data dependencies present**: `data/clean/{cn_stock_daily,cn_index_daily}` (71 MB) +
  `data/industry/sw_official_sw1_membership_all.csv`. No missing dependency for the P13-M-style
  study.
- **Modules already processing it**: `run_local_industry_relative_oos.py`,
  `verify_p13m_pooled_single.py`, `profile_p13m_pooled.py`, `run_p13o/p/q/r/s_analysis.py`,
  `run_p13u_gate.py`.
- **Full-run artifacts already on disk**: 78 per-symbol `p13m_*.txt` + `p13m_76stock_real_run.txt`
  + complete `data/industry/p13o/` audit (16 files incl. `oos_predictions_76.json`).
- **What would prevent a *complete new* validation round**: nothing technical for the P13-M-style
  OOS study; for *holdout* evaluation the virgin zone has only 2 trading days (P13-T STOPPED
  until ≥20 days accumulate). Missing symbols on virgin dates (000004/000016) are reported, not
  dropped.
- **Leakage/PIT risk**: managed (per-phase PIT audits, P13-U gate, discovery/validation split).
  **Smoke-suitable now: YES.**

## 12. Existing Reusable Components

| R | Component | Location | Status | Reusable for | Missing |
|---|---|---|---|---|---|
| R1 | 8-factor engine + normalization/decorrelation | `factors/__init__.py` | IMPLEMENTED | factor layer of the agent loop | duplicate copy in `factors.py` (pick one) |
| R1 | PIT factor/label dataset builder | `local_pipeline.py` | IMPLEMENTED | training/eval datasets | wiring to agent |
| R1 | Pooled industry-relative context (~32× optimized) | `industry_relative.py` | IMPLEMENTED | candidate comparison | — |
| R1 | Fitted calibrators + 94,760-row OOS baseline | `data/industry/p13q/`, `p13o/oos_predictions_76.json` | IMPLEMENTED (artifacts) | calibrated probability in packets | a src-side apply-path (artifacts are script-side) |
| R1 | Market regime classifier | `regime.py` | IMPLEMENTED | regime input to packet | — |
| R2 | OOS/leakage/walk-forward primitives + P13-O audit pipeline | `oos.py`, `leakage.py`, `validation.py`, `scripts/run_p13o_analysis.py` | IMPLEMENTED | continuous validation runner | scheduler |
| R2 | Virgin-holdout integrity gate | `scripts/run_p13u_gate.py` | IMPLEMENTED | holdout protection | — |
| R3 | Complete P14 information/evidence stack | `information/*` | IMPLEMENTED (fixture-bound) | evidence-backed packets once a real source exists | real source adapters |
| R3 | Industry importers (3 sources) + downloader | `scripts/import_*.py`, `download_cn_stock_history.py` | IMPLEMENTED | first real P14-B adapter material | adapter-contract glue |
| R3 | Operational collectors (sentiment/macro/overseas) | `scripts/xueqiu_sentiment.py`, `macro_event_monitor.py`, `global_liquidity_radar.py` | PARTIAL (standalone) | future adapters | PIT/evidence integration |
| R4 | ResearchOrchestrator + packet | `agent/orchestrator.py` | PARTIAL | the agent core | evidence/model wiring |
| R4 | Recommendation ledger + review | `ledger.py`, `recommendation.py`, `postmortem.py`, `review.py` | IMPLEMENTED (primitives) | full loop | agent→ledger wiring exists in tests only |
| R4 | Deterministic report layer | `scripts/run_p13s_report.py` | IMPLEMENTED (script-side) | agent reporting | src-side extraction if desired |
| R5 | Drift/freshness/health primitives + Feishu push | `monitoring.py`, `source_health.py`, `feishu_pusher.py` | PARTIAL | hardening | scheduler/recovery/deploy |

## 13. Missing Critical Capabilities

1. **Real source adapters for the P14 information layer** (currently fixture-only) — the one gap
   that keeps R3 content-poor.
2. **Agent ↔ P14 wiring**: no code path turns an as_of into (query → evidence bundle → packet
   section). Today the agent reads provider/factor data only.
3. **Model apply-path in src**: calibrated probabilities exist as research artifacts; no src
   module applies a calibrator to a live decision date (research_only boundary respected).
4. **A product decision on recommendation policy**: P13-R proved no studied policy beats
   hold-all; the first usable agent must be research/paper-test-postured (the orchestrator's
   rule already is).
5. Scheduler / recovery / deployment (R5).

## 14. Dead Ends / Overengineering Candidates (report only; nothing deleted)

1. **Duplicated factor implementations**: `factors.py` and `factors/__init__.py` define the same
   8 factor functions — drift risk (duplicated semantics).
2. **Three calibration surfaces**: `model/calibration.py` (16 LOC), `calibration.py` (62),
   `scripts/run_p13q_analysis.py` (639) — only the last is research-authoritative.
3. **Primitive stubs beside the real machinery**: `backtest/walk_forward.py` (14 LOC) and
   `validation.py` (46 LOC) coexist with the P13-O validation pipeline that actually validated
   the factors (scripts-side).
4. **`data/pit/` empty directory** while `pit_store.py` exists (runtime store lives under
   `data/clean/`) — stale layout artifact.
5. **docs/progress/P0…P12** historical phase docs — obsolete phase bookkeeping (keep as history).
6. **agent-contract.md** documents substantially more than the 53-line orchestrator implements
   (documented ambition ≫ implementation — classify the doc as design, not status).
7. **Redundant test surface**: both `factors.py` and `factors/__init__.py` paths exercised by
   tests, cementing the duplication.

## 15. Product Completion Gap

Chain status for "first usable Research/Recommendation Agent" (as_of → info → evidence →
factors → regime → probability/risk → validated logic → agent → candidates → recommendation →
ledger → replay):

| Link | State | Gap |
|---|---|---|
| as_of → visible information | ✓ (P14-D; real data via legacy path) | bridge P14 query to real store |
| → evidence | ✓ (P14-E) | wire into packet |
| → factors | ✓ (8 factors + pooled context) | — |
| → regime | ✓ (`regime.py`) | — |
| → probability / risk | PARTIAL | calibrated apply-path + risk gate wiring |
| → validated research logic | PARTIAL | P13-R: no policy beat hold-all → posture decision (research/paper-test) |
| → Agent organizes evidence | PARTIAL | packet lacks evidence section from P14-E |
| → candidate analysis | PARTIAL | single-symbol path proven (smoke); multi-symbol loop is script-side |
| → recommendation | PARTIAL | conservative rule exists (NO_ACTION/PAPER_TEST/RESEARCH only) |
| → Recommendation Ledger | ✓ | — |
| → replay / retrospective | PARTIAL | postmortem primitives present |

**Bottom line**: ~70% of the loop's components exist and work in isolation; the missing 30% is
almost entirely **wiring** (3 integration points), not new quant capability.

## 16. Compressed Roadmap

- **Completed**: R0 foundation (dual PIT-safe data paths, authority chain), R1 factors + research
  artifacts (calibration/policies/regime validated on 76 stocks), R2 research validation
  (OOS/leakage/stability; holdout protected), R3 infrastructure, R4 primitives (packet/ledger),
  R5 monitoring primitives.
- **Critical path** (evidence-based, decision outside this task): real source adapter →
  evidence-backed packet wiring → calibrated-model apply-path → end-to-end single-symbol loop →
  76-stock smoke loop.
- **Important but deferrable**: walk-forward/backtest deepening, stress testing, real
  news/sentiment adapters, scheduler/recovery/deployment.
- **Research optional**: new factors, sentiment integration into evidence, macro events as
  evidence class.
- **Stopped / Protected**: P13-T (STOPPED), P13-U virgin zone (PROTECTED).
- **Do Not Touch**: P14-D/E semantics + frozen contracts + golden/harness; holdout boundary;
  accepted research registries.

## 17. Shortest Credible Critical Path

1. **One real source adapter**: local historical store (`data/clean/cn_stock_daily`) as the first
   P14-B `SourceAdapter` (reuse `adapters.py` contract + fixture adapters as templates + the
   importers/downloader). Effect: the entire accepted P14 chain runs on real data.
2. **Evidence-backed packet**: extend `ResearchOrchestrator` with a build path
   as_of → `run_query` → `create_bundle` → packet.evidence/exclusions (all machinery already
   accepted and tested).
3. **Calibrated apply-path**: a src-side function applying the fitted P13-Q calibrator to a
   decision-date probability (research-only dates < virgin_start, enforced by
   `assert_research_zone`).
4. **End-to-end loop for one symbol** → ledger append → postmortem replay; then 76-stock smoke
   (the runner already exists and is proven).

No new architecture required; every step composes existing, independently accepted components.

## 18. Recommended Next Task Candidates

### Candidate 1 — R3-A: First real source adapter (local historical store → P14-B)
- **Objective**: admit `cn_stock_daily` as a real `SourceAdapter` into the P14-B RawStore with
  durable audit + golden equivalence vs the legacy provider path.
- **Why it matters**: converts the fixture-bound accepted information layer to real data; unlocks
  every downstream evidence capability.
- **Reusable**: `adapters.py` contract, `adapters_fixture.py` (template), `local_store.py`,
  `download_cn_stock_history.py`.
- **Missing**: adapter implementation + equivalence golden + tests.
- **Risk**: low-medium. **Dependencies**: none. **Acceptance outline**: adapter contract tests,
  byte-identical double-ingest, mutation/duplicate semantics, exact-head CI, independent review.

### Candidate 2 — R4-A: Evidence-backed research packet + ledger loop
- **Objective**: wire `ResearchOrchestrator` to P14-D `run_query` + P14-E `create_bundle`
  (evidence/exclusions into the packet), and the calibrated apply-path (P13-Q) for
  research-zone dates; append `RecommendationRecord` to the ledger; replay via postmortem.
- **Why it matters**: this IS the first usable agent loop.
- **Reusable**: orchestrator, ledger, P14-D/E, calibrator artifacts, boundary guard.
- **Missing**: the wiring + tests (single-symbol E2E).
- **Risk**: medium (must respect research boundary; conservative action set).
- **Dependencies**: ideally after Candidate 1 (else fixture-bound demo). **Acceptance outline**:
  E2E test as_of→packet→ledger→replay; boundary fail-fast tests; determinism; exact-head CI.

### Candidate 3 — R2-A: Repeatable 76-stock validation runner
- **Objective**: script-ize the proven smoke run into a deterministic universe-wide validation
  round (freshness-checked inputs, deterministic artifacts + manifest, double-run identical).
- **Why it matters**: product-grade regression for every future change; already 90% exists.
- **Reusable**: `run_local_industry_relative_oos.py`, `verify_p13m_pooled_single.py`,
  membership/universe data.
- **Missing**: orchestration + manifest + CI wiring.
- **Risk**: low. **Dependencies**: none. **Acceptance outline**: 76/76 coverage report,
  deterministic double-run, boundary guard assertions, exact-head CI.

## 19. Risks / Blockers

1. **GitHub channel instability** — pushes routinely need multi-attempt retries (observed
   throughout 2026-10-04); plan for patience, never force-push; rebase onto remote acceptance
   records when collisions occur (precedent: `69cfe2a` integration).
2. **No real external adapters** — R3 content is the product's thinnest layer.
3. **P13-R negative result** — no policy beat hold-all; product expectations must remain
   research/paper-test until a validated edge exists.
4. **Virgin zone too short** — holdout evaluation blocked until ≥20 trading days accumulate
   (P13-T STOPPED).
5. **PROJECT_STATUS drift** — P14-E implementation acceptance asserted by the owner but not yet
   recorded in-repo (§4).
6. **Two-world architecture** — if R3-A/R4-A are not done, the P14 layer risks becoming an
   unused (fixture-bound) monument next to the live research path.

## 20. Evidence

- HEAD `4ff243c66b1906a4b0a8ddbfc082413b9b9f893f`; clean tree; origin/main synced; 569 commits.
- Full pytest **583 passed / 2 warnings / 0 failed** (this audit, local); P14-C audit exit 0
  (61/61/61); P14-D audit exit 0; P14-E audit exit 0 (17/17 + 26/26 golden); P13-M regression
  3 passed.
- Exact-head CI: run `37189305728` (HEAD `d100d0197744671a83de03af1cc2580ae85e4bd9`) and run
  `37190466113` (HEAD `4ff243c…`), both completed/success, all steps green.
- 76-stock smoke run executed during this audit: `run_local_industry_relative_oos.py --symbol
  000001` → 1,340 OOS predictions × 4 variants (see §11).
- Inventory counts: src 7,532 LOC (~100 files); scripts 15,118 LOC (~55 files); tests 10,353 LOC
  (86 files); docs 40+ files incl. 13 contracts; `.github/workflows/tests.yml` (pytest + p13m jobs).
- Key artifacts: `data/industry/p13o/oos_predictions_76.json` (94,760 rows),
  `p13q/` 13 files, `p13r/decision_policy_registry.json`, `p13s/` reports+schema,
  78 `p13m_*.txt` + `p13m_76stock_real_run.txt`.

*Audit-only task: no production, contract, or boundary file was modified by this audit.*
