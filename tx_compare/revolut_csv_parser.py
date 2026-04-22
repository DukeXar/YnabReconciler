from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from tx_compare.models import Transaction
from tx_compare.normalize import normalize_merchant


def _parse_money(value: str) -> float:
    cleaned = value.replace("£", "").replace(",", "").strip()
    if not cleaned:
        return 0.0
    return float(cleaned)


def parse_revolut_csv_transactions(csv_path: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            state = (row.get("State") or "").strip().upper()
            if state != "COMPLETED":
                continue

            amount = _parse_money(row.get("Amount", ""))
            fee = _parse_money(row.get("Fee", ""))
            normalized_amount = round((-amount) + fee, 2)
            if normalized_amount == 0:
                continue

            started = (row.get("Started Date") or "").strip()
            tx_date = datetime.strptime(started[:10], "%Y-%m-%d").date()

            merchant_raw = (row.get("Description") or "").strip()
            transactions.append(
                Transaction(
                    source="revolut_csv",
                    tx_date=tx_date,
                    amount=normalized_amount,
                    merchant_raw=merchant_raw,
                    merchant_norm=normalize_merchant(merchant_raw),
                    raw_line=str(row),
                )
            )
    return transactions
