# Backtest → Paper → Live: the transition path

The whole package is designed so the **signal logic never gets rewritten** as you move from
backtesting to paper trading to live trading. Only the *data source* and the *order
destination* change. That is what keeps live behavior matching the backtest.

## The single source of truth

```
algo_core/backtest/portfolio.py
    compute_target_weights(...)   <- the rules (used BY the backtest)
    latest_target_weights(...)    <- today's targets (used BY paper/live)
```

Backtest and live call the *same* function. There is no separate "live strategy" to drift.

## Stage 1 — Backtest (DONE)
- `run_portfolio.py` evaluates the rules out-of-sample with risk controls.
- Decision gate: only proceed if the OOS result is acceptable (Sharpe holds, drawdown
  controlled) on a broad, laggard-inclusive basket.

## Stage 2 — Paper trading (NEXT, after we're satisfied with Stage 1)
Run once per day after the close:
1. Update daily data (`fetch_daily.py`).
2. `run_today.py` prints the TARGET weights for the next session.
3. A paper-broker adapter (to build) places **simulated** orders to move the account toward
   those targets, and logs fills + equity.
4. Compare the paper equity curve to the backtest's expectation. They should track. If paper
   diverges badly from backtest, STOP — there is a data/timing/execution bug to fix before
   any real money.

What Stage 2 validates: **execution plumbing**, not the edge (the backtest already tested the
edge). Data timing, order rounding, slippage realism, corporate actions, and operational
discipline are what break first.

## Stage 3 — Live trading (LAST, only after paper proves out)
- Swap the paper-broker adapter for a real broker adapter (e.g. Alpaca: commission-free US
  stocks, clean API). Same `latest_target_weights` call; only the order router changes.
- Start with the smallest size possible. Treat the first months as continued validation.
- Keep a verified, time-stamped track record from day one (this is the asset that matters for
  the sell/raise goal).

## Safety boundaries (deliberate)
- `run_today.py` NEVER places orders. It only prints targets.
- The live adapter will be a separate, explicitly-invoked component with its own guardrails
  (max position, kill-switch, daily loss limit) before it is allowed to send a single order.
- No live trading until: (a) Stage 1 OOS is acceptable, (b) Stage 2 paper tracks the backtest
  for a meaningful period, (c) risk guardrails are in place and tested.

## Current status
- Stage 1: in progress (risk controls just added; broaden + validate next).
- Stage 2: not started. The seam (`latest_target_weights`, `run_today.py`) is ready for it.
- Stage 3: not started.
