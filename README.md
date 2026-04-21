# Transaction Compare CLI

Command-line app to compare financial transactions from:

- a CSV export
- a PDF statement

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
  --csv "./SampleData/Selected Transactions for Anton's Budget as of 2026-04-21 18-08.csv" \
  --pdf "./SampleData/27_Jan_2026_-_26_Feb_2026.pdf" \
  --out ./missing_report.csv
```

Optional tuning:

- `--merchant-threshold` (default `0.55`): merchant name similarity requirement
- `--amount-tolerance` (default `0.01`): tolerated amount delta

Exit code:

- `0` when no missing transactions were found
- `1` when at least one missing transaction was found

## Notes

- CSV parser expects columns like `Date`, `Payee`, `Outflow`, `Inflow`.
- PDF parser is optimized for Amex-style statement transaction rows.
