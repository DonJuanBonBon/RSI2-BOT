"""
SHOW TRACK RECORD — a colored summary of your forward paper-trading performance.

    python algo_core/examples/show_track_record.py

Reads paper_state/track_record.csv (built by run_daily.py / run_forward_paper.py) and reports
days tracked, total return, CAGR, max drawdown, current equity, and the current holdings.
Pure read — changes nothing.
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from algo_core.reporting import GREEN, RED, BOLD, CYAN, GREY, RESET

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATE_DIR = os.path.join(PROJECT, "paper_state")


def _pct(x):
    return f"{(GREEN if x >= 0 else RED)}{x*100:,.2f}%{RESET}"


def main() -> None:
    rec_path = os.path.join(STATE_DIR, "track_record.csv")
    if not os.path.exists(rec_path):
        print("No track record yet. Run: python algo_core/examples/run_daily.py")
        return

    df = pd.read_csv(rec_path)
    if df.empty:
        print("Track record is empty.")
        return

    eq = df["equity"].astype(float)
    start, current = float(eq.iloc[0]), float(eq.iloc[-1])
    total_ret = current / start - 1.0
    days = len(df)
    years = days / 252.0
    cagr = (current / start) ** (1 / years) - 1.0 if years > 0 else float("nan")
    peak = eq.cummax()
    max_dd = float((eq / peak - 1.0).min())

    print(f"\n{BOLD}{CYAN}FORWARD PAPER TRACK RECORD{RESET}")
    print(f"  Period          : {df['date'].iloc[0]}  ->  {df['date'].iloc[-1]}  "
          f"({days} trading days)")
    print(f"  Start equity    : ${start:,.2f}")
    print(f"  Current equity  : ${current:,.2f}")
    print(f"  Total return    : {_pct(total_ret)}")
    if years >= 0.1:
        print(f"  CAGR (annualized): {_pct(cagr)}")
    else:
        print(f"  CAGR            : {GREY}n/a (need more history){RESET}")
    print(f"  Max drawdown    : {_pct(max_dd)}")
    if "deployment_pct" in df.columns:
        print(f"  Avg deployment  : {df['deployment_pct'].astype(float).mean():.1f}%")

    state_path = os.path.join(STATE_DIR, "account_state.json")
    if os.path.exists(state_path):
        try:
            st = json.load(open(state_path))
            pos = st.get("positions", {})
            print(f"\n  {BOLD}Current holdings{RESET}  (cash ${float(st.get('cash', 0)):,.2f})")
            if pos:
                for t, sh in sorted(pos.items()):
                    print(f"    {t:<8}{float(sh):>14.4f} shares")
            else:
                print("    none (flat)")
        except Exception:
            pass

    print(f"\n{GREY}Honest note: a few weeks of data proves the pipeline, not the edge. "
          f"Months of record are what matter.{RESET}\n")


if __name__ == "__main__":
    main()
