from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class EtlStats:
    extracted: int
    valid: int
    rejected: int
    loaded_by_table: Dict[str, int]


@dataclass(frozen=True)
class PurchaseModel:
    model: Any
    feature_columns: tuple
