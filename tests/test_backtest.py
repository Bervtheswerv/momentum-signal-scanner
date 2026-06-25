"""Tests for the engine — above all, lookahead safety."""

import numpy as np
import pandas as pd

from scanner.backtest import Backtester, simulate
from scanner.config import Config
from scanner.strategy import MACDStrategy, RSIStrategy


def test_lookahead_safety_is_exact(prices):
    rng = np.random.default_rng(0)
    pos = pd.Series(rng.integers(-1, 2, len(prices)), index=prices.index)
    ret = simulate(prices, pos, cost_bps=0.0)
    asset_ret = prices.pct_change(fill_method=None).fillna(0.0)
    expected = pos.shift(1).fillna(0.0) * asset_ret
    assert np.allclose(ret.values, expected.values)


def test_flat_earns_nothing(prices):
    pos = pd.Series(0, index=prices.index)
    assert np.allclose(simulate(prices, pos).values, 0.0)


def test_costs_reduce_returns(prices):
    rng = np.random.default_rng(1)
    pos = pd.Series(rng.integers(-1, 2, len(prices)), index=prices.index)
    free = (1 + simulate(prices, pos, 0.0)).prod()
    costed = (1 + simulate(prices, pos, 20.0)).prod()
    assert costed < free


def test_scan_is_ranked_and_complete(panel):
    bt = Backtester(Config())
    results = bt.scan(panel, [RSIStrategy(), MACDStrategy()])
    # 3 tickers x 2 strategies
    assert len(results) == 6
    assert {"ticker", "strategy", "sharpe", "win_rate", "expectancy"} <= set(results.columns)
    # sorted by Sharpe, descending
    assert results["sharpe"].is_monotonic_decreasing
