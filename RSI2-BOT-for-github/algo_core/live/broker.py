from __future__ import annotations
import math
from abc import ABC, abstractmethod

class Broker(ABC):
    @abstractmethod
    def get_equity(self) -> float: ...
    @abstractmethod
    def get_positions(self) -> dict: ...
    @abstractmethod
    def submit_order(self, symbol: str, qty: float, side: str) -> None: ...

class MockBroker(Broker):
    def __init__(self, cash, prices=None):
        self.cash=float(cash); self.positions={}; self.prices=dict(prices or {}); self.submitted=[]
    def set_prices(self, prices): self.prices.update(prices)
    def get_equity(self):
        return self.cash + sum(sh*self.prices.get(t,0.0) for t,sh in self.positions.items())
    def get_positions(self): return dict(self.positions)
    def submit_order(self, symbol, qty, side):
        if qty <= 0: return
        p=self.prices.get(symbol)
        if not p or p<=0: raise ValueError(f"no price for {symbol}")
        signed = qty if side=="buy" else -qty
        self.cash -= signed*p
        self.positions[symbol]=self.positions.get(symbol,0.0)+signed
        if abs(self.positions[symbol])<1e-12: self.positions.pop(symbol,None)
        self.submitted.append({"symbol":symbol,"qty":qty,"side":side})
    def cancel_all_orders(self):
        return None

def compute_orders(equity, current_positions, target_weights, prices, band=0.02,
                   max_order_notional=None, min_notional=1.0):
    if equity <= 0: return []
    orders=[]
    for t in sorted(set(current_positions)|set(target_weights)):
        p=prices.get(t)
        if p is None or p<=0: continue
        tgt_w=max(0.0,float(target_weights.get(t,0.0)))
        cur=current_positions.get(t,0.0)
        cur_w=(cur*p)/equity
        if band>0.0 and abs(tgt_w-cur_w)<band: continue
        tgt_sh=tgt_w*equity/p
        delta=tgt_sh-cur
        notional=delta*p
        if max_order_notional and abs(notional)>max_order_notional:
            delta=math.copysign(max_order_notional/p, delta); notional=delta*p
        if abs(notional)<min_notional: continue
        orders.append({"symbol":t,"qty":round(abs(delta),6),"side":"buy" if delta>0 else "sell","notional":round(notional,2)})
    return orders

def rebalance_to_targets(broker, target_weights, prices, band=0.02, dry_run=True, max_order_notional=None):
    equity=broker.get_equity(); positions=broker.get_positions()
    orders=compute_orders(equity, positions, target_weights, prices, band=band, max_order_notional=max_order_notional)
    if not dry_run:
        cancel=getattr(broker,"cancel_all_orders",None)
        if callable(cancel):
            try: cancel()
            except Exception as e: print(f"  [warn] could not cancel open orders: {e}")
        for o in sorted(orders, key=lambda x: 0 if x["side"]=="sell" else 1):
            try:
                broker.submit_order(o["symbol"], o["qty"], o["side"])
            except Exception as e:
                print(f"  [order skipped] {o['side'].upper()} {o['symbol']} qty {o['qty']}: {e}")
    return orders
