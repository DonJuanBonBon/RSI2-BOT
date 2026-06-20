"""
Strategy base class.

A Strategy turns an OHLCV DataFrame into a `position` Series: the TARGET weight per bar,
decided using information up to and including that bar. The backtest engine applies the
one-bar execution lag, so strategies express intent, not timing tricks.

Contract:
  generate_signals(df) -> pd.Series indexed like df, values typically in [-1, 1].
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    name: str = "strategy"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return target-position weights aligned to df.index."""
        raise NotImplementedError

    def __repr__(self) -> str:
        params = ", ".join(f"{k}={v}" for k, v in vars(self).items())
        return f"{self.__class__.__name__}({params})"
