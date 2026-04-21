from __future__ import annotations

import unittest
from datetime import date

from tx_compare.__main__ import build_parser, dedupe_transactions
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

    def test_deduplicate_transactions_by_date_amount_merchant_norm(self) -> None:
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

        deduped = dedupe_transactions([first, duplicate, distinct])

        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0], first)
        self.assertEqual(deduped[1], distinct)


if __name__ == "__main__":
    unittest.main()
