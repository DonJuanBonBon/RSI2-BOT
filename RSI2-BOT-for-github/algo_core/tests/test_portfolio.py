import numpy as np
import pandas as pd
from algo_core.backtest import (PortfolioBacktester, latest_target_weights,
                                compute_target_weights)
from algo_core.strategies import RSI2Reversion


def _daily(seed, n=900, drift=0.0003):
    rng = np.random.RandomState(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(drift, 0.012, n)))
    idx = pd.date_range("2016-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": close, "high": close*1.005, "low": close*0.995,
                         "close": close, "volume": 1e6}, index=idx)


def _data(k=6):
    return {f"T{i}": _daily(i) for i in range(k)}


def test_deployment_never_exceeds_one():
    res = PortfolioBacktester(max_weight=0.2).run(_data(), RSI2Reversion())
    assert (res.deployment <= 1.0 + 1e-9).all()


def test_per_name_weight_cap_respected():
    res = PortfolioBacktester(max_weight=0.2).run(_data(8), RSI2Reversion())
    assert res.weights.abs().max().max() <= 0.2 + 1e-9


def test_total_deployment_cap_respected():
    res = PortfolioBacktester(max_weight=0.2, max_total_deployment=0.5).run(_data(8), RSI2Reversion())
    assert res.deployment.max() <= 0.5 + 1e-9


def test_deployment_cap_lowers_or_equals_exposure():
    data = _data(8)
    full = PortfolioBacktester(max_total_deployment=1.0).run(data, RSI2Reversion())
    capped = PortfolioBacktester(max_total_deployment=0.5).run(data, RSI2Reversion())
    assert capped.metrics["avg_deployment"] <= full.metrics["avg_deployment"] + 1e-9


def test_regime_filter_flattens_in_bear():
    data = _data(5)
    base = next(iter(data.values()))
    n = len(base)
    down = pd.Series(np.linspace(400, 100, n), index=base.index)
    market = pd.DataFrame({"close": down, "open": down, "high": down, "low": down, "volume": 1e6})
    res = PortfolioBacktester(max_total_deployment=0.6).run(data, RSI2Reversion(), market=market)
    assert res.deployment.sum() == 0.0


def test_latest_target_weights_shape():
    w = latest_target_weights(_data(6), RSI2Reversion(), max_total_deployment=0.6)
    assert isinstance(w, dict)
    assert all(0 < v <= 0.2 + 1e-9 for v in w.values())
    assert sum(w.values()) <= 0.6 + 1e-9


def test_test_frac_shortens_sample():
    data = _data(6)
    full = PortfolioBacktester().run(data, RSI2Reversion())
    oos = PortfolioBacktester().run(data, RSI2Reversion(), test_frac=0.3)
    assert oos.metrics["n_bars"] < full.metrics["n_bars"]
