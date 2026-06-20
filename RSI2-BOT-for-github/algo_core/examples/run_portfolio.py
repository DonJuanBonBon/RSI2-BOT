import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from algo_core.backtest import PortfolioBacktester
from algo_core.data.loader import load_ohlcv
from algo_core.strategies import RSI2Reversion
from algo_core.reporting import GREEN, RED, BOLD, CYAN, RESET
TEST_FRAC=0.30; MAX_WEIGHT=0.20; CAP=0.60; SLIPPAGE_BPS=5.0
def _pct(x): return f"{(GREEN if x>=0 else RED)}{x*100:,.1f}%{RESET}"
def _row(label,m):
    return f"  {label:<16}{_pct(m['cagr']):>16}{str(round(m['sharpe'],3)):>10}{_pct(m['max_drawdown']):>16}{m['avg_deployment']*100:>10.0f}%"
def main():
    files=sys.argv[1:]
    if not files: print("Give daily CSVs (include SPY_daily.csv)."); sys.exit(1)
    market=None; price={}
    for f in files:
        ticker=os.path.basename(f).split("_")[0].upper()
        try: df=load_ohlcv(f)
        except Exception as e: print(f"  skip {ticker}: {e}"); continue
        if ticker=="SPY": market=df
        else: price[ticker]=df
    if not price: print("No tradable names."); sys.exit(1)
    strat=RSI2Reversion()
    def run(cap,use_market):
        bt=PortfolioBacktester(max_weight=MAX_WEIGHT,max_total_deployment=cap,slippage_bps=SLIPPAGE_BPS)
        return bt.run(price,strat,market=(market if use_market else None),test_frac=TEST_FRAC).metrics
    none=run(1.0,False); cap_only=run(CAP,False)
    regime_only=run(1.0,True) if market is not None else None
    both=run(CAP,True) if market is not None else None
    print(f"\n{BOLD}{CYAN}RSI(2) PORTFOLIO - OOS risk-control isolation, {len(price)} names{RESET}")
    print(f"  Per-name cap {MAX_WEIGHT*100:.0f}%  Deployment cap {CAP*100:.0f}%  Regime: {'SPY 200d' if market is not None else 'add SPY'}")
    print(f"\n  {BOLD}{'Config':<16}{'CAGR':>16}{'Sharpe':>10}{'MaxDD':>16}{'AvgDeploy':>11}{RESET}")
    print(f"  {'-'*68}")
    print(_row("none",none)); print(_row("cap-only",cap_only))
    if regime_only: print(_row("regime-only",regime_only)); print(_row("both",both))
    print(f"\n{BOLD}How to read it:{RESET}")
    print("  Best = biggest MaxDD cut per unit Sharpe lost. Choose by risk posture.\n")
if __name__=="__main__": main()
