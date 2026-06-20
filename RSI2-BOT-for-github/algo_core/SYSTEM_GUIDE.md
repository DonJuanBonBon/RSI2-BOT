# algo_core — System Guide & Status

**Last updated:** 2026-06-15 · **Tests:** 52 passing

A clean, honest, end-to-end systematic-trading pipeline: research → backtest → risk control →
paper validation → forward track record → (paper) live execution. Built by extracting the
sound ideas from the course-code catalog and rebuilding everything that was defective.

---

## 1. What we actually proved (the honest result)

The one validated edge is **RSI(2) mean-reversion** on large-cap US stocks (buy a name when
its 2-day RSI is oversold while it's above its 200-day average; exit on the bounce).

Out-of-sample, after costs, on a broad 24-name laggard-inclusive basket, cap-only risk
posture:

| Metric | Value |
|---|---|
| OOS Sharpe | ~0.59 |
| OOS CAGR | ~4.9% |
| Max drawdown | −14% (with 60% deployment cap) |
| Paper-engine parity vs backtest | PASS (<0.4% diff) |

**Honest caveats (do not forget these):**
- It's a *modest* edge (~0.59 Sharpe), not a money cannon. Real, but small.
- The basket is "survivorship-lite" — 24 names still listed today. Encouraging that the edge
  survived adding laggards, but not bulletproof.
- A second long-only edge (time-series momentum) did **not** diversify it (correlation 0.66) —
  proving you can't diversify a long-only equity edge with another. Real diversification needs
  a **market-neutral** sleeve (the documented v2 direction).
- "Validated" means the *method and execution* are sound, not that future returns are assured.

---

## 2. Architecture (what each module does)

```
algo_core/
  indicators/      causal technical indicators (no lookahead)
  strategies/      RSI2Reversion (the edge), TSMomentum (studied, not adopted), SMACross (demo)
  backtest/        portfolio engine + risk controls + metrics; ORB intraday engine (earlier work)
                   compute_target_weights / latest_target_weights  <-- the shared signal seam
  risk/            position sizing + guards
  data/            OHLCV loader, train/test + walk-forward splits, fetchers
  reporting/       colored terminal output
  paper/           PaperAccount, run_paper_sim (parity), forward logger (track record)
  live/            broker-agnostic order computation + MockBroker (tested) + AlpacaBroker
  tests/           52 tests (run: python -m pytest algo_core/tests/ -q)
  examples/        runnable scripts (below)
```

**The seam that makes live trustworthy:** `compute_target_weights` produces the target
holdings used by the backtest, the paper engine, the forward logger, AND the live order
runner. One signal source, no separate "live logic" to drift.

---

## 3. How to run it (VS Code, from the ClaudeAlgo folder)

One-time setup:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r algo_core/requirements.txt
python -m pytest algo_core/tests/ -q          # expect: 52 passed
```

**Research / validation (uses data you fetch):**
```
python algo_core/examples/fetch_daily.py            # download 20y daily for the default basket
python algo_core/examples/run_portfolio.py SPY_daily.csv <names...>   # risk-control isolation
python algo_core/examples/run_paper.py <names...>   # paper-vs-backtest parity + no-trade band
```

**Forward paper trading (run once per day to build the track record):**
```
python algo_core/examples/fetch_daily.py <names...>            # refresh data
python algo_core/examples/run_forward_paper.py <names...>      # advances 1 day, logs equity
# -> writes paper_state/track_record.csv  (your dated record)
```

**Live order planning (DRY-RUN by default, paper-only):**
```
python algo_core/examples/run_live.py <names...>                       # offline plan, no broker
python algo_core/examples/run_live.py --broker alpaca <names...>       # plan vs Alpaca paper acct
python algo_core/examples/run_live.py --broker alpaca --execute <names...>   # submit PAPER orders
```

---

## 4. Stages & current status (backtest -> paper -> live)

| Stage | Status |
|---|---|
| 1. Backtest (OOS, costs, risk controls) | DONE & validated |
| 2. Paper engine reproduces backtest (parity) | DONE — PASS on real data |
| 3. No-trade band (live realism) | DONE — cuts trade count ~60% |
| 4. Forward paper logger (track record) | DONE — ready to run daily |
| 5. Live adapter (Alpaca, paper mode) | BUILT — **unverified against live API**; test in paper first |
| 6. Real-money live | NOT started — gated behind paper validation + explicit opt-in |

---

## 5. Safety boundaries (deliberate)

- API keys come from environment variables only. The course habit of plaintext keys is banned.
- `run_live.py` is **dry-run by default**; it places nothing without `--execute`.
- `AlpacaBroker` defaults to **paper mode**. Real-money requires BOTH `allow_live=True` and env
  `ALPACA_ALLOW_LIVE=YES` — and even then `run_live.py` won't trigger it.
- No real-money trading until: forward paper tracks the backtest for a meaningful period, the
  Alpaca adapter is proven in paper mode, and per-order / daily-loss guardrails are added.

---

## 6. What's next (in order)

1. **Run the forward paper logger daily** (or schedule it) to accumulate a real track record.
2. Validate the **Alpaca adapter in paper mode** with tiny size; confirm fills match intent.
3. Add live guardrails (max position, daily-loss kill-switch) before any real money.
4. Build the **market-neutral v2 edge** for genuine diversification (the data showed long-only
   can't diversify long-only).
5. Once a real, dated track record exists, pursue third-party verification (the asset for the
   sell/raise goal).

This document is the checkpoint. The system is honest, tested end-to-end, and ready to start
generating a forward track record.
