"""Tests for the metrics, including the per-trade stats."""

import numpy as np
import pandas as pd

from scanner.metrics import max_drawdown, sharpe_ratio, total_return, trade_stats


def test_sharpe_zero_vol_is_nan():
    assert np.isnan(sharpe_ratio(pd.Series([0.01, 0.01, 0.01])))


def test_max_drawdown_known():
    # equity 1 -> 0.8 -> 0.9 => worst drawdown -20%
    assert np.isclose(max_drawdown(pd.Series([0.0, -0.2, 0.125])), -0.2)


def test_total_return_known():
    assert np.isclose(total_return(pd.Series([0.1, -0.1])), 1.1 * 0.9 - 1.0)


def test_trade_stats_counts_held_runs():
    # held position (after the engine's shift) spends two non-zero runs:
    # a long run and a short run => 2 trades.
    idx = pd.RangeIndex(8)
    position = pd.Series([0, 1, 1, 1, 0, -1, -1, 0], index=idx)
    returns = pd.Series([0, 0, 0.02, 0.03, 0, 0, -0.04, 0], index=idx, dtype=float)
    stats = trade_stats(position, returns)
    assert stats["n_trades"] == 2
    # long run made money, short run lost => 50% win rate
    assert np.isclose(stats["win_rate"], 50.0)
