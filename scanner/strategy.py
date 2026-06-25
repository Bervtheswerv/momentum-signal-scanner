"""
strategy.py — the strategy hierarchy, redesigned for Liskov substitutability.

Two things the original got wrong, and how this fixes them:

1. LIFECYCLE BUG (the crash). The old `Strategy.__init__` did
   `self.signals = pd.DataFrame(index=self.asset.data.index)` — but `main.py`
   built strategies with `asset=None`, so construction blew up. Strategies here
   are STATELESS: they don't hold an asset. You hand price data to a method and
   get signals back, so one strategy instance works for every asset.

2. LISKOV / OPEN-CLOSED VIOLATION. The old `Plotter` did
   `isinstance(strategy, RSIStrategy)` to decide what to draw. That means a
   consumer of the abstraction had to know every concrete subclass — adding a
   strategy meant editing the Plotter. Here, each strategy is SELF-DESCRIBING:
   it declares its own indicator panels via `panels()`, so the Plotter renders
   any strategy uniformly and never names a subclass. New strategy → zero
   changes to the Plotter or the Backtest.

Position convention: a single integer series, +1 long / -1 short / 0 flat,
which is cleaner than the old separate Long/Short trigger columns and plugs
straight into a vectorised, lookahead-safe backtest.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .indicators import macd, rsi


# --- declarative plot description (lets the Plotter stay strategy-agnostic) ---
@dataclass(frozen=True)
class Line:
    """One line to draw on a panel."""
    series: pd.Series
    label: str


@dataclass(frozen=True)
class Panel:
    """One indicator subplot: some lines, a y-label, optional reference lines."""
    lines: tuple[Line, ...]
    ylabel: str
    hlines: tuple[float, ...] = ()


def _regime_from_crosses(long_entry: pd.Series, short_entry: pd.Series) -> pd.Series:
    """Turn boolean entry signals into a held +1/-1/0 position.

    Stamp +1 where a long signal fires, -1 where a short fires, then forward-fill
    to HOLD that stance until the opposite signal flips it. Flat (0) before the
    first signal. This is shared by every strategy, so the regime logic lives in
    exactly one place.
    """
    pos = pd.Series(np.nan, index=long_entry.index)
    pos[long_entry] = 1.0
    pos[short_entry] = -1.0
    return pos.ffill().fillna(0.0).astype("int8").rename("position")


class Strategy(ABC):
    """Abstract strategy. Subclasses are fully substitutable: every consumer
    uses only `label`, `compute_indicators`, `generate_position`, and `panels`,
    never the concrete type."""

    @property
    @abstractmethod
    def label(self) -> str:
        """Human-readable name, e.g. 'RSI(14) 30/70'. Used in plots and results."""

    @abstractmethod
    def compute_indicators(self, close: pd.Series) -> pd.DataFrame:
        """Return a DataFrame of the indicator column(s) this strategy needs."""

    @abstractmethod
    def generate_position(self, indicators: pd.DataFrame) -> pd.Series:
        """Return the +1/-1/0 position series. Must be lookahead-safe: a position
        for bar t may use data only up to and including bar t."""

    @abstractmethod
    def panels(self, indicators: pd.DataFrame) -> list[Panel]:
        """Describe how to plot this strategy's indicators (for the Plotter)."""


class RSIStrategy(Strategy):
    """Mean-reversion on RSI: go long when RSI crosses up through the oversold
    line, short when it crosses down through the overbought line."""

    def __init__(self, period: int = 14, lower: float = 30.0, upper: float = 70.0):
        self.period = period
        self.lower = lower
        self.upper = upper

    @property
    def label(self) -> str:
        return f"RSI({self.period}) {self.lower:.0f}/{self.upper:.0f}"

    def compute_indicators(self, close: pd.Series) -> pd.DataFrame:
        return rsi(close, self.period).to_frame()

    def generate_position(self, indicators: pd.DataFrame) -> pd.Series:
        r = indicators["rsi"]
        prev = r.shift(1)  # yesterday's RSI — keeps the cross past-and-present only
        long_entry = (prev <= self.lower) & (r > self.lower)
        short_entry = (prev >= self.upper) & (r < self.upper)
        return _regime_from_crosses(long_entry, short_entry)

    def panels(self, indicators: pd.DataFrame) -> list[Panel]:
        return [Panel(
            lines=(Line(indicators["rsi"], "RSI"),),
            ylabel="RSI",
            hlines=(self.lower, self.upper),
        )]


class MACDStrategy(Strategy):
    """Trend/momentum on the MACD histogram: long when the histogram crosses
    above zero, short when it crosses below."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    @property
    def label(self) -> str:
        return f"MACD({self.fast},{self.slow},{self.signal})"

    def compute_indicators(self, close: pd.Series) -> pd.DataFrame:
        return macd(close, self.fast, self.slow, self.signal)

    def generate_position(self, indicators: pd.DataFrame) -> pd.Series:
        h = indicators["hist"]
        prev = h.shift(1)
        long_entry = (prev < 0.0) & (h > 0.0)
        short_entry = (prev > 0.0) & (h < 0.0)
        return _regime_from_crosses(long_entry, short_entry)

    def panels(self, indicators: pd.DataFrame) -> list[Panel]:
        return [Panel(
            lines=(
                Line(indicators["macd"], "MACD"),
                Line(indicators["signal"], "signal"),
                Line(indicators["hist"], "histogram"),
            ),
            ylabel="MACD",
            hlines=(0.0,),
        )]
