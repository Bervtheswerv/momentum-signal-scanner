"""Tests for the strategy hierarchy — including Liskov substitutability."""

import pandas as pd

from scanner.strategy import MACDStrategy, Panel, RSIStrategy, Strategy

ALL_STRATEGIES = [RSIStrategy(), MACDStrategy()]


def test_positions_are_long_short_flat(prices):
    for strat in ALL_STRATEGIES:
        pos = strat.generate_position(strat.compute_indicators(prices))
        assert set(pos.unique()).issubset({-1, 0, 1})
        assert not pos.isna().any()


def test_substitutable_through_base_interface(prices):
    """Anything operating on a Strategy works for every concrete strategy
    without knowing its type — the Liskov contract."""
    def consume(s: Strategy):
        ind = s.compute_indicators(prices)
        pos = s.generate_position(ind)
        panels = s.panels(ind)
        return s.label, len(pos), panels

    for strat in ALL_STRATEGIES:
        label, n, panels = consume(strat)
        assert isinstance(label, str) and n == len(prices)
        assert panels and all(isinstance(p, Panel) for p in panels)


def test_labels_are_descriptive():
    assert RSIStrategy(14, 30, 70).label == "RSI(14) 30/70"
    assert MACDStrategy(12, 26, 9).label == "MACD(12,26,9)"
