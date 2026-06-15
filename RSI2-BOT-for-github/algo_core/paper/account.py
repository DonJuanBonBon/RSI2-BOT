from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd

@dataclass
class PaperAccount:
    cash: float
    positions: dict = field(default_factory=dict)
    trade_log: list = field(default_factory=list)
    def mark_to_market(self, prices: dict) -> float:
        val = self.cash
        for t, sh in self.positions.items():
            p = prices.get(t)
            if p is not None and not pd.isna(p): val += sh * p
        return val
    def rebalance_to(self, target_weights, prices, cost_rate, date=None, band=0.0):
        equity = self.mark_to_market(prices)
        if equity <= 0: return
        names = set(self.positions) | set(target_weights)
        for t in names:
            p = prices.get(t)
            if p is None or pd.isna(p) or p <= 0: continue
            tgt_w = max(0.0, float(target_weights.get(t, 0.0)))
            cur_shares = self.positions.get(t, 0.0)
            cur_w = (cur_shares * p) / equity
            if band > 0.0 and abs(tgt_w - cur_w) < band: continue
            tgt_shares = tgt_w * equity / p
            delta = tgt_shares - cur_shares
            if abs(delta * p) < 1e-9: continue
            trade_value = delta * p
            cost = abs(trade_value) * cost_rate
            self.cash -= trade_value; self.cash -= cost
            self.positions[t] = tgt_shares
            self.trade_log.append({"date":date,"ticker":t,"delta_shares":round(delta,6),"price":round(p,4),"cost":round(cost,4)})
        self.positions = {t: s for t, s in self.positions.items() if abs(s) > 1e-12}
