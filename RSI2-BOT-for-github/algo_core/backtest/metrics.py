"""
Performance metrics computed from a strategy return series.

`periods_per_year` controls annualization:
  - daily bars: 252 (equities) or 365 (crypto, 24/7)
  - hourly crypto: 24*365 = 8760
  - 15-min crypto: 4*24*365 = 35040
Pick the right one for your bar size or Sharpe will be meaningless.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_metrics(
    strat_returns: pd.Series,
    periods_per_year: int = 365,
    position: pd.Series | None = None,
) -> dict:
    """Return a dict of headline metrics from a per-bar return series."""
    r = strat_returns.dropna()
    if len(r) == 0:
        return {"error": "no returns"}

    equity = (1.0 + r).cumprod()
    total_return = equity.iloc[-1] - 1.0
    n = len(r)
    years = n / periods_per_year if periods_per_year else np.nan

    cagr = equity.iloc[-1] ** (1.0 / years) - 1.0 if years and years > 0 else np.nan

    mean, std = r.mean(), r.std(ddof=0)
    sharpe = (mean / std) * np.sqrt(periods_per_year) if std > 0 else np.nan

    downside = r[r < 0].std(ddof=0)
    sortino = (mean / downside) * np.sqrt(periods_per_year) if downside > 0 else np.nan

    max_dd = _max_drawdown(equity)
    calmar = (cagr / abs(max_dd)) if (max_dd < 0 and not np.isnan(cagr)) else np.nan

    win_rate = float((r > 0).mean())

    out = {
        "total_return": _f(total_return),
        "cagr": _f(cagr),
        "sharpe": _f(sharpe),
        "sortino": _f(sortino),
        "max_drawdown": _f(max_dd),
        "calmar": _f(calmar),
        "win_rate_per_bar": _f(win_rate),
        "n_bars": int(n),
        "periods_per_year": int(periods_per_year),
    }

    if position is not None:
        pos = position.reindex(r.index).fillna(0.0)
        # number of round-trip-ish position changes and time in market
        out["n_position_changes"] = int((pos.diff().fillna(pos) != 0).sum())
        out["exposure"] = _f(float((pos != 0).mean()))
    return out


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


def _f(x) -> float:
    try:
        return round(float(x), 6)
    except (TypeError, ValueError):
        return float("nan")
