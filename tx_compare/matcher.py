from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher

from tx_compare.models import MissingTransaction, Transaction


@dataclass(frozen=True)
class MatchConfig:
    amount_tolerance: float = 0.01
    merchant_threshold: float = 0.55
    check_merchant: bool = False


def _merchant_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()


def _match_index(
    tx: Transaction,
    candidates: list[Transaction],
    used: set[int],
    config: MatchConfig,
) -> int | None:
    best_index: int | None = None
    best_score: float = -1.0
    for idx, cand in enumerate(candidates):
        if idx in used:
            continue
        if tx.tx_date != cand.tx_date:
            continue
        if abs(tx.amount - cand.amount) > config.amount_tolerance:
            continue
        if not config.check_merchant:
            return idx
        score = _merchant_similarity(tx.merchant_norm, cand.merchant_norm)
        if score < config.merchant_threshold:
            continue
        if score > best_score:
            best_score = score
            best_index = idx
    return best_index


def overlap_window(
    left: list[Transaction], right: list[Transaction]
) -> tuple[date, date] | None:
    if not left or not right:
        return None
    start = max(min(tx.tx_date for tx in left), min(tx.tx_date for tx in right))
    end = min(max(tx.tx_date for tx in left), max(tx.tx_date for tx in right))
    if start > end:
        return None
    return start, end


def filter_in_window(
    items: list[Transaction], window: tuple[date, date] | None
) -> list[Transaction]:
    if window is None:
        return []
    start, end = window
    return [tx for tx in items if start <= tx.tx_date <= end]


def find_missing(
    ynab_transactions: list[Transaction],
    statement_transactions: list[Transaction],
    config: MatchConfig | None = None,
) -> tuple[
    list[MissingTransaction], list[MissingTransaction], tuple[date, date] | None
]:
    if config is None:
        config = MatchConfig()

    window = overlap_window(ynab_transactions, statement_transactions)
    ynab_in_window = filter_in_window(ynab_transactions, window)
    statement_in_window = filter_in_window(statement_transactions, window)

    used_statement: set[int] = set()
    missing_in_statement: list[MissingTransaction] = []

    for tx in ynab_in_window:
        idx = _match_index(tx, statement_in_window, used_statement, config)
        if idx is None:
            missing_in_statement.append(
                MissingTransaction(
                    direction="missing_in_statement",
                    tx_date=tx.tx_date,
                    amount=tx.amount,
                    merchant=tx.merchant_raw,
                    raw_line=tx.raw_line,
                    reason="no statement match on date/amount/merchant",
                )
            )
        else:
            used_statement.add(idx)

    used_ynab: set[int] = set()
    missing_in_ynab: list[MissingTransaction] = []

    for tx in statement_in_window:
        idx = _match_index(tx, ynab_in_window, used_ynab, config)
        if idx is None:
            missing_in_ynab.append(
                MissingTransaction(
                    direction="missing_in_ynab",
                    tx_date=tx.tx_date,
                    amount=tx.amount,
                    merchant=tx.merchant_raw,
                    raw_line=tx.raw_line,
                    reason="no YNAB match on date/amount/merchant",
                )
            )
        else:
            used_ynab.add(idx)

    missing_in_ynab.sort(key=lambda x: (x.tx_date, x.amount, x.merchant.lower()))
    missing_in_statement.sort(key=lambda x: (x.tx_date, x.amount, x.merchant.lower()))
    return missing_in_ynab, missing_in_statement, window
