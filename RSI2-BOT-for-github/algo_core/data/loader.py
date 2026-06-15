"""
Data loading + out-of-sample splitting.

Why this module exists: the course backtests trained and tested on the SAME data, which is
how you fool yourself. Here, splitting your data into train (develop) and test (validate
ONCE) is the path of least resistance.
"""
from __future__ import annotations

from typing import Iterator

import pandas as pd

_CANONICAL = ["open", "high", "low", "close", "volume"]

# common column aliases seen in course CSVs / vendor exports
_ALIASES = {
    "date": "datetime", "time": "datetime", "timestamp": "datetime",
    "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume",
    "vol": "volume", "adj close": "close", "adj_close": "close",
}


def load_ohlcv(
    path: str,
    datetime_col: str | None = None,
    tz: str | None = None,
) -> pd.DataFrame:
    """
    Load an OHLCV CSV into a clean, datetime-indexed, sorted, de-duplicated DataFrame
    with lowercase columns open/high/low/close/volume.

    Raises if required price columns are missing — better a loud failure than a silent
    wrong backtest.
    """
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.rename(columns={k: v for k, v in _ALIASES.items() if k in df.columns})

    # find datetime
    dt = datetime_col.lower() if datetime_col else None
    if dt is None:
        dt = "datetime" if "datetime" in df.columns else None
    if dt is None:
        raise KeyError(
            "No datetime column found. Pass datetime_col=... explicitly. "
            f"Columns seen: {list(df.columns)}"
        )
    df[dt] = pd.to_datetime(df[dt], utc=tz is not None, errors="raise")
    df = df.set_index(dt).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    if tz:
        df.index = df.index.tz_convert(tz)

    missing = [c for c in ["open", "high", "low", "close"] if c not in df.columns]
    if missing:
        raise KeyError(f"CSV missing required price columns: {missing}")
    if "volume" not in df.columns:
        df["volume"] = pd.NA

    keep = [c for c in _CANONICAL if c in df.columns]
    return df[keep].astype({c: "float64" for c in keep if c != "volume"})


def train_test_split(df: pd.DataFrame, test_frac: float = 0.3):
    """
    Chronological split — NEVER shuffle time series. Returns (train, test).
    Develop on train; touch test as few times as possible (ideally once).
    """
    if not 0 < test_frac < 1:
        raise ValueError("test_frac must be in (0,1)")
    n = len(df)
    cut = int(n * (1 - test_frac))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def walk_forward_splits(
    df: pd.DataFrame, n_splits: int = 5, test_frac: float = 0.2
) -> Iterator[tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Expanding-window walk-forward: each fold trains on all data up to a point and tests on
    the next chunk. This is the honest way to estimate out-of-sample stability.
    Yields (train, test) DataFrames.
    """
    n = len(df)
    test_size = int(n * test_frac / n_splits) or 1
    first_train = n - test_size * n_splits
    if first_train <= 0:
        raise ValueError("Not enough rows for requested n_splits/test_frac")
    for i in range(n_splits):
        train_end = first_train + i * test_size
        test_end = train_end + test_size
        yield df.iloc[:train_end].copy(), df.iloc[train_end:test_end].copy()
