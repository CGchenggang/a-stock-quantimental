"""Reusable point-in-time leakage audit helpers."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .data.providers import ProviderResult, pit_status, PitStatus

@dataclass(frozen=True)
class LeakageFinding:
    index: int
    status: PitStatus
    source: str
    available_time: str | None

@dataclass(frozen=True)
class LeakageAudit:
    decision_time: str
    total: int
    admissible: int
    findings: tuple[LeakageFinding,...]
    passed: bool
    def as_dict(self):
        return {"decision_time":self.decision_time,"total":self.total,"admissible":self.admissible,
                "passed":self.passed,"findings":[{"index":x.index,"status":x.status.value,
                "source":x.source,"available_time":x.available_time} for x in self.findings]}

def audit_provider_results(results: Iterable[ProviderResult], decision_time: str) -> LeakageAudit:
    findings=[]
    total=admissible=0
    for index,result in enumerate(results):
        total+=1
        status=pit_status(result,decision_time)
        if status is PitStatus.ADMISSIBLE: admissible+=1
        else: findings.append(LeakageFinding(index,status,result.source,result.available_time))
    return LeakageAudit(decision_time,total,admissible,tuple(findings),not findings and total>0)

def assert_no_pit_leakage(results: Iterable[ProviderResult], decision_time: str) -> LeakageAudit:
    audit=audit_provider_results(results,decision_time)
    if not audit.passed:
        statuses=", ".join(f"{x.index}:{x.status.value}" for x in audit.findings)
        raise ValueError(f"PIT leakage or inadmissible inputs detected: {statuses}")
    return audit
