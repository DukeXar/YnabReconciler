from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tx_compare.amex_csv_parser import parse_amex_csv_transactions


class AmexCSVParserTests(unittest.TestCase):
    def test_parser_extracts_rows_with_signs(self) -> None:
        content = """Date,Description,Amount
21/04/2026,MINERVASVIRTUALACADEMY  LONDON,137.50
17/04/2026,IKEA VALLEY PARK CROYDO -,-349.00
11/04/2026,"JD Wetherspoons PLC     Watford,",17.55
"""
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "activity.csv"
            csv_path.write_text(content, encoding="utf-8")

            rows = parse_amex_csv_transactions(csv_path)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].amount, 137.50)
        self.assertEqual(rows[1].amount, -349.00)
        self.assertEqual(rows[2].merchant_raw, "JD Wetherspoons PLC     Watford,")

    def test_parser_skips_zero_amount_rows(self) -> None:
        content = """Date,Description,Amount
21/04/2026,Some Merchant,0.00
20/04/2026,Another Merchant,12.34
"""
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "activity.csv"
            csv_path.write_text(content, encoding="utf-8")

            rows = parse_amex_csv_transactions(csv_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount, 12.34)


if __name__ == "__main__":
    unittest.main()
