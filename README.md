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
  --csv ./SampleData/transactions_1.csv ./SampleData/transactions_2.csv \
  --pdf ./SampleData/statement_1.pdf ./SampleData/statement_2.pdf
```

Wildcard example (shell expansion):

```bash
python3 -m tx_compare compare \
  --csv ./SampleData/*.csv \
  --pdf ./SampleData/*.pdf
```

Use unquoted wildcards so your shell expands them.

This prints a human-readable table to the terminal by default.

Optional report outputs:

- `--out-text ./missing_report.txt` to save the human-readable report
- `--out-csv ./missing_report.csv` to save a machine-readable CSV report

Optional tuning:

- `--merchant-threshold` (default `0.55`): merchant name similarity requirement
- `--amount-tolerance` (default `0.01`): tolerated amount delta

Exit code:

- `0` when no missing transactions were found
- `1` when at least one missing transaction was found

## Notes

- CSV parser expects columns like `Date`, `Payee`, `Outflow`, `Inflow`.
- PDF parser is optimized for Amex-style statement transaction rows.
- Duplicate transactions across multiple CSV inputs (or multiple PDF inputs) are deduplicated by normalized `(date, amount, merchant)`.
