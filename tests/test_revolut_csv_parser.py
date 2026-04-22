from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tx_compare.revolut_csv_parser import parse_revolut_csv_transactions


class RevolutCSVParserTests(unittest.TestCase):
    def test_parser_maps_amount_signs_and_fee(self) -> None:
        content = """Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Card Payment,Current,2026-04-21 20:51:25,2026-04-22 04:06:48,Clr Limpsfieldchartgol,-20.00,0.00,GBP,COMPLETED,775.38
Deposit,Current,2026-04-06 19:38:08,2026-04-06 19:38:29,Open banking deposit,1500.00,0.00,GBP,COMPLETED,2537.82
Charge,Current,2026-03-27 01:39:01,2026-03-27 01:39:01,Metal plan fee,0.00,14.99,GBP,COMPLETED,173.46
"""
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "account-statement.csv"
            csv_path.write_text(content, encoding="utf-8")

            rows = parse_revolut_csv_transactions(csv_path)

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].amount, 20.00)
        self.assertEqual(rows[1].amount, -1500.00)
        self.assertEqual(rows[2].amount, 14.99)

    def test_parser_skips_non_completed_and_zero_net_rows(self) -> None:
        content = """Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
Card Payment,Current,2025-10-21 22:08:38,,Sata Internacional,-116.34,0.00,GBP,REVERTED,
Transfer,Current,2026-04-03 05:19:51,2026-04-03 05:19:51,Transfer to MAKSIM KLAUTSAN,5.00,5.00,GBP,COMPLETED,1037.82
Card Payment,Current,2026-04-21 20:51:25,2026-04-22 04:06:48,Clr Limpsfieldchartgol,-20.00,0.00,GBP,COMPLETED,775.38
"""
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "account-statement.csv"
            csv_path.write_text(content, encoding="utf-8")

            rows = parse_revolut_csv_transactions(csv_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount, 20.00)


if __name__ == "__main__":
    unittest.main()
