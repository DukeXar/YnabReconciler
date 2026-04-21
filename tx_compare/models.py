from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Transaction:
    source: str
    tx_date: date
    amount: float
    merchant_raw: str
    merchant_norm: str
    raw_line: str


@dataclass(frozen=True)
class MissingTransaction:
    direction: str
    tx_date: date
    amount: float
    merchant: str
    raw_line: str
    reason: str
