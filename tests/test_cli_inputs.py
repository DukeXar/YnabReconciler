from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from tx_compare.__main__ import build_parser, load_ynab_transactions
from tx_compare.models import Transaction


class CLIInputTests(unittest.TestCase):
    def test_parser_accepts_multiple_ynab_and_amex_paths(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "compare",
                "--ynab",
                "a.csv",
                "b.csv",
                "--amex-pdf",
                "one.pdf",
                "two.pdf",
            ]
        )

        self.assertEqual([str(path) for path in args.ynab], ["a.csv", "b.csv"])
        self.assertEqual([str(path) for path in args.amex_pdf], ["one.pdf", "two.pdf"])
        self.assertIsNone(args.amex_csv)
        self.assertIsNone(args.revo_csv)
        self.assertFalse(args.merchant_check)

    def test_parser_accepts_multiple_ynab_and_amex_csv_paths(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "compare",
                "--ynab",
                "a.csv",
                "b.csv",
                "--amex-csv",
                "one.csv",
                "two.csv",
            ]
        )

        self.assertEqual([str(path) for path in args.ynab], ["a.csv", "b.csv"])
        self.assertEqual([str(path) for path in args.amex_csv], ["one.csv", "two.csv"])
        self.assertIsNone(args.amex_pdf)
        self.assertIsNone(args.revo_csv)

    def test_parser_accepts_multiple_ynab_and_revolut_csv_paths(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "compare",
                "--ynab",
                "a.csv",
                "b.csv",
                "--revo-csv",
                "one.csv",
                "two.csv",
            ]
        )

        self.assertEqual([str(path) for path in args.ynab], ["a.csv", "b.csv"])
        self.assertEqual([str(path) for path in args.revo_csv], ["one.csv", "two.csv"])
        self.assertIsNone(args.amex_pdf)
        self.assertIsNone(args.amex_csv)

    def test_parser_rejects_multiple_statement_types(self) -> None:
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "compare",
                    "--ynab",
                    "a.csv",
                    "--amex-csv",
                    "one.csv",
                    "--amex-pdf",
                    "one.pdf",
                ]
            )

        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "compare",
                    "--ynab",
                    "a.csv",
                    "--amex-csv",
                    "one.csv",
                    "--revo-csv",
                    "one.csv",
                ]
            )

    def test_parser_can_enable_merchant_check(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "compare",
                "--ynab",
                "a.csv",
                "--amex-pdf",
                "one.pdf",
                "--merchant-check",
            ]
        )

        self.assertTrue(args.merchant_check)

    def test_load_ynab_transactions_keeps_overlapping_rows(self) -> None:
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
            "tx_compare.__main__.parse_ynab_transactions",
            side_effect=[[first, duplicate], [distinct]],
        ):
            rows = load_ynab_transactions([Path("a.csv"), Path("b.csv")])

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], first)
        self.assertEqual(rows[1], duplicate)
        self.assertEqual(rows[2], distinct)


if __name__ == "__main__":
    unittest.main()
