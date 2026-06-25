"""
results.py — persist the scan results.

Refactor note vs the original `DataManager`: the old code opened an Excel file
in append mode, wrote per-year sheets, re-read every sheet, recomputed a
'Consolidated' sheet and appended it again each year — fragile, and it
duplicated the consolidated rows on every run. A ranked scan is just one table,
so we write one clean CSV (the portable default) and optionally an Excel copy.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_results(results: pd.DataFrame, results_dir: Path | str, to_excel: bool = False) -> Path:
    """Write the ranked results table to CSV (and optionally .xlsx). Returns the
    CSV path."""
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "scan_results.csv"
    results.to_csv(csv_path, index=False)

    if to_excel:
        try:
            results.to_excel(results_dir / "scan_results.xlsx", index=False)
        except ModuleNotFoundError:
            print("openpyxl not installed; skipped the Excel copy (CSV written).")

    return csv_path
