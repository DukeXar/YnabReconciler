# Transaction Compare CLI

Command-line app to compare financial transactions from:

- a YNAB CSV export
- an AMEX PDF statement or Revolut account statement CSV

and report what is missing in each source.

By default it compares in both directions, but only inside the overlapping date window between both sources.

## Requirements

- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 -m tx_compare compare \
  --ynab ./SampleData/Amex/*.csv \
  --amex-pdf ./SampleData/Amex/*.pdf
```

Revolut example:

```bash
python3 -m tx_compare compare \
  --ynab "./SampleData/Rev/Selected Transactions for Anton's Budget as of 2026-04-22 09-53.csv" \
  --revo-csv ./SampleData/Rev/account-statement*.csv
```

Use unquoted wildcards so your shell expands them.

This prints a human-readable table to the terminal by default.

Optional report outputs:

- `--out-text ./missing_report.txt` to save the human-readable report
- `--out-csv ./missing_report.csv` to save a machine-readable CSV report

Optional tuning:

- `--merchant-threshold` (default `0.55`): merchant name similarity requirement
- `--amount-tolerance` (default `0.01`): tolerated amount delta
- by default merchant names are ignored and matching uses date/amount
- `--merchant-check`: also require merchant-name similarity for matching

Exit code:

- `0` when no missing transactions were found
- `1` when at least one missing transaction was found

## Notes

- YNAB parser expects columns like `Date`, `Payee`, `Outflow`, `Inflow`.
- AMEX parser is optimized for Amex-style PDF statement transaction rows.
- Revolut parser expects account statement CSV columns like `Started Date`, `Description`, `Amount`, `Fee`, `State`.
- Transactions from multiple input files are kept as provided; overlapping files are treated as distinct input.
