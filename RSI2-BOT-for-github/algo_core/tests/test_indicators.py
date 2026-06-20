import numpy as np
import pandas as pd

from algo_core.indicators import sma, ema, rsi, bollinger_bands, atr, rolling_zscore


def _series():
    return pd.Series(np.arange(1, 101, dtype=float))


def test_sma_basic():
    s = _series()
    out = sma(s, 3)
    assert np.isnan(out.iloc[1])              # warmup is NaN
    assert out.iloc[2] == 2.0                 # mean(1,2,3)
    assert out.iloc[-1] == 99.0               # mean(98,99,100)


def test_sma_is_causal():
    # changing a FUTURE value must not change a past SMA value
    s = _series()
    base = sma(s, 5).iloc[10]
    s2 = s.copy()
    s2.iloc[50] = 9999.0
    assert sma(s2, 5).iloc[10] == base


def test_rsi_bounds():
    s = pd.Series(np.random.RandomState(0).normal(100, 5, 200).cumsum())
    out = rsi(s, 14).dropna()
    assert (out >= 0).all() and (out <= 100).all()


def test_rsi_all_gains_is_100():
    s = pd.Series(np.arange(1, 50, dtype=float))   # strictly rising
    assert rsi(s, 14).dropna().iloc[-1] == 100.0


def test_bollinger_ordering():
    s = pd.Series(np.random.RandomState(1).normal(100, 3, 100))
    bb = bollinger_bands(s, 20, 2).dropna()
    assert (bb["upper"] >= bb["mid"]).all()
    assert (bb["mid"] >= bb["lower"]).all()


def test_atr_positive():
    rng = np.random.RandomState(2)
    close = pd.Series(rng.normal(100, 2, 100).cumsum() + 1000)
    df = pd.DataFrame({"high": close + 1, "low": close - 1, "close": close})
    assert (atr(df, 14).dropna() > 0).all()


def test_zscore_mean_zero():
    s = pd.Series(np.random.RandomState(3).normal(0, 1, 500))
    z = rolling_zscore(s, 50).dropna()
    assert abs(z.mean()) < 0.5
