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


def parse_csv_transactions(csv_path: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            outflow = _parse_money(row.get("Outflow", ""))
            inflow = _parse_money(row.get("Inflow", ""))
            amount = round(outflow - inflow, 2)
            if amount == 0:
                continue

            merchant_raw = (row.get("Payee") or "").strip()
            tx_date = datetime.strptime(
                (row.get("Date") or "").strip(), "%d.%m.%Y"
            ).date()
            transactions.append(
                Transaction(
                    source="csv",
                    tx_date=tx_date,
                    amount=amount,
                    merchant_raw=merchant_raw,
                    merchant_norm=normalize_merchant(merchant_raw),
                    raw_line=str(row),
                )
            )
    return transactions
