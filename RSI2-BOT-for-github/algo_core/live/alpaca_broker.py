from __future__ import annotations
import os
from .broker import Broker

class AlpacaBroker(Broker):
    def __init__(self, paper: bool = True, allow_live: bool = False):
        key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_SECRET_KEY")
        if not key or not secret:
            raise RuntimeError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables (use your PAPER keys).")
        if not paper:
            if not (allow_live and os.getenv("ALPACA_ALLOW_LIVE") == "YES"):
                raise RuntimeError("Refusing LIVE trading. Use paper=True, or set allow_live=True AND environment ALPACA_ALLOW_LIVE=YES to override (not recommended yet).")
        try:
            from alpaca.trading.client import TradingClient
        except ImportError as e:
            raise RuntimeError("alpaca-py not installed. Run: pip install alpaca-py") from e
        self._client = TradingClient(key, secret, paper=paper)
        self.paper = paper

    def account_info(self) -> dict:
        a = self._client.get_account()
        return {"status": str(getattr(a,"status","")), "equity": float(a.equity),
                "cash": float(a.cash), "buying_power": float(a.buying_power),
                "account_number": str(getattr(a,"account_number","")),
                "pattern_day_trader": bool(getattr(a,"pattern_day_trader",False)),
                "trading_blocked": bool(getattr(a,"trading_blocked",False)), "paper": self.paper}

    def is_market_open(self) -> bool:
        return bool(self._client.get_clock().is_open)

    def get_equity(self) -> float:
        return float(self._client.get_account().equity)

    def get_positions(self) -> dict:
        return {p.symbol: float(p.qty) for p in self._client.get_all_positions()}

    def submit_order(self, symbol: str, qty: float, side: str) -> None:
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        qty = round(float(qty), 6)
        if qty <= 0: return
        if side == "sell":
            held = 0.0
            try:
                pos = self._client.get_open_position(symbol); held = float(pos.qty)
            except Exception:
                held = 0.0
            if held <= 0: return
            sell_qty = min(qty, held)
            if sell_qty >= held - 1e-9:
                self._client.close_position(symbol); return
            req = MarketOrderRequest(symbol=symbol, qty=round(sell_qty,6), side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
        else:
            req = MarketOrderRequest(symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
        self._client.submit_order(order_data=req)
