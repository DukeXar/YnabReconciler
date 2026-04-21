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
        csv_rows = [_tx("csv", 2, 9.49, "Ryman Stationery")]
        pdf_rows = [_tx("pdf", 2, 9.49, "1167 Clapham J London")]

        missing_in_csv, missing_in_pdf, _ = find_missing(csv_rows, pdf_rows)

        self.assertEqual(missing_in_csv, [])
        self.assertEqual(missing_in_pdf, [])

    def test_all_transactions_match_without_missing(self) -> None:
        csv_rows = [
            _tx("csv", 28, 9.20, "Waitrose"),
            _tx("csv", 29, 7.55, "Transport for London"),
        ]
        pdf_rows = [
            _tx("pdf", 28, 9.20, "Waitrose"),
            _tx("pdf", 29, 7.55, "Transport for London"),
        ]

        missing_in_csv, missing_in_pdf, window = find_missing(csv_rows, pdf_rows)

        self.assertEqual(window, (date(2026, 1, 28), date(2026, 1, 29)))
        self.assertEqual(missing_in_csv, [])
        self.assertEqual(missing_in_pdf, [])

    def test_find_missing_bidirectional_in_overlap(self) -> None:
        csv_rows = [
            _tx("csv", 28, 9.2, "Waitrose"),
            _tx("csv", 29, 7.55, "Transport for London"),
        ]
        pdf_rows = [
            _tx("pdf", 28, 9.2, "Waitrose Clapham"),
            _tx("pdf", 29, 6.4, "TFL TRAVEL CHARGE"),
        ]
        config = MatchConfig(merchant_threshold=0.3)

        missing_in_csv, missing_in_pdf, window = find_missing(
            csv_rows, pdf_rows, config
        )

        self.assertEqual(window, (date(2026, 1, 28), date(2026, 1, 29)))
        self.assertEqual(len(missing_in_csv), 1)
        self.assertEqual(len(missing_in_pdf), 1)
        self.assertEqual(missing_in_csv[0].amount, 6.4)
        self.assertEqual(missing_in_pdf[0].amount, 7.55)

    def test_amount_tolerance_enables_matching(self) -> None:
        csv_rows = [_tx("csv", 28, 12.34, "Cafe Nero")]
        pdf_rows = [_tx("pdf", 28, 12.35, "Cafe Nero")]

        strict_cfg = MatchConfig(amount_tolerance=0.001, merchant_threshold=1.0)
        loose_cfg = MatchConfig(amount_tolerance=0.02, merchant_threshold=1.0)

        missing_in_csv_strict, missing_in_pdf_strict, _ = find_missing(
            csv_rows, pdf_rows, strict_cfg
        )
        missing_in_csv_loose, missing_in_pdf_loose, _ = find_missing(
            csv_rows, pdf_rows, loose_cfg
        )

        self.assertEqual(len(missing_in_csv_strict), 1)
        self.assertEqual(len(missing_in_pdf_strict), 1)
        self.assertEqual(missing_in_csv_loose, [])
        self.assertEqual(missing_in_pdf_loose, [])

    def test_duplicate_candidates_only_match_once(self) -> None:
        csv_rows = [_tx("csv", 28, 15.00, "Trainline")]
        pdf_rows = [
            _tx("pdf", 28, 15.00, "Trainline"),
            _tx("pdf", 28, 15.00, "Trainline"),
        ]

        missing_in_csv, missing_in_pdf, _ = find_missing(csv_rows, pdf_rows)

        self.assertEqual(missing_in_pdf, [])
        self.assertEqual(len(missing_in_csv), 1)
        self.assertEqual(missing_in_csv[0].merchant, "Trainline")

    def test_can_skip_merchant_check_via_config(self) -> None:
        csv_rows = [_tx("csv", 28, 22.24, "B Century")]
        pdf_rows = [_tx("pdf", 28, 22.24, "Some Other Merchant")]

        with_merchant = MatchConfig(check_merchant=True, merchant_threshold=0.95)
        without_merchant = MatchConfig(check_merchant=False, merchant_threshold=0.95)

        missing_in_csv_strict, missing_in_pdf_strict, _ = find_missing(
            csv_rows, pdf_rows, with_merchant
        )
        missing_in_csv_skip, missing_in_pdf_skip, _ = find_missing(
            csv_rows, pdf_rows, without_merchant
        )

        self.assertEqual(len(missing_in_csv_strict), 1)
        self.assertEqual(len(missing_in_pdf_strict), 1)
        self.assertEqual(missing_in_csv_skip, [])
        self.assertEqual(missing_in_pdf_skip, [])


if __name__ == "__main__":
    unittest.main()
