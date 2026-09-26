from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("ASTOCK_DATA_DIR", "data"))
    workspace_dir: Path = Path(os.getenv("ASTOCK_WORKSPACE_DIR", "workspace"))
    min_quality_for_decision: float = 0.75
    horizons: tuple[int, ...] = (1, 3, 5, 10)

settings = Settings()
