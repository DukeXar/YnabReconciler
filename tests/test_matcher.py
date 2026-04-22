from __future__ import annotations

import unittest
from datetime import date

from tx_compare.matcher import MatchConfig, find_missing
from tx_compare.models import Transaction


def _tx(source: str, day: int, amount: float, merchant: str) -> Transaction:
    return Transaction(
        source=source,
        tx_date=date(2026, 1, day),
        amount=amount,
        merchant_raw=merchant,
        merchant_norm=merchant.lower(),
        raw_line=merchant,
    )


class MatcherTests(unittest.TestCase):
    def test_default_config_ignores_merchant_names(self) -> None:
        ynab_rows = [_tx("csv", 2, 9.49, "Ryman Stationery")]
        statement_rows = [_tx("pdf", 2, 9.49, "1167 Clapham J London")]

        missing_in_ynab, missing_in_statement, _ = find_missing(
            ynab_rows, statement_rows
        )

        self.assertEqual(missing_in_ynab, [])
        self.assertEqual(missing_in_statement, [])

    def test_all_transactions_match_without_missing(self) -> None:
        ynab_rows = [
            _tx("csv", 28, 9.20, "Waitrose"),
            _tx("csv", 29, 7.55, "Transport for London"),
        ]
        statement_rows = [
            _tx("pdf", 28, 9.20, "Waitrose"),
            _tx("pdf", 29, 7.55, "Transport for London"),
        ]

        missing_in_ynab, missing_in_statement, window = find_missing(
            ynab_rows, statement_rows
        )

        self.assertEqual(window, (date(2026, 1, 28), date(2026, 1, 29)))
        self.assertEqual(missing_in_ynab, [])
        self.assertEqual(missing_in_statement, [])

    def test_find_missing_bidirectional_in_overlap(self) -> None:
        ynab_rows = [
            _tx("csv", 28, 9.2, "Waitrose"),
            _tx("csv", 29, 7.55, "Transport for London"),
        ]
        statement_rows = [
            _tx("pdf", 28, 9.2, "Waitrose Clapham"),
            _tx("pdf", 29, 6.4, "TFL TRAVEL CHARGE"),
        ]
        config = MatchConfig(merchant_threshold=0.3)

        missing_in_ynab, missing_in_statement, window = find_missing(
            ynab_rows, statement_rows, config
        )

        self.assertEqual(window, (date(2026, 1, 28), date(2026, 1, 29)))
        self.assertEqual(len(missing_in_ynab), 1)
        self.assertEqual(len(missing_in_statement), 1)
        self.assertEqual(missing_in_ynab[0].amount, 6.4)
        self.assertEqual(missing_in_statement[0].amount, 7.55)

    def test_amount_tolerance_enables_matching(self) -> None:
        ynab_rows = [_tx("csv", 28, 12.34, "Cafe Nero")]
        statement_rows = [_tx("pdf", 28, 12.35, "Cafe Nero")]

        strict_cfg = MatchConfig(amount_tolerance=0.001, merchant_threshold=1.0)
        loose_cfg = MatchConfig(amount_tolerance=0.02, merchant_threshold=1.0)

        missing_in_ynab_strict, missing_in_statement_strict, _ = find_missing(
            ynab_rows, statement_rows, strict_cfg
        )
        missing_in_ynab_loose, missing_in_statement_loose, _ = find_missing(
            ynab_rows, statement_rows, loose_cfg
        )

        self.assertEqual(len(missing_in_ynab_strict), 1)
        self.assertEqual(len(missing_in_statement_strict), 1)
        self.assertEqual(missing_in_ynab_loose, [])
        self.assertEqual(missing_in_statement_loose, [])

    def test_duplicate_candidates_only_match_once(self) -> None:
        ynab_rows = [_tx("csv", 28, 15.00, "Trainline")]
        statement_rows = [
            _tx("pdf", 28, 15.00, "Trainline"),
            _tx("pdf", 28, 15.00, "Trainline"),
        ]

        missing_in_ynab, missing_in_statement, _ = find_missing(
            ynab_rows, statement_rows
        )

        self.assertEqual(missing_in_statement, [])
        self.assertEqual(len(missing_in_ynab), 1)
        self.assertEqual(missing_in_ynab[0].merchant, "Trainline")

    def test_can_skip_merchant_check_via_config(self) -> None:
        ynab_rows = [_tx("csv", 28, 22.24, "B Century")]
        statement_rows = [_tx("pdf", 28, 22.24, "Some Other Merchant")]

        with_merchant = MatchConfig(check_merchant=True, merchant_threshold=0.95)
        without_merchant = MatchConfig(check_merchant=False, merchant_threshold=0.95)

        missing_in_ynab_strict, missing_in_statement_strict, _ = find_missing(
            ynab_rows, statement_rows, with_merchant
        )
        missing_in_ynab_skip, missing_in_statement_skip, _ = find_missing(
            ynab_rows, statement_rows, without_merchant
        )

        self.assertEqual(len(missing_in_ynab_strict), 1)
        self.assertEqual(len(missing_in_statement_strict), 1)
        self.assertEqual(missing_in_ynab_skip, [])
        self.assertEqual(missing_in_statement_skip, [])


if __name__ == "__main__":
    unittest.main()
