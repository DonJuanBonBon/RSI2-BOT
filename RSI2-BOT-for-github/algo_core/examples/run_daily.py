"""
DAILY WORKFLOW — run this once per day, AFTER the US market close (or before the next open).

It does two things in one command:
  1. Refreshes daily price data for the basket (free, via yfinance).
  2. Advances the forward paper account one day and appends to the track record.

    python algo_core/examples/run_daily.py

That's it. To see how the record is doing:  python algo_core/examples/show_track_record.py

WHY AFTER THE CLOSE: RSI(2) decides from the day's closing prices, then the position is held
into the next session — exactly matching the backtest's one-day execution lag. Running after
the close gives the freshest complete bar; the simulated fill is the next session.

Data note: free Yahoo daily data is fine for this daily strategy. This script needs internet
(to reach Yahoo); run it on your own machine, not inside a sandbox.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from algo_core.data.loader import load_ohlcv
from algo_core.strategies import RSI2Reversion
from algo_core.paper import step_forward
from algo_core.reporting import GREEN, RED, YELLOW, BOLD, CYAN, GREY, RESET

# The traded universe (broad, laggard-inclusive large caps).
BASKET = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "JPM", "JNJ", "PG", "KO",
          "HD", "WMT", "UNH", "MA", "INTC", "VZ", "PFE", "DIS", "NKE", "BA",
          "T", "F", "CSCO", "IBM"]

STARTING_CASH = 250_000.0
BAND = 0.02
PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT, "data")
STATE_DIR = os.path.join(PROJECT, "paper_state")
os.makedirs(DATA_DIR, exist_ok=True)


def fetch_basket(tickers) -> int:
    try:
        import yfinance as yf
    except ImportError:
        print(f"{RED}yfinance not installed.{RESET} Run: pip install -r algo_core/requirements.txt")
        return 0
    ok = 0
    for t in tickers:
        try:
            df = yf.download(t, period="max", interval="1d", auto_adjust=True, progress=False)
            if df is None or df.empty:
                print(f"  {YELLOW}{t}: no data{RESET}")
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(c).strip().lower() for c in df.columns]
            out = pd.DataFrame({
                "datetime": pd.to_datetime(df.index).tz_localize(None),
                "open": df["open"].values, "high": df["high"].values,
                "low": df["low"].values, "close": df["close"].values,
                "volume": df["volume"].values,
            }).dropna()
            out.to_csv(os.path.join(DATA_DIR, f"{t}_daily.csv"), index=False)
            ok += 1
        except Exception as e:
            print(f"  {YELLOW}{t}: fetch failed ({e}){RESET}")
    return ok


def main() -> None:
    print(f"\n{BOLD}{CYAN}DAILY WORKFLOW{RESET}")
    print(f"  1/2 refreshing data for {len(BASKET)} names ...")
    n = fetch_basket(BASKET)
    if n == 0:
        print(f"{RED}No data fetched — aborting (need internet + yfinance).{RESET}")
        sys.exit(1)
    print(f"      fetched {n}/{len(BASKET)} names")

    price = {}
    for t in BASKET:
        p = os.path.join(DATA_DIR, f"{t}_daily.csv")
        if os.path.exists(p):
            try:
                price[t] = load_ohlcv(p)
            except Exception as e:
                print(f"  {YELLOW}{t}: load error ({e}){RESET}")
    if not price:
        print(f"{RED}No usable data.{RESET}")
        sys.exit(1)

    print(f"  2/2 advancing the paper account ...")
    res = step_forward(price, RSI2Reversion(), STATE_DIR,
                       starting_cash=STARTING_CASH, band=BAND)

    if res["status"] == "up_to_date":
        print(f"  {GREEN}Already processed through {res['date']}.{RESET} Nothing to do "
              f"(markets may not have a new close yet).")
    elif res["status"] == "no_data":
        print(f"  {RED}No data.{RESET}")
    else:
        print(f"  {GREEN}Stepped to {res['date']}{RESET}  equity ${res['equity']:,.2f}  "
              f"positions: {res['n_positions']}")
        if res["targets"]:
            print(f"\n  {BOLD}Target holdings for next session{RESET}")
            for t, w in sorted(res["targets"].items(), key=lambda kv: -kv[1]):
                print(f"    {t:<8}{w*100:>6.1f}%")
        else:
            print(f"  Flat — no positions today.")
    print(f"\n{GREY}Track record: {os.path.join(STATE_DIR, 'track_record.csv')}{RESET}")
    print(f"{GREY}This is a simulation. To send these targets to Alpaca paper, see run_live.py.{RESET}\n")


if __name__ == "__main__":
    main()