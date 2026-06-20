import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from algo_core.backtest import PortfolioBacktester
from algo_core.data.loader import load_ohlcv
from algo_core.strategies import RSI2Reversion
from algo_core.paper import run_paper_sim
from algo_core.reporting import GREEN, RED, BOLD, CYAN, RESET
TEST_FRAC=0.30; MAX_WEIGHT=0.20; DEPLOY_CAP=0.60; SLIPPAGE_BPS=5.0; START_CASH=25_000.0
def _pct(x): return f"{(GREEN if x>=0 else RED)}{x*100:,.1f}%{RESET}"
def main():
    files=[f for f in sys.argv[1:] if os.path.basename(f).split('_')[0].upper()!='SPY']
    if not files: print("Give daily CSVs."); sys.exit(1)
    price={}
    for f in files:
        ticker=os.path.basename(f).split('_')[0].upper()
        try: price[ticker]=load_ohlcv(f)
        except Exception as e: print(f"  skip {ticker}: {e}")
    if not price: print("No usable data."); sys.exit(1)
    strat=RSI2Reversion()
    bt=PortfolioBacktester(max_weight=MAX_WEIGHT, max_total_deployment=DEPLOY_CAP, slippage_bps=SLIPPAGE_BPS).run(price, strat, test_frac=TEST_FRAC)
    sim=run_paper_sim(price, strat, starting_cash=START_CASH, max_weight=MAX_WEIGHT, max_total_deployment=DEPLOY_CAP, slippage_bps=SLIPPAGE_BPS, test_frac=TEST_FRAC, band=0.0)
    sim_band=run_paper_sim(price, strat, starting_cash=START_CASH, max_weight=MAX_WEIGHT, max_total_deployment=DEPLOY_CAP, slippage_bps=SLIPPAGE_BPS, test_frac=TEST_FRAC, band=0.02)
    bt_tr=bt.metrics["total_return"]; sim_tr=sim.metrics["total_return"]
    diff=abs(bt_tr-sim_tr); parity=diff<0.02
    print(f"\n{BOLD}{CYAN}PAPER ENGINE vs BACKTEST - parity check{RESET}")
    print(f"  Names: {len(price)}   OOS, cap-only ({DEPLOY_CAP*100:.0f}%), {SLIPPAGE_BPS:.0f}bps slip\n")
    print(f"  {'Metric':<16}{'Backtest':>14}{'Paper':>14}")
    print(f"  {'-'*44}")
    print(f"  {'Total return':<16}{_pct(bt_tr):>23}{_pct(sim_tr):>23}")
    print(f"  {'CAGR':<16}{_pct(bt.metrics['cagr']):>23}{_pct(sim.metrics['cagr']):>23}")
    print(f"  {'Sharpe':<16}{str(round(bt.metrics['sharpe'],3)):>14}{str(round(sim.metrics['sharpe'],3)):>14}")
    print(f"  {'Max drawdown':<16}{_pct(bt.metrics['max_drawdown']):>23}{_pct(sim.metrics['max_drawdown']):>23}")
    print(f"\n  Parity (within 2%): {(GREEN+'PASS'+RESET) if parity else (RED+'FAIL'+RESET)}  (diff {diff*100:.2f}%)")
    print(f"\n{BOLD}No-trade band (2%) - live realism{RESET}")
    print(f"  {'':16}{'trades':>14}{'total return':>16}")
    print(f"  {'band 0%':<16}{sim.metrics['n_trades']:>14,}{_pct(sim.metrics['total_return']):>23}")
    print(f"  {'band 2%':<16}{sim_band.metrics['n_trades']:>14,}{_pct(sim_band.metrics['total_return']):>23}")
    print()
if __name__=="__main__": main()
