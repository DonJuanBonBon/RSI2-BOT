# Steps 1 & 2 — Forward Paper Record + Alpaca Paper Connection

This is the bridge from backtest to a real broker connection. **Golden rule: paper only.**
Do every step in order. Do not skip to live trading.

Prereqs (one time, in the project folder):
```
python -m venv .venv
.venv\Scripts\activate
pip install -r algo_core/requirements.txt
python -m pytest algo_core/tests/ -q        # expect: all passed
```

---

## STEP 1 — Build the forward paper track record (start TODAY)

The earlier you start, the sooner you have a meaningful record. It needs internet (Yahoo data)
and runs entirely as a simulation — no broker, no risk.

### Daily routine (after the US market close)
```
python algo_core/examples/run_daily.py
```
This refreshes data for the 24-name basket, advances the simulated account one day, and appends
to `paper_state/track_record.csv`. It is idempotent — running twice the same day does nothing.

Check how it's doing anytime:
```
python algo_core/examples/show_track_record.py
```

### Optional: automate it (Windows Task Scheduler)
1. Create a file `run_daily.bat` in the project folder:
   ```bat
   @echo off
   cd /d "%~dp0"
   call .venv\Scripts\activate
   python algo_core\examples\run_daily.py >> paper_state\daily_log.txt 2>&1
   ```
2. Open Task Scheduler → Create Basic Task → Daily → time ~5:30 PM your time (after the
   4 PM ET close) → Action: Start a program → point it at `run_daily.bat`.
3. It will quietly extend your track record every weekday. (Weekends/holidays just no-op.)

### What to expect
A few weeks proves the pipeline. **Months** are what make the record meaningful. Expect modest
numbers and idle cash on many days — that's the strategy, not a bug.

---

## STEP 2 — Connect to Alpaca PAPER (validate execution)

Goal: prove the live order loop works against a real broker API, with fake money, before any
real money ever. Do these sub-steps in order and stop if anything looks wrong.

### 2a. Create the account + paper keys
1. Sign up free at https://alpaca.markets.
2. Switch to the **Paper Trading** dashboard (toggle in the UI).
3. Generate **paper** API keys (API Keys panel). Copy the Key ID and the Secret (shown once).

### 2b. Install the SDK + set credentials
```
pip install alpaca-py
```
Set environment variables. For the current PowerShell session:
```
$env:ALPACA_API_KEY="your_paper_key_id"
$env:ALPACA_SECRET_KEY="your_paper_secret"
```
To persist across reboots: System Properties → Environment Variables → add both as User
variables (or use `setx`). Never put keys in a .py file or commit them.

### 2c. Preflight — read-only connection test (NO orders)
```
python algo_core/examples/check_alpaca.py
```
Expect: `Connection: OK`, Mode PAPER, status ACTIVE, your paper equity (usually $100,000), and
your positions (none at first). If it errors, fix credentials before going further. This step
cannot place an order.

### 2d. Dry-run — see the planned orders (still NO orders sent)
First make sure data is fresh (run Step 1's `run_daily.py` today), then:
```
python algo_core/examples/run_live.py --broker alpaca AAPL_daily.csv MSFT_daily.csv NVDA_daily.csv AMZN_daily.csv GOOGL_daily.csv META_daily.csv JPM_daily.csv JNJ_daily.csv PG_daily.csv KO_daily.csv HD_daily.csv WMT_daily.csv UNH_daily.csv MA_daily.csv INTC_daily.csv VZ_daily.csv PFE_daily.csv DIS_daily.csv NKE_daily.csv BA_daily.csv T_daily.csv F_daily.csv CSCO_daily.csv IBM_daily.csv
```
It prints the target holdings and the exact orders it *would* place. Read them. Nothing is sent
(dry-run is the default).

### 2e. First real PAPER order — small and controlled
Run the SAME command with `--execute` added. Best practice for the very first time: do it while
the **market is open** (so you see immediate fills), and consider starting with just a couple of
tickers to watch one or two orders go through:
```
python algo_core/examples/run_live.py --broker alpaca --execute AAPL_daily.csv MSFT_daily.csv
```
Then check the Alpaca paper dashboard — you should see the orders/fills. Re-run
`check_alpaca.py` to see the new positions.

### 2f. Reconcile
Confirm the positions Alpaca shows match the target weights the bot intended (within the 2%
no-trade band). If they line up, the execution path is validated.

### Safety gates (do not cross yet)
- Everything above is PAPER (fake money). Keep it that way for a meaningful period.
- `run_live.py` never sends without `--execute`. `AlpacaBroker` never goes live without an
  explicit `allow_live=True` AND `ALPACA_ALLOW_LIVE=YES` — leave those alone.
- Before ANY real money (months away): add the live guardrails (daily-loss kill-switch, max
  position) — that is Step 4 from the priority list, not now.

### Timing note
RSI(2) decides on the day's close and holds into the next session. Run `run_daily.py` and the
Alpaca execute step after the close; market orders submitted while closed queue for the next
open — which matches the backtest's one-day execution lag.

### Troubleshooting
- "Missing credentials" → env vars not set in this terminal session.
- "alpaca-py not installed" → `pip install alpaca-py`.
- API call fails after connecting → keys are wrong, or live keys used on the paper endpoint;
  regenerate PAPER keys.
- Orders rejected when market closed → expected for some checks; they queue for next open.
