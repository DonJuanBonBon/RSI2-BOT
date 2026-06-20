from __future__ import annotations
import json, os
import pandas as pd
from .account import PaperAccount
from ..backtest.portfolio import compute_target_weights

def _paths(state_dir):
    return (os.path.join(state_dir,"account_state.json"), os.path.join(state_dir,"track_record.csv"))

def _load_state(state_path, starting_cash):
    if os.path.exists(state_path):
        with open(state_path) as fh: st=json.load(fh)
        return float(st["cash"]), {k:float(v) for k,v in st.get("positions",{}).items()}, st.get("last_date")
    return float(starting_cash), {}, None

def step_forward(price_data, strategy, state_dir, starting_cash=25_000.0, max_weight=0.20,
                 max_total_deployment=0.60, slippage_bps=5.0, band=0.02, market=None, regime_sma=200):
    os.makedirs(state_dir, exist_ok=True)
    state_path, record_path = _paths(state_dir)
    cash, positions, last_date = _load_state(state_path, starting_cash)
    acct = PaperAccount(cash=cash, positions=positions)
    regime_close = market["close"] if market is not None else None
    target, closes = compute_target_weights(price_data, strategy, max_weight, max_total_deployment, regime_close, regime_sma)
    if len(closes)==0: return {"status":"no_data"}
    latest = closes.index[-1]
    if last_date is not None and pd.Timestamp(latest) <= pd.Timestamp(last_date):
        return {"status":"up_to_date","date":str(pd.Timestamp(latest).date())}
    prices = closes.loc[latest].to_dict()
    equity = acct.mark_to_market(prices)
    prev_equity=None
    if os.path.exists(record_path):
        try: prev_equity=float(pd.read_csv(record_path)["equity"].iloc[-1])
        except Exception: prev_equity=None
    daily_ret=(equity/prev_equity-1.0) if prev_equity else 0.0
    cost_rate=slippage_bps/10_000.0
    acct.rebalance_to(target.loc[latest].to_dict(), prices, cost_rate, date=latest, band=band)
    deployed=sum(s*prices.get(t,0.0) for t,s in acct.positions.items())
    deployment=deployed/equity if equity>0 else 0.0
    with open(state_path,"w") as fh:
        json.dump({"cash":acct.cash,"positions":acct.positions,"last_date":pd.Timestamp(latest).isoformat()}, fh)
    row=pd.DataFrame([{"date":pd.Timestamp(latest).date(),"equity":round(equity,2),"cash":round(acct.cash,2),"deployment_pct":round(deployment*100,1),"n_positions":len(acct.positions),"daily_return_pct":round(daily_ret*100,3)}])
    row.to_csv(record_path, mode="a", header=not os.path.exists(record_path), index=False)
    targets={t:round(float(w),4) for t,w in target.loc[latest].items() if w>0}
    return {"status":"stepped","date":str(pd.Timestamp(latest).date()),"equity":round(equity,2),"n_positions":len(acct.positions),"targets":targets}

def replay_forward(price_data, strategy, state_dir, **kwargs):
    closes=pd.DataFrame({t:df["close"] for t,df in price_data.items()}).sort_index()
    for d in closes.index:
        sub={t:df.loc[df.index<=d] for t,df in price_data.items()}
        step_forward(sub, strategy, state_dir, **kwargs)
    _, record_path=_paths(state_dir)
    return pd.read_csv(record_path)
