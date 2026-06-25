"""
config.py — all tunable settings in one place.

Refactor note vs the original: the old Config hardcoded an absolute output path
on one machine, so the project only ran there. Outputs now live in a repo-
relative `output/` folder, so anyone who clones it can run it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Repo root = two levels up from this file (scanner/ -> repo/).
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    """Immutable run configuration. Frozen so a run can't accidentally mutate it."""

    # --- output locations (all relative to the repo) ---
    output_dir: Path = REPO_ROOT / "output"
    plots_dir: Path = REPO_ROOT / "output" / "plots"
    results_dir: Path = REPO_ROOT / "output" / "results"

    # --- universe & period ---
    # A diversified set: mega-cap tech, semis (NVDA/TSM), a bank (JPM), and a
    # high-vol name (TSLA). Swap in any tickers you like — `--refresh` pulls them
    # live; the shipped cache covers exactly this set so the demo runs offline.
    universe: tuple[str, ...] = (
        "AAPL", "MSFT", "AMZN", "GOOGL", "NVDA", "JPM", "TSLA", "TSM",
    )
    start: str = "2015-01-01"
    end: str = "2021-12-31"

    # --- economics ---
    risk_free: float = 0.02      # annual, for Sharpe
    cost_bps: float = 5.0        # per position change (turnover), in basis points

    def ensure_dirs(self) -> None:
        """Create the output directories if they don't exist."""
        for d in (self.output_dir, self.plots_dir, self.results_dir):
            Path(d).mkdir(parents=True, exist_ok=True)
