"""
LIVE/PAPER ORDER RUNNER — computes today's target portfolio and the orders to reach it.

SAFETY: this is DRY-RUN by default. It prints the planned orders and places nothing. To
actually send orders you must (a) pass --execute and (b) use --broker alpaca with paper
credentials set. Live (real-money) trading is intentionally NOT reachable from this script.

USAGE
-----
  # 1) Plan only, no broker, using a hypothetical $25k (safe, offline):
  python algo_core/examples/run_live.py AAPL_daily.csv MSFT_daily.csv ...

  # 2) Plan against your Alpaca PAPER account (needs ALPACA_API_KEY / ALPACA_SECRET_KEY,
  #    and `pip install alpaca-py`):
  python algo_core/examples/run_live.py --broker alpaca AAPL_daily.csv MSFT_daily.csv ...

  # 3) Actually submit to Alpaca PAPER (still fake money):
  python algo_core/examples/run_live.py --broker alpaca --execute AAPL_daily.csv ...
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from algo_core.data.loader import load_ohlcv
from algo_core.strategies import RSI2Reversion
from algo_core.backtest import latest_target_weights
from algo_core.live import MockBroker, rebalance_to_targets
from algo_core.reporting import GREEN, RED, YELLOW, BOLD, CYAN, GREY, RESET

MAX_WEIGHT = 0.20
DEPLOY_CAP = 0.60
BAND = 0.02
MAX_ORDER_NOTIONAL = None       # set a $ cap per order for extra safety if desired


def main() -> None:
    args = sys.argv[1:]
    capital = 25_000.0
    use_alpaca = False
    execute = False
    rest = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--capital":
            capital = float(args[i + 1]); i += 2
        elif a == "--broker":
            use_alpaca = (args[i + 1].lower() == "alpaca"); i += 2
        elif a == "--execute":
            execute = True; i += 1
        else:
            rest.append(a); i += 1

    files = [f for f in rest if os.path.basename(f).split("_")[0].upper() != "SPY"]
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
        print("No usable data."); sys.exit(1)

    targets = latest_target_weights(price, RSI2Reversion(), max_weight=MAX_WEIGHT,
                                    max_total_deployment=DEPLOY_CAP)
    prices = {t: float(df["close"].iloc[-1]) for t, df in price.items()}

    if use_alpaca:
        try:
            from algo_core.live.alpaca_broker import AlpacaBroker
            broker = AlpacaBroker(paper=True)         # PAPER ONLY
            mode = "ALPACA PAPER"
        except Exception as e:
            print(f"{RED}Alpaca unavailable: {e}{RESET}")
            print("Falling back to offline planning with --capital.")
            broker = MockBroker(capital, prices); mode = "OFFLINE PLAN"
    else:
        broker = MockBroker(capital, prices); mode = "OFFLINE PLAN"

    if isinstance(broker, MockBroker):
        broker.set_prices(prices)

    dry = not execute
    orders = rebalance_to_targets(broker, targets, prices, band=BAND, dry_run=dry,
                                  max_order_notional=MAX_ORDER_NOTIONAL)

    print(f"\n{BOLD}{CYAN}LIVE ORDER RUNNER — mode: {mode}{RESET}")
    print(f"  Equity: ${broker.get_equity():,.2f}   band {BAND*100:.0f}%   "
          f"{'DRY-RUN (nothing sent)' if dry else 'EXECUTED'}")
    print(f"\n  {BOLD}Target holdings{RESET}")
    if targets:
        for t, w in sorted(targets.items(), key=lambda kv: -kv[1]):
            print(f"    {t:<8}{w*100:>6.1f}%")
    else:
        print("    (flat — no positions today)")

    print(f"\n  {BOLD}Planned orders{RESET}")
    if not orders:
        print("    none (already within band of targets)")
    else:
        for o in orders:
            c = GREEN if o["side"] == "buy" else RED
            print(f"    {c}{o['side'].upper():<4}{RESET} {o['symbol']:<8}"
                  f"qty {o['qty']:<12} (${o['notional']:,.2f})")

    if dry:
        print(f"\n{YELLOW}DRY-RUN: no orders were placed. Add --execute (with --broker alpaca) "
              f"to send to your PAPER account.{RESET}")
    print(f"{GREY}Real-money/live trading is not enabled from this script by design.{RESET}\n")


if __name__ == "__main__":
    main()
