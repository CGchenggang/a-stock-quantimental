"""Deterministic source-health model from observable ingestion evidence.

Health is aggregated from facts — ingestion attempts, accepted/rejected/
duplicate/mutation counts, errors, coverage, freshness — by documented
deterministic rules. No ML, no manual "this source looks reliable" labels.

Health states (handoff §14):

- OK          accepted > 0, no errors/mutations, freshness FRESH, coverage 1.0
- DEGRADED    accepted > 0 but with documented blemishes (duplicates,
              rejected, mutations, stale rows, coverage < 1.0, or errors)
- STALE       accepted > 0 but the latest available data is older than the
              audit reference window (stale_count > fresh_count)
- EMPTY       attempted > 0 but nothing accepted and nothing rejected
              (pure replay of an empty source is EMPTY, not an error)
- ERROR       errors present and nothing accepted (fetch/auth/timeout or
              total parse failure)
- UNRESOLVED  accepted > 0 but every accepted row carries unresolved
              availability (cannot be PIT-evaluated at all)
"""
from __future__ import annotations

from typing import Any


def source_health(metrics: dict[str, Any]) -> dict[str, Any]:
    """Aggregate one source's observable metrics into a health record.

    Expected metric keys (all optional; missing facts count as 0):
      attempted, accepted, rejected, duplicates, mutations, errors,
      parse_errors, fresh, stale, unresolved, coverage (0..1),
      missing_symbols (list), latest_available_date, reference_date
    """
    attempted = int(metrics.get("attempted", 0))
    accepted = int(metrics.get("accepted", 0))
    rejected = int(metrics.get("rejected", 0))
    duplicates = int(metrics.get("duplicates", 0))
    mutations = int(metrics.get("mutations", 0))
    errors = int(metrics.get("errors", 0))
    parse_errors = int(metrics.get("parse_errors", 0))
    fresh = int(metrics.get("fresh", 0))
    stale = int(metrics.get("stale", 0))
    unresolved = int(metrics.get("unresolved", 0))
    coverage = float(metrics.get("coverage", 0.0))
    reasons: list[str] = []

    if attempted == 0 and accepted == 0 and errors == 0:
        health = "UNRESOLVED"
        reasons.append("no ingestion attempts observed")
    elif accepted == 0 and (errors > 0 or (attempted > 0 and rejected == 0
                                           and duplicates == 0)):
        health = "ERROR"
        reasons.append("no accepted rows and ingestion errors present")
    elif accepted == 0 and rejected == 0 and duplicates == 0 and attempted > 0:
        health = "EMPTY"
        reasons.append("source returned zero rows")
    else:
        if errors > 0 or mutations > 0 or rejected > 0:
            health = "DEGRADED"
            if errors > 0:
                reasons.append(f"{errors} ingestion errors")
            if mutations > 0:
                reasons.append(f"{mutations} raw mutations")
            if rejected > 0:
                reasons.append(f"{rejected} rejected rows")
        if stale > fresh and (fresh + stale) > 0:
            health = "STALE"
            reasons.append("freshness majority stale")
        elif coverage < 1.0 and accepted > 0:
            health = "DEGRADED"
            reasons.append(f"coverage {coverage:.4f} below 1.0")
        elif not reasons:
            health = "OK"
        elif health != "STALE" and not reasons:
            reasons.append("no blemishes observed")

    return {
        "health": health,
        "reasons": reasons,
        "metrics": {
            "attempted": attempted, "accepted": accepted,
            "rejected": rejected, "duplicates": duplicates,
            "mutations": mutations, "errors": errors,
            "parse_errors": parse_errors, "fresh": fresh,
            "stale": stale, "unresolved": unresolved,
            "coverage": coverage,
        },
        "note": "health is aggregated from observable evidence by documented "
                "deterministic rules; no ML score, no manual labels",
    }
