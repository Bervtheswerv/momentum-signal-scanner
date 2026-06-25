"""
data.py — load the price universe, offline-first.

Refactor note vs the original `Asset` class: the old Asset had two jobs —
fetch data AND compute indicators. That's two responsibilities in one class.
Indicator maths now lives in `indicators.py` / the strategies, so this module
has the single job of producing a clean price panel.

Two bugs fixed for modern data:
  * The old code read `self.data['Adj Close']`, but current yfinance with
    auto_adjust returns an already-adjusted 'Close' and NO 'Adj Close'.
  * It fetched each ticker separately and per-year, which fragments the series
    and re-downloads constantly. We fetch the whole universe once and cache it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import REPO_ROOT

CACHE_DIR = REPO_ROOT / "data"


def load_universe(
    tickers: tuple[str, ...],
    start: str,
    end: str,
    cache_dir: Path | str = CACHE_DIR,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Return a DataFrame of adjusted closes (one column per ticker), cached.

    Reads the local CSV cache first; only downloads on a miss or force_refresh.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = "-".join(sorted(tickers))
    cache = cache_dir / f"universe_{key}_{start}_{end}.csv"

    if cache.exists() and not force_refresh:
        return pd.read_csv(cache, index_col=0, parse_dates=True)

    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "yfinance not installed and no cache present. "
            "`pip install -U yfinance` or drop a cached CSV at "
            f"{cache}."
        ) from exc

    raw = yf.download(list(tickers), start=start, end=end, auto_adjust=True, progress=False)
    # auto_adjust=True => 'Close' is already adjusted; columns are a MultiIndex
    # (field, ticker) for multi-ticker downloads.
    close = raw["Close"] if "Close" in raw else raw
    close = close.dropna(how="all")
    if close.empty:  # pragma: no cover
        raise RuntimeError("No data returned — Yahoo may be rate-limiting or yfinance is outdated.")
    close.to_csv(cache)
    return close
