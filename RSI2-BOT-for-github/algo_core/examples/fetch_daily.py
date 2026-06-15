"""
Download FREE long-history DAILY data for blue-chip stocks (Yahoo, no API key).

Daily data goes back ~20+ years for free — enough observations to actually test an edge,
unlike the shallow intraday feeds.

USAGE
-----
    python algo_core/examples/fetch_daily.py
    python algo_core/examples/fetch_daily.py MSFT AAPL NVDA AMZN JPM JNJ PG KO

Saves one CSV per ticker (e.g. MSFT_daily.csv) in the project folder, columns:
    datetime,open,high,low,close,volume
"""
from __future__ import annotations

import os
import sys

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed. Run:  pip install -r algo_core/requirements.txt")
    sys.exit(1)

DEFAULT_BASKET = ["MSFT", "AAPL", "NVDA", "AMZN", "JPM", "JNJ", "PG", "KO"]


def fetch_one(ticker: str, folder: str) -> bool:
    df = yf.download(ticker, period="max", interval="1d",
                     auto_adjust=True, progress=False)
    if df is None or df.empty:
        print(f"  {ticker}: no data")
        return False
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).strip().lower() for c in df.columns]
    out = pd.DataFrame({
        "datetime": pd.to_datetime(df.index).tz_localize(None),
        "open": df["open"].values, "high": df["high"].values,
        "low": df["low"].values, "close": df["close"].values,
        "volume": df["volume"].values,
    }).dropna()
    path = os.path.join(folder, f"{ticker.upper()}_daily.csv")
    out.to_csv(path, index=False)
    print(f"  {ticker}: {len(out):,} rows  ({out['datetime'].iloc[0].date()} -> "
          f"{out['datetime'].iloc[-1].date()})")
    return True


def main() -> None:
    tickers = [t.upper() for t in sys.argv[1:]] or DEFAULT_BASKET
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print(f"Downloading DAILY data (period=max, split/div-adjusted) for: {tickers}")
    ok = sum(fetch_one(t, folder) for t in tickers)
    print(f"\nSaved {ok}/{len(tickers)} tickers.")
    print("Next: python algo_core/examples/run_meanrev.py "
          + " ".join(f"{t}_daily.csv" for t in tickers))


if __name__ == "__main__":
    main()
