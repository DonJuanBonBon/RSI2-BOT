"""
ALPACA PREFLIGHT — verify your PAPER connection. Places NO orders.

This is the FIRST thing to run after setting up Alpaca. It connects with your paper keys and
prints account status, balances, current positions, and whether the market is open. If this
works, the connection is good and you can move on to a dry-run, then a tiny test order.

SETUP (one time)
----------------
  1. Create a free account at https://alpaca.markets and open the PAPER trading dashboard.
  2. Generate paper API keys (API Keys section). Copy the Key ID and Secret.
  3. Install the SDK:            pip install alpaca-py
  4. Set environment variables (PowerShell, this session):
         $env:ALPACA_API_KEY="your_key_id"
         $env:ALPACA_SECRET_KEY="your_secret"
     (To persist them, use System > Environment Variables, or setx.)
  5. Run:                        python algo_core/examples/check_alpaca.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from algo_core.reporting import GREEN, RED, YELLOW, BOLD, CYAN, GREY, RESET


def main() -> None:
    print(f"\n{BOLD}{CYAN}ALPACA PREFLIGHT (paper) — read-only, no orders{RESET}")

    if not os.getenv("ALPACA_API_KEY") or not os.getenv("ALPACA_SECRET_KEY"):
        print(f"{RED}Missing credentials.{RESET} Set them first:")
        print('  $env:ALPACA_API_KEY="your_paper_key"')
        print('  $env:ALPACA_SECRET_KEY="your_paper_secret"')
        sys.exit(1)

    try:
        from algo_core.live.alpaca_broker import AlpacaBroker
    except Exception as e:
        print(f"{RED}Import error: {e}{RESET}")
        sys.exit(1)

    try:
        broker = AlpacaBroker(paper=True)
    except Exception as e:
        print(f"{RED}Could not create client: {e}{RESET}")
        print("If this says alpaca-py not installed, run: pip install alpaca-py")
        sys.exit(1)

    try:
        info = broker.account_info()
    except Exception as e:
        print(f"{RED}Connected to the SDK but the API call failed: {e}{RESET}")
        print("Most likely the keys are wrong, or they are LIVE keys used on the paper "
              "endpoint. Regenerate PAPER keys and retry.")
        sys.exit(1)

    ok = info["status"] == "ACTIVE" and not info["trading_blocked"]
    print(f"\n  {BOLD}Connection: {(GREEN+'OK'+RESET) if ok else (YELLOW+'CHECK'+RESET)}{RESET}")
    print(f"  Mode            : {'PAPER' if info['paper'] else 'LIVE'}")
    print(f"  Account status  : {info['status']}  "
          f"(trading_blocked={info['trading_blocked']})")
    acct = info["account_number"]
    print(f"  Account #       : {GREY}{('*' * max(0, len(acct)-4)) + acct[-4:] if acct else 'n/a'}{RESET}")
    print(f"  Equity          : ${info['equity']:,.2f}")
    print(f"  Cash            : ${info['cash']:,.2f}")
    print(f"  Buying power    : ${info['buying_power']:,.2f}")

    try:
        is_open = broker.is_market_open()
        print(f"  Market open now : {'yes' if is_open else 'no (orders queue for next open)'}")
    except Exception as e:
        print(f"  Market clock    : {YELLOW}could not read ({e}){RESET}")

    try:
        pos = broker.get_positions()
        if pos:
            print(f"\n  {BOLD}Current positions{RESET}")
            for s, q in sorted(pos.items()):
                print(f"    {s:<8}{q:>14.4f} shares")
        else:
            print(f"\n  Current positions: none (flat)")
    except Exception as e:
        print(f"  {YELLOW}Could not read positions: {e}{RESET}")

    if ok:
        print(f"\n  {GREEN}Preflight passed. Next: a dry-run, then one tiny test order.{RESET}")
        print(f"  {GREY}See STEP_1_2_GUIDE.md for the exact sequence.{RESET}")
    else:
        print(f"\n  {YELLOW}Account not fully active — resolve the status before trading.{RESET}")
    print()


if __name__ == "__main__":
    main()
