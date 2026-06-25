"""Deterministic, offline fixtures."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def dates():
    return pd.bdate_range("2018-01-01", periods=400)


@pytest.fixture
def prices(dates):
    """A reproducible geometric random-walk price series (fixed seed)."""
    rng = np.random.default_rng(11)
    ret = rng.normal(0.0004, 0.015, len(dates))
    return pd.Series(100.0 * np.exp(np.cumsum(ret)), index=dates, name="SYN")


@pytest.fixture
def panel(dates):
    """A small multi-asset price panel for scan tests."""
    rng = np.random.default_rng(3)
    out = {}
    for t in ("AAA", "BBB", "CCC"):
        ret = rng.normal(0.0003, 0.013, len(dates))
        out[t] = 100.0 * np.exp(np.cumsum(ret))
    return pd.DataFrame(out, index=dates)
