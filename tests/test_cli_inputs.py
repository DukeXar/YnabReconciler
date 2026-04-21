from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from tx_compare.__main__ import build_parser, load_csv_transactions
from tx_compare.models import Transaction


class CLIInputTests(unittest.TestCase):
    def test_parser_accepts_multiple_csv_and_pdf_paths(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "compare",
                "--csv",
                "a.csv",
                "b.csv",
                "--pdf",
                "one.pdf",
                "two.pdf",
            ]
        )

        self.assertEqual([str(path) for path in args.csv], ["a.csv", "b.csv"])
        self.assertEqual([str(path) for path in args.pdf], ["one.pdf", "two.pdf"])
        self.assertFalse(args.merchant_check)

    def test_parser_can_enable_merchant_check(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["compare", "--csv", "a.csv", "--pdf", "one.pdf", "--merchant-check"]
        )

        self.assertTrue(args.merchant_check)

    def test_load_csv_transactions_keeps_overlapping_rows(self) -> None:
        first = Transaction(
            source="csv",
            tx_date=date(2026, 1, 1),
            amount=12.34,
            merchant_raw="Cafe Nero",
            merchant_norm="caffe nero",
            raw_line="line 1",
        )
        duplicate = Transaction(
            source="csv",
            tx_date=date(2026, 1, 1),
            amount=12.34,
            merchant_raw="Caffe Nero London",
            merchant_norm="caffe nero",
            raw_line="line 2",
        )
        distinct = Transaction(
            source="csv",
            tx_date=date(2026, 1, 2),
            amount=12.34,
            merchant_raw="Caffe Nero London",
            merchant_norm="caffe nero",
            raw_line="line 3",
        )

        with patch(
            "tx_compare.__main__.parse_csv_transactions",
            side_effect=[[first, duplicate], [distinct]],
        ):
            rows = load_csv_transactions([Path("a.csv"), Path("b.csv")])

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], first)
        self.assertEqual(rows[1], duplicate)
        self.assertEqual(rows[2], distinct)


if __name__ == "__main__":
    unittest.main()
