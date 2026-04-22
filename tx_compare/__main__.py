from __future__ import annotations

import argparse
import csv
from pathlib import Path

from tx_compare.csv_parser import parse_ynab_transactions
from tx_compare.matcher import MatchConfig, find_missing
from tx_compare.models import MissingTransaction, Transaction
from tx_compare.pdf_parser import parse_pdf_transactions
from tx_compare.revolut_csv_parser import parse_revolut_csv_transactions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tx-compare",
        description="Compare YNAB export transactions to statement transactions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="Compare two sources")
    compare.add_argument(
        "--ynab",
        required=True,
        nargs="+",
        type=Path,
        help="One or more YNAB CSV export file paths",
    )
    statements = compare.add_mutually_exclusive_group(required=True)
    statements.add_argument(
        "--amex-pdf",
        nargs="+",
        type=Path,
        help="One or more AMEX PDF statement paths",
    )
    statements.add_argument(
        "--revo-csv",
        nargs="+",
        type=Path,
        help="One or more Revolut account statement CSV paths",
    )
    compare.add_argument(
        "--out-csv",
        type=Path,
        default=None,
        help="Optional output CSV report path",
    )
    compare.add_argument(
        "--out",
        dest="out_csv",
        type=Path,
        default=None,
        help=argparse.SUPPRESS,
    )
    compare.add_argument(
        "--out-text",
        type=Path,
        default=None,
        help="Optional output plain-text report path",
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
    compare.add_argument(
        "--merchant-check",
        action="store_true",
        help="Enable merchant-name similarity check (off by default)",
    )
    compare.add_argument(
        "--no-merchant-check",
        dest="merchant_check",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    compare.set_defaults(merchant_check=False)
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


def _human_rows(
    missing_in_ynab: list[MissingTransaction],
    missing_in_statement: list[MissingTransaction],
    ynab_label: str,
    statement_label: str,
) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    for row in missing_in_ynab:
        rows.append(
            (
                row.tx_date.isoformat(),
                f"{row.amount:.2f}",
                row.merchant,
                ynab_label,
            )
        )
    for row in missing_in_statement:
        rows.append(
            (
                row.tx_date.isoformat(),
                f"{row.amount:.2f}",
                row.merchant,
                statement_label,
            )
        )
    rows.sort(key=lambda item: (item[0], float(item[1]), item[2].lower(), item[3]))
    return rows


def build_human_report(
    missing_in_ynab: list[MissingTransaction],
    missing_in_statement: list[MissingTransaction],
    ynab_label: str = "YNAB",
    statement_label: str = "STATEMENT",
) -> str:
    rows = _human_rows(
        missing_in_ynab,
        missing_in_statement,
        ynab_label,
        statement_label,
    )
    header = ["Date", "Amount", "Merchant", "Missing In"]
    if not rows:
        return "Missing Transactions:\n(none)"

    date_width = max(len(header[0]), *(len(row[0]) for row in rows))
    amount_width = max(len(header[1]), *(len(row[1]) for row in rows))
    merchant_width = max(len(header[2]), *(len(row[2]) for row in rows))
    location_width = max(len(header[3]), *(len(row[3]) for row in rows))

    lines = ["Missing Transactions:"]
    lines.append(
        f"{header[0]:<{date_width}}  {header[1]:>{amount_width}}  "
        f"{header[2]:<{merchant_width}}  {header[3]:<{location_width}}"
    )
    lines.append(
        f"{'-' * date_width}  {'-' * amount_width}  {'-' * merchant_width}  {'-' * location_width}"
    )
    for row in rows:
        lines.append(
            f"{row[0]:<{date_width}}  {row[1]:>{amount_width}}  "
            f"{row[2]:<{merchant_width}}  {row[3]:<{location_width}}"
        )
    return "\n".join(lines)


def write_human_report(path: Path, report_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text + "\n", encoding="utf-8")


def load_ynab_transactions(paths: list[Path]) -> list[Transaction]:
    all_rows: list[Transaction] = []
    for path in paths:
        all_rows.extend(parse_ynab_transactions(path))
    return all_rows


def load_amex_transactions(paths: list[Path]) -> list[Transaction]:
    all_rows: list[Transaction] = []
    for path in paths:
        all_rows.extend(parse_pdf_transactions(path))
    return all_rows


def load_revolut_transactions(paths: list[Path]) -> list[Transaction]:
    all_rows: list[Transaction] = []
    for path in paths:
        all_rows.extend(parse_revolut_csv_transactions(path))
    return all_rows


def run_compare(args: argparse.Namespace) -> int:
    ynab_transactions = load_ynab_transactions(args.ynab)

    if args.amex_pdf:
        statement_paths = args.amex_pdf
        statement_label = "AMEX PDF"
        statement_transactions = load_amex_transactions(args.amex_pdf)
    else:
        statement_paths = args.revo_csv
        statement_label = "REVOLUT CSV"
        statement_transactions = load_revolut_transactions(args.revo_csv)

    config = MatchConfig(
        amount_tolerance=args.amount_tolerance,
        merchant_threshold=args.merchant_threshold,
        check_merchant=args.merchant_check,
    )

    missing_in_ynab, missing_in_statement, window = find_missing(
        ynab_transactions=ynab_transactions,
        statement_transactions=statement_transactions,
        config=config,
    )

    print(f"YNAB files: {len(args.ynab)} | rows parsed: {len(ynab_transactions)}")
    print(
        f"{statement_label} files: {len(statement_paths)} | "
        f"rows parsed: {len(statement_transactions)}"
    )
    if window is None:
        print("Overlap window: none")
    else:
        print(f"Overlap window: {window[0].isoformat()} -> {window[1].isoformat()}")

    print(f"Missing in YNAB: {len(missing_in_ynab)}")
    print(f"Missing in {statement_label}: {len(missing_in_statement)}")
    report_text = build_human_report(
        missing_in_ynab,
        missing_in_statement,
        ynab_label="YNAB",
        statement_label=statement_label,
    )
    print()
    print(report_text)

    if args.out_csv:
        combined = [*missing_in_ynab, *missing_in_statement]
        write_missing_report(args.out_csv, combined)
        print(f"\nCSV report written to: {args.out_csv}")

    if args.out_text:
        write_human_report(args.out_text, report_text)
        print(f"Text report written to: {args.out_text}")

    return 1 if missing_in_ynab or missing_in_statement else 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "compare":
        return run_compare(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
