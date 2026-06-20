"""
FORWARD PAPER TRADING — run this ONCE PER DAY (after the close) to build a real track record.

Each run advances the simulated account by the latest day of data and appends to
paper_state/track_record.csv. Over weeks and months this becomes your dated performance
record — the asset that matters for ever raising money or selling a service.

WORKFLOW (daily)
----------------
    python algo_core/examples/fetch_daily.py AAPL MSFT NVDA ...   # refresh data
    python algo_core/examples/run_forward_paper.py AAPL_daily.csv MSFT_daily.csv ...

It is idempotent per day: running twice the same day does nothing the second time.

This places NO real orders. It is a simulation that records what a disciplined daily
rebalance would have done.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from algo_core.data.loader import load_ohlcv
from algo_core.strategies import RSI2Reversion
from algo_core.paper import step_forward
from algo_core.reporting import GREEN, CYAN, BOLD, GREY, RESET

STATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "paper_state"))
START_CASH = 25_000.0
BAND = 0.02


def main() -> None:
    args = sys.argv[1:]
    capital = START_CASH
    if args and args[0] == "--capital":
        capital = float(args[1]); args = args[2:]
    files = [f for f in args if os.path.basename(f).split("_")[0].upper() != "SPY"]
    if not files:
        print("Give daily CSVs. First: python algo_core/examples/fetch_daily.py")
        sys.exit(1)

    price = {}
    for f in files:
        ticker = os.path.basename(f).split("_")[0].upper()
        try:
            price[ticker] = load_ohlcv(f)
        except Exception as e:
            print(f"  skip {ticker}: {e}")
    if not price:
        print("No usable data.")
        sys.exit(1)

    res = step_forward(price, RSI2Reversion(), STATE_DIR, starting_cash=capital, band=BAND)

    print(f"\n{BOLD}{CYAN}FORWARD PAPER TRADING{RESET}")
    if res["status"] == "up_to_date":
        print(f"  Already processed through {res['date']}. Nothing to do today.")
    elif res["status"] == "no_data":
        print("  No data found.")
    else:
        print(f"  Stepped to {res['date']}   equity ${res['equity']:,.2f}   "
              f"positions: {res['n_positions']}")
        if res["targets"]:
            print(f"\n  {BOLD}Target holdings (next session){RESET}")
            for t, w in sorted(res["targets"].items(), key=lambda kv: -kv[1]):
                print(f"    {t:<8}{w*100:>6.1f}%")
        else:
            print(f"  {GREEN}Flat — no positions today.{RESET}")
    print(f"\n{GREY}Track record: {os.path.join(STATE_DIR, 'track_record.csv')}{RESET}")
    print(f"{GREY}Simulation only — no real orders placed.{RESET}\n")


if __name__ == "__main__":
    main()
