Research Report
===============

Report ID: 1dffbcabc4b7f4d0
Schema Version: p13s-report-1

Recommendation Summary
----------------------
Symbol: 000002
Decision Time: 2025-01-02T16:00:00+08:00
Policy: hold_all

Probability / Calibration
-------------------------
Raw Probability: 42.7640%
Calibrated Probability: 42.7640%
Calibration Method: none

Expected Return
---------------
Expected Return: -0.3211%
Cost-adjusted Expected Return: -0.4211%
Cost Scenario: low

Risk
----
Risk Score: 0.020514
Risk Flags: (none recorded by P13-R)

Market Regime
-------------
Market Regime: BEAR

Selection Reason
----------------
Selection Reason: baseline_hold_all

Data Freshness
--------------
Decision Time: 2025-01-02T16:00:00+08:00
Data Available Time: 2025-01-02T16:00:00+08:00
Freshness Status: fresh

Uncertainty
-----------
- low_confidence

Evidence
--------
- raw_probability: report field 'raw_probability' <- packet field 'raw_probability' <- p13q_calibration
- calibrated_probability: report field 'calibrated_probability' <- packet field 'calibrated_probability' <- p13q_calibration
- expected_return: report field 'expected_return' <- packet field 'expected_return' <- p13r_expected_return_model
- cost_adjusted_expected_return: report field 'cost_adjusted_expected_return' <- packet field 'cost_adjusted_expected_return' <- p13r_expected_return_model
- risk_score: report field 'risk_score' <- packet field 'risk_score' <- p13r_risk_features
- risk_flags: report field 'risk_flags' <- packet field 'risk_flags' <- p13r_risk_features
- market_regime: report field 'market_regime' <- packet field 'market_regime' <- p13o_regime_labeler
- selection_reason: report field 'selection_reason' <- packet field 'selection_reason' <- p13r_policy_registry
- data_available_time: report field 'data_available_time' <- packet field 'data_available_time' <- p13r_pit_audit

Research Status
---------------
research_only = true
This artifact documents a research decision layer for human review; it is not an order and not an execution instruction.
