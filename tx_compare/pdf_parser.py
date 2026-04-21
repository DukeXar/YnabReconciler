from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from tx_compare.models import Transaction
from tx_compare.normalize import normalize_merchant

MONTHS_SHORT = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

MONTHS_LONG = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def parse_pdf_transactions(pdf_path: Path) -> list[Transaction]:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency 'pypdf'. Install dependencies with: pip install -r requirements.txt"
        ) from exc

    reader = PdfReader(str(pdf_path))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    period = _extract_statement_period(full_text)

    transactions: list[Transaction] = []
    for page in reader.pages:
        page_text = page.extract_text(extraction_mode="layout") or ""
        transactions.extend(parse_layout_page_text(page_text, period))

    if transactions:
        return transactions
    return parse_statement_text(full_text)


def _extract_statement_period(text: str) -> tuple[date, date] | None:
    pattern = re.compile(
        r"From\s+(\d{1,2})\s*([A-Za-z]+)\s+to\s+(\d{1,2})\s*([A-Za-z]+)\s+(\d{4})"
    )
    match = pattern.search(text)
    if not match:
        return None

    start_day, start_mon, end_day, end_mon, end_year = match.groups()
    end_year_i = int(end_year)
    start_month_i = MONTHS_LONG[start_mon]
    end_month_i = MONTHS_LONG[end_mon]
    start_year_i = end_year_i if start_month_i <= end_month_i else end_year_i - 1

    return (
        date(start_year_i, start_month_i, int(start_day)),
        date(end_year_i, end_month_i, int(end_day)),
    )


def _infer_year_for_tx(
    month: int, period_start: date | None, period_end: date | None
) -> int:
    if not period_start or not period_end:
        return period_end.year if period_end else date.today().year
    if period_start.year == period_end.year:
        return period_end.year
    if month >= period_start.month:
        return period_start.year
    return period_end.year


def parse_statement_text(text: str) -> list[Transaction]:
    period = _extract_statement_period(text)
    period_start = period[0] if period else None
    period_end = period[1] if period else None

    # Example row in extracted text:
    # Jan 31 Jan 31 DELIVEROO LONDON 32.65
    row_pattern = re.compile(
        r"\b([A-Z][a-z]{2})\s+(\d{1,2})\s+[A-Z][a-z]{2}\s+\d{1,2}\s+"
        r"(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})\b"
    )

    blacklist = {
        "payment received",
        "membership fee",
        "total new spend transactions",
        "total of other account transactions",
    }

    transactions: list[Transaction] = []
    for match in row_pattern.finditer(text):
        mon_name, day_str, merchant_raw, amount_str = match.groups()
        merchant_raw = " ".join(merchant_raw.split())
        merchant_low = merchant_raw.lower()
        if any(entry in merchant_low for entry in blacklist):
            continue

        month = MONTHS_SHORT[mon_name]
        year = _infer_year_for_tx(month, period_start, period_end)
        tx_date = date(year, month, int(day_str))
        amount = round(float(amount_str.replace(",", "")), 2)

        transactions.append(
            Transaction(
                source="pdf",
                tx_date=tx_date,
                amount=amount,
                merchant_raw=merchant_raw,
                merchant_norm=normalize_merchant(merchant_raw),
                raw_line=match.group(0),
            )
        )

    return transactions


def parse_layout_page_text(
    page_text: str, period: tuple[date, date] | None
) -> list[Transaction]:
    period_start = period[0] if period else None
    period_end = period[1] if period else None

    row_pattern = re.compile(
        r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*(\d{1,2})\s+"
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{1,2}\s+"
        r"(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})$"
    )

    blacklist = {
        "payment received",
        "statement of account",
        "transaction date",
        "total new spend transactions",
    }

    lines = [" ".join(line.split()) for line in page_text.splitlines() if line.strip()]
    rows: list[Transaction] = []

    index = 0
    while index < len(lines):
        line = lines[index]
        match = row_pattern.match(line)
        if not match:
            index += 1
            continue

        tx_mon, tx_day, _proc_mon, merchant_raw, amount_str = match.groups()
        merchant_low = merchant_raw.lower()
        if any(item in merchant_low for item in blacklist):
            index += 1
            continue

        amount = float(amount_str.replace(",", ""))
        if index + 1 < len(lines) and lines[index + 1] == "CR":
            amount = -amount
            index += 1

        month = MONTHS_SHORT[tx_mon]
        year = _infer_year_for_tx(month, period_start, period_end)
        tx_date = date(year, month, int(tx_day))

        rows.append(
            Transaction(
                source="pdf",
                tx_date=tx_date,
                amount=round(amount, 2),
                merchant_raw=merchant_raw,
                merchant_norm=normalize_merchant(merchant_raw),
                raw_line=line,
            )
        )
        index += 1

    return rows
