#!/usr/bin/env python3
"""
RSI2-BOT  -  your automated paper-trading bot, in one file.

WHAT YOU CAN TYPE (just copy one of these):
    python bot.py check     ->  is my broker connected, and how much money is in the account?
    python bot.py run       ->  run the bot for today (find stocks, place the practice trades)
    python bot.py status    ->  how is my bot doing? (value, profit/loss, what it owns)
    python bot.py reset     ->  start the record over (use once, after changing starting money)
    python bot.py test      ->  run the bot's built-in self-checks
    python bot.py help      ->  show this menu

Everything here uses PRACTICE money (paper trading). No real money is ever used.
Run `python bot.py run` once each weekday morning or evening. That's it.
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess

# Use modern UTF-8 text so output never crashes when saved to a log file on Windows.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from algo_core.reporting import GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET
from algo_core.data.loader import load_ohlcv
from algo_core.strategies import RSI2Reversion
from algo_core.paper import step_forward
from algo_core.backtest import latest_target_weights
from algo_core.live import rebalance_to_targets
from algo_core.examples.run_daily import (fetch_basket, BASKET, STARTING_CASH, BAND,
                                          STATE_DIR, DATA_DIR)

MAX_WEIGHT = 0.20
DEPLOY_CAP = 0.60
WIDTH = 66


def block(title, color=CYAN):
    bar = "=" * (WIDTH - 2)
    print(f"\n{BOLD}{color}+{bar}+{RESET}")
    print(f"{BOLD}{color}| {title.ljust(WIDTH - 3)}|{RESET}")
    print(f"{BOLD}{color}+{bar}+{RESET}")


def row(label, value, color=""):
    print(f"   {label:<22}{color}{value}{RESET}")


def money(x):
    return f"${x:,.2f}"


def signed_money(x):
    c = GREEN if x >= 0 else RED
    return f"{c}{'+' if x >= 0 else ''}{money(x)}{RESET}"


def has_keys():
    return bool(os.getenv("ALPACA_API_KEY") and os.getenv("ALPACA_SECRET_KEY"))


def _load_prices():
    price = {}
    for t in BASKET:
        p = os.path.join(DATA_DIR, f"{t}_daily.csv")
        if os.path.exists(p):
            try:
                price[t] = load_ohlcv(p)
            except Exception:
                pass
    return price


def cmd_check():
    block("STEP 1  -  IS YOUR BROKER CONNECTED?", CYAN)
    if not has_keys():
        row("Status", "Not connected yet", RED)
        print(f"\n   {YELLOW}Your Alpaca keys aren't set on this computer yet.{RESET}")
        print("   Add your PAPER keys (see START_HERE.md), then run this again.")
        return
    try:
        from algo_core.live.alpaca_broker import AlpacaBroker
        broker = AlpacaBroker(paper=True)
        info = broker.account_info()
    except Exception as e:
        row("Status", "Could not connect", RED)
        print(f"\n   {YELLOW}{e}{RESET}")
        print("   Double-check you used your PAPER keys (they start with 'PK').")
        return
    connected = ("ACTIVE" in str(info["status"]).upper()) and not info["trading_blocked"]
    row("Status", "Connected and ready" if connected else "Needs attention",
        GREEN if connected else YELLOW)
    row("Account type", "Practice money (paper)" if info["paper"] else "LIVE")
    row("Account value", money(info["equity"]), GREEN)
    row("Cash available", money(info["cash"]))
    try:
        row("Market right now", "Open" if broker.is_market_open() else "Closed (orders run at next open)")
    except Exception:
        pass
    if connected:
        print(f"\n   {GREEN}You're all set. Next, type:  python bot.py run{RESET}")


def cmd_run():
    block("RUNNING YOUR BOT FOR TODAY", CYAN)
    print(f"   1. Getting the latest prices for {len(BASKET)} stocks ...")
    fetched = fetch_basket(BASKET)
    price = _load_prices()
    if not price:
        print(f"   {RED}Couldn't get any prices and no saved data found. Stopping.{RESET}")
        return
    if fetched == 0:
        print(f"      {YELLOW}Couldn't refresh online -- using the last saved prices.{RESET}")
    else:
        print(f"      got fresh prices for {fetched} stocks.")
    print("   2. Updating your performance record ...")
    step_forward(price, RSI2Reversion(), STATE_DIR, starting_cash=STARTING_CASH, band=BAND)
    print("   3. Deciding what to hold today ...")
    targets = latest_target_weights(price, RSI2Reversion(),
                                    max_weight=MAX_WEIGHT, max_total_deployment=DEPLOY_CAP)
    if targets:
        print(f"      the bot wants to hold {GREEN}{len(targets)}{RESET} stock(s):")
        for t, w in sorted(targets.items(), key=lambda kv: -kv[1]):
            print(f"        - {t}: about {w * 100:.0f}% of your money")
    else:
        print(f"      nothing looks worth buying today -- staying in cash. {GREY}(normal){RESET}")
    print("   4. Sending the trades to your practice account ...")
    if not has_keys():
        print(f"      {YELLOW}Broker not connected -- skipped. Run 'python bot.py check' first.{RESET}")
    else:
        try:
            from algo_core.live.alpaca_broker import AlpacaBroker
            broker = AlpacaBroker(paper=True)
            prices = {t: float(df["close"].iloc[-1]) for t, df in price.items()}
            orders = rebalance_to_targets(broker, targets, prices, band=BAND, dry_run=False)
            if orders:
                print(f"      placed {len(orders)} order(s):")
                for o in orders:
                    verb = "BUY " if o["side"] == "buy" else "SELL"
                    c = GREEN if o["side"] == "buy" else RED
                    print(f"        - {c}{verb}{RESET} {o['symbol']:<6} ({money(o['notional'])})")
            else:
                print("      nothing to change -- already holding the right stocks.")
        except Exception as e:
            print(f"      {YELLOW}Broker step had a problem (skipped, will retry tomorrow): {e}{RESET}")
    block("DONE  -  practice money only, no real funds used", GREEN)
    print(f"   {GREY}Orders fill at the next market open. See how you're doing: python bot.py status{RESET}")


def cmd_status():
    block("HOW YOUR BOT IS DOING", CYAN)
    rec = os.path.join(STATE_DIR, "track_record.csv")
    if not os.path.exists(rec):
        print(f"   No record yet. Run it once first:  {BOLD}python bot.py run{RESET}")
        return
    import pandas as pd
    df = pd.read_csv(rec)
    if df.empty:
        print("   The record is empty. Run: python bot.py run")
        return
    eq = df["equity"].astype(float)
    start, cur = float(eq.iloc[0]), float(eq.iloc[-1])
    profit = cur - start
    pct = (cur / start - 1) * 100 if start else 0.0
    worst = float((eq / eq.cummax() - 1).min()) * 100
    row("Days running", str(len(df)))
    row("Started with", money(start))
    row("Now worth", money(cur), GREEN if cur >= start else RED)
    row("Profit / loss", f"{signed_money(profit)}  ({'+' if pct >= 0 else ''}{pct:.2f}%)")
    row("Worst dip so far", f"{worst:.2f}%", RED if worst < 0 else "")
    st_path = os.path.join(STATE_DIR, "account_state.json")
    if os.path.exists(st_path):
        try:
            st = json.load(open(st_path))
            pos = st.get("positions", {})
            cash = float(st.get("cash", 0.0))
            invested = cur - cash
            print()
            row("Money invested", f"{money(invested)}  ({invested / cur * 100:.0f}%)" if cur else money(invested))
            row("Money in cash", f"{money(cash)}  ({cash / cur * 100:.0f}%)" if cur else money(cash))
            if pos:
                print(f"\n   {BOLD}Stocks you own right now:{RESET}")
                for t, sh in sorted(pos.items()):
                    print(f"     - {t}: {float(sh):.2f} shares")
            else:
                print(f"\n   {GREY}Not holding any stocks right now (all in cash).{RESET}")
        except Exception:
            pass
    print(f"\n   {GREY}Reminder: a few days tells you nothing. Real results take months.{RESET}")


def cmd_reset():
    block("RESET YOUR RECORD", YELLOW)
    print(f"   This erases your current practice record and starts fresh at {money(STARTING_CASH)}.")
    try:
        ans = input("\n   Type YES to confirm (anything else cancels): ").strip()
    except EOFError:
        ans = ""
    if ans != "YES":
        print("   Cancelled -- nothing changed.")
        return
    if os.path.isdir(STATE_DIR):
        shutil.rmtree(STATE_DIR, ignore_errors=True)
    print(f"   {GREEN}Done. Your next 'run' starts fresh at {money(STARTING_CASH)}.{RESET}")


def cmd_help():
    block("RSI2-BOT  -  WHAT DO YOU WANT TO DO?", CYAN)
    print(f"   {BOLD}python bot.py check{RESET}    Is my broker connected?  How much money?")
    print(f"   {BOLD}python bot.py run{RESET}      Run the bot for today (find stocks, place trades)")
    print(f"   {BOLD}python bot.py status{RESET}   How is my bot doing? (value, profit, holdings)")
    print(f"   {BOLD}python bot.py reset{RESET}    Start the record over")
    print(f"   {BOLD}python bot.py test{RESET}     Run the built-in self-checks")
    print(f"\n   {GREY}Everything uses practice money. Run 'run' once each weekday.{RESET}")
    print(f"   {GREY}New here? Open START_HERE.md first.{RESET}")


def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "help"
    try:
        if cmd == "check":
            cmd_check()
        elif cmd in ("run", "auto", "update"):
            cmd_run()
        elif cmd == "status":
            cmd_status()
        elif cmd == "reset":
            cmd_reset()
        elif cmd == "test":
            subprocess.run([sys.executable, "-m", "pytest", "algo_core/tests/", "-q"], cwd=HERE)
        else:
            cmd_help()
    except Exception as e:
        print(f"\n{RED}Something went wrong: {type(e).__name__}: {e}{RESET}")
        print(f"{GREY}If this keeps happening, copy this message for support.{RESET}")


if __name__ == "__main__":
    main()
