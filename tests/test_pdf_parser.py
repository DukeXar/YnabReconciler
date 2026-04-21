from __future__ import annotations

import unittest
from datetime import date

from tx_compare.pdf_parser import parse_layout_page_text, parse_statement_text


class PDFParserTests(unittest.TestCase):
    def test_parse_statement_text_extracts_rows(self) -> None:
        text = """
From 27 January to 26 February 2026
Jan 29 Jan 29 NORDIC BALANCE LONDON 87.50
Jan 29 Jan 29 TFL TRAVEL CHARGE TFL.GOV.UK/CP 7.55
"""
        rows = parse_statement_text(text)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].tx_date, date(2026, 1, 29))
        self.assertEqual(rows[0].amount, 87.50)
        self.assertEqual(rows[1].merchant_norm, "transport for london")

    def test_parse_layout_page_text_extracts_amount_and_credit(self) -> None:
        text = """
Jan25 Jan27 PAYPAL *BETTERME 04MR 4029357733 15.19
Feb6 Feb6 PAYMENT RECEIVED - THANK YOU 1,000.00
CR
"""
        rows = parse_layout_page_text(text, (date(2026, 1, 27), date(2026, 2, 26)))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].tx_date, date(2026, 1, 25))
        self.assertEqual(rows[0].amount, 15.19)


if __name__ == "__main__":
    unittest.main()
