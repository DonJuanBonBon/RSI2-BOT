"""
Causal technical indicators.

Every function here uses ONLY past and current data at each timestamp — never future
data. Rolling/ewm windows are causal by nature in pandas. We never call .shift(-n) here.

Course-code origin: rebuilt clean from the SMA/RSI/VWAP/Bollinger logic in the ATC bootcamp
(`6_sma.py`, `7_rsi.py`, `8_vwap.py`, `9_more_indicators/`) and the Harvard BB template,
but vectorized, documented, and de-risked.

All functions take a pandas Series (or DataFrame for OHLCV-based ones) and return a Series
aligned to the input index. Leading values are NaN until the window fills (expected).
"""
from __future__ import annotations

import pandas as pd
import numpy as np


def returns(close: pd.Series) -> pd.Series:
    """Simple period-over-period returns."""
    return close.pct_change()


def log_returns(close: pd.Series) -> pd.Series:
    """Log returns: ln(P_t / P_{t-1})."""
    return np.log(close / close.shift(1))


def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    _check_window(window)
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (span form, like most charting tools)."""
    _check_window(span)
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder's smoothing), range 0-100.
    Causal: at time t uses only deltas up to t.
    """
    _check_window(window)
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder's smoothing == EMA with alpha = 1/window
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    # When avg_loss == 0 (no losses), RSI is 100 by definition.
    out = out.where(avg_loss != 0.0, 100.0)
    return out


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    MACD line, signal line, histogram. Returns a DataFrame with columns
    ['macd', 'signal', 'hist'].
    """
    if fast >= slow:
        raise ValueError("fast span must be < slow span")
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0):
    """
    Bollinger Bands. Returns DataFrame ['mid', 'upper', 'lower'].
    Uses population std (ddof=0) to match common charting defaults.
    """
    _check_window(window)
    mid = sma(close, window)
    sd = close.rolling(window=window, min_periods=window).std(ddof=0)
    return pd.DataFrame(
        {"mid": mid, "upper": mid + num_std * sd, "lower": mid - num_std * sd}
    )


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """
    Average True Range. Expects columns: high, low, close.
    Causal Wilder smoothing.
    """
    _require_cols(df, ["high", "low", "close"])
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def vwap_rolling(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    Rolling VWAP over `window` bars (a causal alternative to session-anchored VWAP,
    which needs intraday session boundaries). Expects high, low, close, volume.
    """
    _require_cols(df, ["high", "low", "close", "volume"])
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = typical * df["volume"]
    return (
        pv.rolling(window=window, min_periods=window).sum()
        / df["volume"].rolling(window=window, min_periods=window).sum()
    )


def rolling_zscore(series: pd.Series, window: int = 20) -> pd.Series:
    """Rolling z-score — the workhorse of mean-reversion signals. Causal."""
    _check_window(window)
    mean = series.rolling(window=window, min_periods=window).mean()
    std = series.rolling(window=window, min_periods=window).std(ddof=0)
    return (series - mean) / std.replace(0.0, np.nan)


# ----------------------------- helpers ----------------------------- #
def _check_window(window: int) -> None:
    if not isinstance(window, (int, np.integer)) or window < 1:
        raise ValueError(f"window must be a positive int, got {window!r}")


def _require_cols(df: pd.DataFrame, cols) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"DataFrame missing required columns: {missing}")
