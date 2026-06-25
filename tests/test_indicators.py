"""Tests for the hand-rolled indicators."""

import numpy as np
import pandas as pd

from scanner.indicators import macd, rsi


def test_rsi_bounded(prices):
    r = rsi(prices, 14).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_rsi_all_gains_is_100():
    rising = pd.Series(np.arange(1, 60, dtype=float))
    assert np.allclose(rsi(rising, 14).dropna(), 100.0)


def test_macd_columns_and_identity(prices):
    df = macd(prices)
    assert list(df.columns) == ["macd", "signal", "hist"]
    # histogram is macd minus signal, by definition
    assert np.allclose((df["macd"] - df["signal"]).values, df["hist"].values)
