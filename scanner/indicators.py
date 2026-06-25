"""
indicators.py — RSI and MACD as plain pandas functions.

Refactor note vs the original: the old code called `talib.RSI` / `talib.MACD`.
TA-Lib is a C library that's painful to install, so it makes the repo hard to
run and the indicators a black box. These hand-rolled versions are portable
(pandas only) and defensible — you can explain exactly what they compute.
"""

from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index via Wilder's smoothing.

    RSI = 100 - 100/(1 + RS), where RS = avg_gain / avg_loss over `period`.
    Wilder's averaging is a recursive (exponential) mean, not a simple rolling
    mean — reproduced exactly by ewm(alpha=1/period, adjust=False). Pinned to
    100 when there are no losses.
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.where(avg_loss != 0.0, 100.0).rename("rsi")


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Moving Average Convergence Divergence.

    macd  = EMA(fast) - EMA(slow)        (momentum of the trend)
    signal = EMA(macd, signal)           (a smoothing of the macd line)
    hist  = macd - signal                (what we actually trade on)

    EMAs use adjust=False so the result matches standard charting platforms.
    Returns a DataFrame with columns ['macd', 'signal', 'hist'].
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})
