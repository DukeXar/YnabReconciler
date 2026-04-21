from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tx_compare.csv_parser import parse_csv_transactions
from tx_compare.matcher import MatchConfig, find_missing
from tx_compare.models import MissingTransaction
from tx_compare.pdf_parser import parse_pdf_transactions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tx-compare",
        description="Compare CSV transactions to PDF statement transactions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="Compare two sources")
    compare.add_argument("--csv", required=True, type=Path, help="Path to CSV file")
    compare.add_argument(
        "--pdf", required=True, type=Path, help="Path to PDF statement"
    )
    compare.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output CSV report path",
    )
    compare.add_argument(
        "--merchant-threshold",
        type=float,
        default=0.55,
        help="Merchant similarity threshold between 0 and 1",
    )
    compare.add_argument(
        "--amount-tolerance",
        type=float,
        default=0.01,
        help="Allowed amount delta for matching",
    )
    return parser


def write_missing_report(path: Path, rows: list[MissingTransaction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "direction",
                "date",
                "amount",
                "merchant",
                "reason",
                "raw_line",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "direction": row.direction,
                    "date": row.tx_date.isoformat(),
                    "amount": f"{row.amount:.2f}",
                    "merchant": row.merchant,
                    "reason": row.reason,
                    "raw_line": row.raw_line,
                }
            )


def _print_preview(label: str, rows: list[MissingTransaction], limit: int = 10) -> None:
    print(label)
    if not rows:
        print("  (none)")
        return
    for row in rows[:limit]:
        print(f"  {row.tx_date.isoformat()}  {row.amount:8.2f}  {row.merchant}")
    if len(rows) > limit:
        print(f"  ... and {len(rows) - limit} more")


def run_compare(args: argparse.Namespace) -> int:
    csv_transactions = parse_csv_transactions(args.csv)
    pdf_transactions = parse_pdf_transactions(args.pdf)
    config = MatchConfig(
        amount_tolerance=args.amount_tolerance,
        merchant_threshold=args.merchant_threshold,
    )

    missing_in_csv, missing_in_pdf, window = find_missing(
        csv_transactions=csv_transactions,
        pdf_transactions=pdf_transactions,
        config=config,
    )

    print(f"CSV rows parsed: {len(csv_transactions)}")
    print(f"PDF rows parsed: {len(pdf_transactions)}")
    if window is None:
        print("Overlap window: none")
    else:
        print(f"Overlap window: {window[0].isoformat()} -> {window[1].isoformat()}")

    print(f"Missing in CSV: {len(missing_in_csv)}")
    print(f"Missing in PDF: {len(missing_in_pdf)}")
    _print_preview("\nTop missing in CSV:", missing_in_csv)
    _print_preview("\nTop missing in PDF:", missing_in_pdf)

    if args.out:
        combined = [*missing_in_csv, *missing_in_pdf]
        write_missing_report(args.out, combined)
        print(f"\nReport written to: {args.out}")

    return 1 if missing_in_csv or missing_in_pdf else 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "compare":
        return run_compare(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
