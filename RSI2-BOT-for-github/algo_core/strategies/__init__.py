"""Strategy base + the one strategy this bot trades."""
from .base import Strategy
from .mean_reversion_rsi2 import RSI2Reversion
__all__ = ["Strategy", "RSI2Reversion"]
