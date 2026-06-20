from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .metrics import compute_metrics


def compute_target_weights(price_data, strategy, max_weight=0.20,
                           max_total_deployment=1.0, regime_close=None, regime_sma=200):
    closes = pd.DataFrame({t: df["close"] for t, df in price_data.items()}).sort_index()
    sig = pd.DataFrame({t: strategy.generate_signals(df).reindex(closes.index).fillna(0.0)
                        for t, df in price_data.items()})
    active = sig.sum(axis=1)
    slot = np.minimum(max_weight, 1.0 / active.replace(0.0, np.nan))
    target = sig.mul(slot, axis=0).fillna(0.0)
    row_sum = target.sum(axis=1)
    scale = (max_total_deployment / row_sum).where(row_sum > max_total_deployment, 1.0)
    target = target.mul(scale, axis=0).fillna(0.0)
    if regime_close is not None:
        sma = regime_close.rolling(regime_sma, min_periods=regime_sma).mean()
        on = (regime_close > sma).astype(float)
        on = on.reindex(closes.index).fillna(0.0)
        target = target.mul(on, axis=0)
    return target, closes


def latest_target_weights(price_data, strategy, max_weight=0.20, max_total_deployment=1.0,
                          market=None, regime_sma=200):
    regime_close = market["close"] if market is not None else None
    target, _ = compute_target_weights(price_data, strategy, max_weight,
                                       max_total_deployment, regime_close, regime_sma)
    last = target.iloc[-1]
    return {t: round(float(w), 4) for t, w in last.items() if w > 0}


@dataclass
class PortfolioResult:
    equity: pd.Series
    returns: pd.Series
    deployment: pd.Series
    weights: pd.DataFrame
    metrics: dict


class PortfolioBacktester:
    def __init__(self, max_weight=0.20, max_total_deployment=1.0, commission_bps=0.0,
                 slippage_bps=5.0, periods_per_year=252, regime_sma=200):
        if not 0 < max_weight <= 1: raise ValueError("max_weight in (0,1]")
        if not 0 < max_total_deployment <= 1: raise ValueError("max_total_deployment in (0,1]")
        self.max_weight=float(max_weight); self.max_total_deployment=float(max_total_deployment)
        self.commission_bps=float(commission_bps); self.slippage_bps=float(slippage_bps)
        self.periods_per_year=int(periods_per_year); self.regime_sma=int(regime_sma)

    @property
    def cost_rate(self): return (self.commission_bps + self.slippage_bps) / 10_000.0

    def run(self, price_data, strategy, market=None, test_frac=None):
        regime_close = market["close"] if market is not None else None
        target, closes = compute_target_weights(price_data, strategy, self.max_weight,
            self.max_total_deployment, regime_close, self.regime_sma)
        rets = closes.pct_change().fillna(0.0)
        effective = target.shift(1).fillna(0.0)
        if test_frac is not None:
            if not 0 < test_frac < 1: raise ValueError("test_frac in (0,1)")
            cut = int(len(closes) * (1 - test_frac))
            idx = closes.index[cut:]
            effective = effective.loc[idx]; rets = rets.loc[idx]
        turnover = effective.diff().abs().sum(axis=1)
        if len(turnover): turnover.iloc[0] = effective.iloc[0].abs().sum()
        costs = turnover * self.cost_rate
        port_ret = (effective * rets).sum(axis=1) - costs
        equity = (1.0 + port_ret).cumprod()
        deployment = effective.sum(axis=1)
        m = compute_metrics(port_ret, periods_per_year=self.periods_per_year)
        avg_dep = float(deployment.mean()) if len(deployment) else 0.0
        m["avg_deployment"]=round(avg_dep,4)
        m["max_deployment"]=round(float(deployment.max()) if len(deployment) else 0.0,4)
        cagr=m.get("cagr",float("nan"))
        m["return_on_deployed_approx"]=round(float(cagr/avg_dep),4) if avg_dep>0 and not np.isnan(cagr) else float("nan")
        gross=(1.0+(effective*rets).sum(axis=1)).cumprod()
        m["cost_drag"]=round(float(gross.iloc[-1]-equity.iloc[-1]),4) if len(gross) else 0.0
        return PortfolioResult(equity, port_ret, deployment, effective, m)
