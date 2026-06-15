import numpy as np
import pandas as pd
from algo_core.paper import step_forward, replay_forward, run_paper_sim
from algo_core.strategies import RSI2Reversion

def _daily(seed, n=450, drift=0.0004):
    rng=np.random.RandomState(seed)
    close=100*np.exp(np.cumsum(rng.normal(drift,0.012,n)))
    idx=pd.date_range("2018-01-01",periods=n,freq="B")
    return pd.DataFrame({"open":close,"high":close*1.005,"low":close*0.995,"close":close,"volume":1e6},index=idx)

def _data(k=4):
    return {f"T{i}":_daily(i) for i in range(k)}

def test_idempotent_per_day(tmp_path):
    data=_data()
    r1=step_forward(data, RSI2Reversion(), str(tmp_path), band=0.02)
    r2=step_forward(data, RSI2Reversion(), str(tmp_path), band=0.02)
    assert r1["status"]=="stepped"; assert r2["status"]=="up_to_date"

def test_track_record_grows_one_row_per_day(tmp_path):
    data=_data()
    rec=replay_forward(data, RSI2Reversion(), str(tmp_path), band=0.02, starting_cash=25_000.0)
    closes=pd.DataFrame({t:df["close"] for t,df in data.items()})
    assert len(rec)==len(closes); assert (rec["equity"]>0).all()

def test_forward_replay_matches_paper_sim(tmp_path):
    data=_data()
    rec=replay_forward(data, RSI2Reversion(), str(tmp_path), band=0.02, starting_cash=25_000.0)
    sim=run_paper_sim(data, RSI2Reversion(), starting_cash=25_000.0, test_frac=None, band=0.02)
    assert abs(float(rec["equity"].iloc[-1])-float(sim.equity.iloc[-1]))/float(sim.equity.iloc[-1]) < 0.005

def test_state_persists(tmp_path):
    import os
    step_forward(_data(), RSI2Reversion(), str(tmp_path), band=0.02)
    assert os.path.exists(os.path.join(str(tmp_path),"account_state.json"))
    assert os.path.exists(os.path.join(str(tmp_path),"track_record.csv"))
