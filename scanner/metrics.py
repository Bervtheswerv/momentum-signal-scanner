"""
metrics.py — performance statistics for a strategy's return stream.

Methodology fix vs the original: the old code ranked strategies by WIN RATE
alone. Win rate is dangerously incomplete — a strategy can win 90% of the time
and still lose money if the 10% of losers are large. So we keep win rate (it's
intuitive) but rank on risk-adjusted return (Sharpe) and report expectancy
(average PnL per trade), which together actually describe whether a strategy
makes money.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def total_return(returns: pd.Series) -> float:
    """Cumulative return over the whole stream, e.g. 0.35 == +35%."""
    return float((1.0 + returns).prod() - 1.0)


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = TRADING_DAYS) -> float:
    """Annualised Sharpe = mean(excess)/std(excess) * sqrt(periods_per_year).
    NaN if volatility is zero or there are fewer than 2 observations."""
    if len(returns) < 2 or returns.std(ddof=1) == 0:
        return float("nan")
    excess = returns - risk_free / periods_per_year
    return float(excess.mean() / excess.std(ddof=1) * np.sqrt(periods_per_year))


def max_drawdown(returns: pd.Series) -> float:
    """Worst peak-to-trough fall of the equity curve, as a negative fraction."""
    if len(returns) == 0:
        return float("nan")
    equity = (1.0 + returns).cumprod()
    return float((equity / equity.cummax() - 1.0).min())


def trade_stats(position: pd.Series, returns: pd.Series) -> dict:
    """Per-trade statistics from a held-position series and the daily returns.

    A 'trade' is a maximal run of constant, non-zero HELD position. We group on
    the lagged position (`position.shift(1)`), because that is the position that
    actually earned each day's return — the same one-bar lag the engine uses.
    Each trade's return is the compounded daily return over its run.

    Returns win_rate (%), expectancy (mean trade return), and n_trades.
    """
    held = position.shift(1).fillna(0).astype(int)
    # New group whenever the held position changes value.
    group_id = (held != held.shift()).cumsum()

    trade_returns = []
    for _, idx in returns.groupby(group_id).groups.items():
        if held.loc[idx[0]] == 0:
            continue  # flat stretch is not a trade
        trade_returns.append((1.0 + returns.loc[idx]).prod() - 1.0)

    n = len(trade_returns)
    if n == 0:
        return {"win_rate": 0.0, "expectancy": 0.0, "n_trades": 0}
    arr = np.array(trade_returns)
    return {
        "win_rate": float((arr > 0).mean() * 100.0),
        "expectancy": float(arr.mean()),
        "n_trades": n,
    }
