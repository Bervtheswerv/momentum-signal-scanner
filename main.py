"""
main.py — run the scan end to end.

    python main.py              # uses the cached universe shipped in data/
    python main.py --refresh    # re-download the universe via yfinance
    python main.py --top 5      # also plot the top-5 ranked combos

Refactor note vs the original main: the old one imported `from strategies` /
`from backtester` (wrong module names, so it never ran) and built strategies
with `asset=None` (which crashed). This orchestrates cleanly: load once, scan,
rank, save, plot.
"""

from __future__ import annotations

import argparse
import warnings

from scanner.backtest import Backtester
from scanner.config import Config
from scanner.data import load_universe
from scanner.plotter import plot_result
from scanner.results import save_results
from scanner.strategy import MACDStrategy, RSIStrategy

warnings.filterwarnings("ignore")


def build_strategies():
    """The strategy set to scan. Add a line here to scan a new strategy —
    nothing else in the codebase needs to change (that's the point of the
    Liskov-clean design)."""
    return [RSIStrategy(period=14, lower=30, upper=70), MACDStrategy(12, 26, 9)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download prices")
    ap.add_argument("--top", type=int, default=4, help="how many top combos to plot")
    args = ap.parse_args()

    config = Config()
    config.ensure_dirs()

    prices = load_universe(config.universe, config.start, config.end, force_refresh=args.refresh)
    strategies = build_strategies()
    backtester = Backtester(config)

    results = backtester.scan(prices, strategies)
    csv_path = save_results(results, config.results_dir)
    print(f"\nScanned {len(prices.columns)} tickers × {len(strategies)} strategies "
          f"= {len(results)} combinations.")
    print(f"Results ranked by Sharpe → {csv_path}\n")
    print(results.head(args.top).round(3).to_string(index=False))

    # Plot the top-ranked combinations.
    for _, row in results.head(args.top).iterrows():
        close = prices[row["ticker"]].dropna()
        strategy = next(s for s in strategies if s.label == row["strategy"])
        result = backtester.run_one(row["ticker"], close, strategy)
        path = plot_result(result, save_dir=config.plots_dir)
        print(f"  plotted {path}")

    print("\nScan complete.")


if __name__ == "__main__":
    main()
