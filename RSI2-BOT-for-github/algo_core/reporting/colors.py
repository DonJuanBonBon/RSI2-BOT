"""Colored terminal output for backtest results. Green=profit, red=loss."""
from __future__ import annotations
import sys
try:
    import colorama
    colorama.just_fix_windows_console()
    _HAS_COLORAMA = True
except Exception:
    _HAS_COLORAMA = False
_COLOR_ON = bool(_HAS_COLORAMA) and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
GREEN = "\033[32m" if _COLOR_ON else ""
RED = "\033[31m" if _COLOR_ON else ""
YELLOW = "\033[33m" if _COLOR_ON else ""
CYAN = "\033[36m" if _COLOR_ON else ""
GREY = "\033[90m" if _COLOR_ON else ""
BOLD = "\033[1m" if _COLOR_ON else ""
RESET = "\033[0m" if _COLOR_ON else ""

def color_money(x: float, width: int = 0) -> str:
    s = f"${x:,.2f}"
    if width:
        s = s.rjust(width)
    return f"{(GREEN if x >= 0 else RED)}{s}{RESET}"

def _pct(x: float) -> str:
    return f"{(GREEN if x >= 0 else RED)}{x*100:,.2f}%{RESET}"

def print_orb_report(result, max_trades_shown: int = 15) -> None:
    s = result.stats
    label = s.get("instrument_label", "")
    title = f"OPENING RANGE BREAKOUT — {label}".strip(" —")
    bar = "═" * 60
    print()
    print(f"{BOLD}{CYAN}╔{bar}╗{RESET}")
    print(f"{BOLD}{CYAN}║{title.center(60)}║{RESET}")
    print(f"{BOLD}{CYAN}╚{bar}╝{RESET}")
    if result.is_synthetic:
        print(f"{YELLOW}⚠  SYNTHETIC DATA — illustrative only, not real.{RESET}")
    print(f"\n{BOLD}Configuration{RESET}")
    print(f"  Instrument      : {s.get('instrument_label','n/a')}")
    print(f"  Sessions tested : {s['n_sessions']}")
    print(f"  OR window       : {s['or_minutes']} min   Direction: {s['direction']}")
    print(f"  Contracts       : {s['contracts']}   Point value: ${s['point_value']:.2f}")
    print(f"  Costs           : ${s['commission_per_side']:.2f}/side + {s['slippage_ticks']} tick slip")
    print(f"\n{BOLD}Headline{RESET}")
    print(f"  Net P&L         : {color_money(s['net_pnl'])}")
    print(f"  Gross P&L       : {color_money(s['gross_pnl'])}   Costs: {RED}-${s['total_costs']:,.2f}{RESET}")
    print(f"  Return on capital: {_pct(s['return_on_capital'])}  (start ${s['starting_capital']:,.0f})")
    print(f"  Max drawdown    : {color_money(s['max_drawdown'])}")
    print(f"\n{BOLD}Trade stats{RESET}")
    print(f"  Trades          : {s['n_trades']}   Wins: {GREEN}{s['n_wins']}{RESET}  Losses: {RED}{s['n_losses']}{RESET}")
    print(f"  Win rate        : {s['win_rate']*100:.1f}%")
    print(f"  Avg win         : {color_money(s['avg_win'])}   Avg loss: {color_money(s['avg_loss'])}")
    pf = s['profit_factor']
    pf_str = "inf" if pf == float("inf") else f"{pf:.2f}"
    print(f"  Profit factor   : {(GREEN if pf >= 1 else RED)}{pf_str}{RESET}   Expectancy/trade: {color_money(s['expectancy'])}")
    trades = result.trades
    if trades:
        print(f"\n{BOLD}Last {min(max_trades_shown, len(trades))} trades{RESET}")
        print(f"  {GREY}{'date':<12}{'side':<6}{'entry':>9}{'exit':>9}{'pts':>8}{'net $':>12}  reason{RESET}")
        for t in trades[-max_trades_shown:]:
            line = f"  {str(t.day):<12}{t.side:<6}{t.entry_px:>9.2f}{t.exit_px:>9.2f}{t.points:>8.2f}"
            print(line + color_money(t.net_pnl, width=12) + f"  {t.exit_reason}")
    print()
