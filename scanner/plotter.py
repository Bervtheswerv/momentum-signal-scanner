"""
plotter.py — strategy-agnostic plotting.

This is the Liskov/Open-Closed payoff. The old Plotter did
`isinstance(strategy, RSIStrategy)` / `isinstance(strategy, MACDStrategy)` to
decide what to draw. This one knows NOTHING about concrete strategies: it draws
the price with the position shading and trade markers, then loops over the
`panels` the strategy declared and renders each one generically. Add a Bollinger
strategy and this file never changes.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_result(result, save_dir: Path | str | None = None):
    """Render one ScanResult: price + held position + each declared indicator panel.

    :param result: a backtest.ScanResult.
    :param save_dir: if given, save a PNG there and close the figure; else return it.
    """
    n_panels = 1 + len(result.panels)
    heights = [3] + [1] * len(result.panels)
    fig, axes = plt.subplots(
        n_panels, 1, figsize=(13, 3 + 2.2 * n_panels),
        sharex=True, gridspec_kw={"height_ratios": heights},
    )
    axes = [axes] if n_panels == 1 else list(axes)

    ax_price = axes[0]
    ax_price.plot(result.close.index, result.close, lw=1.1, color="tab:blue", label="price")
    _shade_positions(ax_price, result.position)
    _mark_trades(ax_price, result.close, result.position)
    m = result.metrics
    ax_price.set_title(
        f"{result.ticker} — {result.strategy_label}    "
        f"(return {m['total_return']:.0%} · Sharpe {m['sharpe']:.2f} · "
        f"win {m['win_rate']:.0f}% · {m['n_trades']} trades)"
    )
    ax_price.set_ylabel("price ($)")
    ax_price.legend(loc="upper left")

    # Each strategy-declared panel, rendered uniformly — no strategy types named.
    for ax, panel in zip(axes[1:], result.panels):
        for line in panel.lines:
            ax.plot(line.series.index, line.series, lw=1.0, label=line.label)
        for y in panel.hlines:
            ax.axhline(y, ls="--", lw=0.8, color="grey", alpha=0.7)
        ax.set_ylabel(panel.ylabel)
        ax.legend(loc="upper left", fontsize=8)

    fig.tight_layout()
    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        path = save_dir / f"{result.ticker}_{result.strategy_label.replace(' ', '_').replace('/', '-')}.png"
        fig.savefig(path, dpi=110, bbox_inches="tight")
        plt.close(fig)
        return path
    return fig


def _shade_positions(ax, position: pd.Series):
    """Shade long stretches green and short stretches red."""
    for value, color in ((1, "tab:green"), (-1, "tab:red")):
        active = position == value
        start = None
        for ts, on in active.items():
            if on and start is None:
                start = ts
            elif not on and start is not None:
                ax.axvspan(start, ts, color=color, alpha=0.10)
                start = None
        if start is not None:
            ax.axvspan(start, active.index[-1], color=color, alpha=0.10)


def _mark_trades(ax, close: pd.Series, position: pd.Series):
    """Mark where the held position flips (entries/exits)."""
    change = position.diff().fillna(position)
    entries_long = change[(position == 1) & (change != 0)].index
    entries_short = change[(position == -1) & (change != 0)].index
    ax.scatter(entries_long, close.loc[entries_long], marker="^", color="green", s=70, zorder=5, label="go long")
    ax.scatter(entries_short, close.loc[entries_short], marker="v", color="red", s=70, zorder=5, label="go short")
