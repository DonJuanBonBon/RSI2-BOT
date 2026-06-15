import numpy as np
import pandas as pd
from algo_core.paper import PaperAccount, run_paper_sim
from algo_core.backtest import PortfolioBacktester
from algo_core.strategies import RSI2Reversion

def _daily(seed, n=1200, drift=0.0003):
    rng = np.random.RandomState(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, 0.012, n)))
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": close, "high": close*1.005, "low": close*0.995,
                         "close": close, "volume": 1e6}, index=idx)

def _data(k=6):
    return {f"T{i}": _daily(i) for i in range(k)}

def test_account_value_conserved_on_rebalance_no_cost():
    acct = PaperAccount(cash=10_000.0); prices = {"A":100.0,"B":50.0}
    before = acct.mark_to_market(prices)
    acct.rebalance_to({"A":0.5,"B":0.5}, prices, cost_rate=0.0)
    assert abs(before - acct.mark_to_market(prices)) < 1e-6

def test_costs_reduce_equity():
    acct = PaperAccount(cash=10_000.0); prices = {"A":100.0}
    acct.rebalance_to({"A":1.0}, prices, cost_rate=0.001)
    assert acct.mark_to_market(prices) < 10_000.0

def test_paper_matches_vectorized_backtest():
    data = _data(6)
    bt = PortfolioBacktester(max_weight=0.2, max_total_deployment=0.6, slippage_bps=5).run(data, RSI2Reversion(), test_frac=0.3)
    sim = run_paper_sim(data, RSI2Reversion(), starting_cash=25_000, max_weight=0.2, max_total_deployment=0.6, slippage_bps=5, test_frac=0.3, band=0.0)
    assert abs(bt.metrics["total_return"] - sim.metrics["total_return"]) < 0.02

def test_paper_equity_positive_and_indexed():
    sim = run_paper_sim(_data(5), RSI2Reversion(), test_frac=0.3)
    assert (sim.equity > 0).all()
    assert sim.equity.index.is_monotonic_increasing

def test_band_reduces_trades():
    data = _data(8)
    nb = run_paper_sim(data, RSI2Reversion(), test_frac=0.3, band=0.0)
    wb = run_paper_sim(data, RSI2Reversion(), test_frac=0.3, band=0.02)
    assert wb.metrics["n_trades"] < nb.metrics["n_trades"]

def test_band_keeps_return_in_reasonable_range():
    data = _data(8)
    nb = run_paper_sim(data, RSI2Reversion(), test_frac=0.3, band=0.0)
    wb = run_paper_sim(data, RSI2Reversion(), test_frac=0.3, band=0.02)
    assert abs(nb.metrics["total_return"] - wb.metrics["total_return"]) < 0.10

def test_band_full_exit_when_target_zero():
    acct = PaperAccount(cash=10_000.0); prices = {"A":100.0}
    acct.rebalance_to({"A":0.5}, prices, cost_rate=0.0, band=0.02)
    assert acct.positions.get("A",0) > 0
    acct.rebalance_to({"A":0.0}, prices, cost_rate=0.0, band=0.02)
    assert acct.positions.get("A",0.0) == 0.0
