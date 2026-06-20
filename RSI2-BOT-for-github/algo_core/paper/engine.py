from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from .account import PaperAccount
from ..backtest.portfolio import compute_target_weights
from ..backtest.metrics import compute_metrics

@dataclass
class PaperSimResult:
    equity: pd.Series
    account: PaperAccount
    metrics: dict

def run_paper_sim(price_data, strategy, starting_cash=25_000.0, max_weight=0.20,
                  max_total_deployment=0.60, slippage_bps=5.0, test_frac=0.30,
                  market=None, regime_sma=200, band=0.0):
    regime_close = market["close"] if market is not None else None
    target, closes = compute_target_weights(price_data, strategy, max_weight,
                                            max_total_deployment, regime_close, regime_sma)
    cost_rate = slippage_bps / 10_000.0
    if test_frac is not None:
        cut = int(len(closes) * (1 - test_frac)); idx = closes.index[cut:]
    else:
        idx = closes.index
    acct = PaperAccount(cash=starting_cash); eq = []
    for d in idx:
        prices = closes.loc[d].to_dict()
        eq.append(acct.mark_to_market(prices))
        acct.rebalance_to(target.loc[d].to_dict(), prices, cost_rate, date=d, band=band)
    equity = pd.Series(eq, index=idx, name="paper_equity")
    rets = equity.pct_change().fillna(0.0)
    m = compute_metrics(rets, periods_per_year=252)
    m["final_equity"] = round(float(equity.iloc[-1]), 2)
    m["n_trades"] = len(acct.trade_log)
    return PaperSimResult(equity, acct, m)
