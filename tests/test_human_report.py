from __future__ import annotations

import unittest
from datetime import date

from tx_compare.__main__ import build_human_report
from tx_compare.models import MissingTransaction


class HumanReportTests(unittest.TestCase):
    def test_build_human_report_includes_required_columns(self) -> None:
        missing_in_ynab = [
            MissingTransaction(
                direction="missing_in_ynab",
                tx_date=date(2026, 1, 26),
                amount=9.74,
                merchant="PRET A MANGER London",
                raw_line="x",
                reason="r",
            )
        ]
        missing_in_statement = [
            MissingTransaction(
                direction="missing_in_statement",
                tx_date=date(2026, 1, 27),
                amount=44.27,
                merchant="Patty & Bun",
                raw_line="y",
                reason="r",
            )
        ]

        report = build_human_report(missing_in_ynab, missing_in_statement)

        self.assertIn("Date", report)
        self.assertIn("Amount", report)
        self.assertIn("Merchant", report)
        self.assertIn("Missing In", report)
        self.assertIn("YNAB", report)
        self.assertIn("STATEMENT", report)


if __name__ == "__main__":
    unittest.main()
