from dataclasses import dataclass

@dataclass(frozen=True)
class QualityReport:
    freshness_minutes: float
    missing_ratio: float
    source_agreement: float
    fallback_ratio: float
    duplicate_ratio: float = 0.0
    timestamp_valid_ratio: float = 1.0

    @property
    def score(self) -> float:
        freshness=max(0.0,min(1.0,1.0-self.freshness_minutes/30.0))
        missing=1.0-min(1.0,self.missing_ratio)
        duplicate=1.0-min(1.0,self.duplicate_ratio)
        timestamp=max(0.0,min(1.0,self.timestamp_valid_ratio))
        return round(0.25*freshness+0.20*missing+0.20*self.source_agreement+
                     0.15*(1-self.fallback_ratio)+0.10*duplicate+0.10*timestamp,4)
