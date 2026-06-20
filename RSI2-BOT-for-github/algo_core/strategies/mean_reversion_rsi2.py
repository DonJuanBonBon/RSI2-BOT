"""Connors-style RSI(2) mean-reversion (long-only). Causal by construction."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .base import Strategy
from ..indicators import rsi, sma


class RSI2Reversion(Strategy):
    name = "rsi2_reversion"

    def __init__(self, rsi_period: int = 2, rsi_buy: float = 10.0,
                 trend_sma: int = 200, exit_sma: int = 5):
        if rsi_period < 1 or trend_sma < 1 or exit_sma < 1:
            raise ValueError("periods must be >= 1")
        self.rsi_period = rsi_period
        self.rsi_buy = float(rsi_buy)
        self.trend_sma = trend_sma
        self.exit_sma = exit_sma

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        r = rsi(close, self.rsi_period).values
        trend = sma(close, self.trend_sma).values
        exit_ma = sma(close, self.exit_sma).values
        c = close.values
        out = np.zeros(len(df))
        holding = False
        for i in range(len(df)):
            if np.isnan(trend[i]) or np.isnan(r[i]) or np.isnan(exit_ma[i]):
                holding = False
                out[i] = 0.0
                continue
            if not holding:
                if c[i] > trend[i] and r[i] < self.rsi_buy:
                    holding = True
                    out[i] = 1.0
                else:
                    out[i] = 0.0
            else:
                if c[i] > exit_ma[i]:
                    holding = False
                    out[i] = 0.0
                else:
                    out[i] = 1.0
        return pd.Series(out, index=df.index, name="position")
