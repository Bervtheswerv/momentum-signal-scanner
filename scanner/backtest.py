"""
backtest.py — the scanning engine.

Two methodology fixes over the original live here.

(1) LOOKAHEAD. The old `compute_pnl` entered a trade at the SAME bar's close
    that generated the signal — you can't trade on a close you haven't seen yet.
    `simulate()` enforces the one-bar lag: a position decided at bar t earns the
    market's move at bar t+1 (`position.shift(1) * return`). Same defence as my
    signal-backtester.

(2) RANKING. The old engine ranked combos by win rate alone. `scan()` ranks by
    Sharpe (risk-adjusted return) and also reports expectancy, drawdown and
    trade count, so a high-win-rate-but-loses-money combo can't top the table.

It also drops the dead `DataFrame.append` (removed in pandas 2.0) — results are
built as a list of dicts and assembled once.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import Config
from .metrics import max_drawdown, sharpe_ratio, total_return, trade_stats
from .strategy import Strategy


def simulate(close: pd.Series, position: pd.Series, cost_bps: float = 0.0) -> pd.Series:
    """Lookahead-safe daily net returns for a +1/-1/0 position over `close`.

    strategy_ret_t = position_{t-1} * asset_ret_t  -  cost on turnover.
    The shift(1) is the execution lag; without it the backtest sees the future.
    """
    asset_ret = close.pct_change(fill_method=None).fillna(0.0)
    held = position.shift(1).fillna(0.0)
    gross = held * asset_ret
    turnover = position.diff().abs().fillna(position.abs())
    cost = turnover * (cost_bps / 10_000.0)
    return (gross - cost).rename("strategy_ret")


@dataclass
class ScanResult:
    """Full result of one (ticker, strategy) run — metrics plus the series
    needed to plot it, so nothing has to be recomputed downstream."""

    ticker: str
    strategy_label: str
    close: pd.Series
    indicators: pd.DataFrame
    position: pd.Series
    returns: pd.Series
    metrics: dict
    panels: list  # declarative plot panels from the strategy; Plotter needs nothing else


class Backtester:
    """Runs every strategy over every ticker and ranks the combinations."""

    def __init__(self, config: Config):
        self.config = config

    def run_one(self, ticker: str, close: pd.Series, strategy: Strategy) -> ScanResult:
        """Backtest a single (ticker, strategy) pair."""
        indicators = strategy.compute_indicators(close)
        position = strategy.generate_position(indicators)
        returns = simulate(close, position, self.config.cost_bps)

        metrics = {
            "total_return": total_return(returns),
            "sharpe": sharpe_ratio(returns, self.config.risk_free),
            "max_drawdown": max_drawdown(returns),
            **trade_stats(position, returns),
        }
        return ScanResult(
            ticker, strategy.label, close, indicators, position, returns, metrics,
            panels=strategy.panels(indicators),
        )

    def scan(self, prices: pd.DataFrame, strategies: list[Strategy]) -> pd.DataFrame:
        """Scan the whole universe × strategy set; return a results table ranked
        by Sharpe (best first)."""
        rows = []
        for ticker in prices.columns:
            close = prices[ticker].dropna()
            if close.empty:
                continue
            for strategy in strategies:
                r = self.run_one(ticker, close, strategy)
                rows.append({"ticker": r.ticker, "strategy": r.strategy_label, **r.metrics})

        results = pd.DataFrame(rows)
        return results.sort_values("sharpe", ascending=False, ignore_index=True)
