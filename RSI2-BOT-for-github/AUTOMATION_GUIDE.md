# 🤖 Make the Bot Run Itself (plain-English guide)

By default, *you* run the bot once a day by typing `python bot.py run`. This guide sets up your
computer to do that **for you, automatically, every weekday** — so you can leave it alone.

It still uses **practice money only**. And it still runs **once per day** — that's all this bot
needs (it makes one decision a day, so running it more often would do nothing).

---

## Before you start (do these first)

1. ✅ You've finished `START_HERE.md` and the bot works when you type `python bot.py run`
   yourself. **Don't automate something that isn't working yet.**
2. ✅ Your Alpaca keys are saved permanently. (In `START_HERE.md` Step 8 you used `setx` — that
   saves them for good, which is exactly what the automatic runner needs.)
3. ✅ Your computer will be **turned on and signed in** at the time you pick each day. If the
   computer is off or asleep, the bot can't run (it'll catch up the next time you turn it on).

---

## What you'll set up

Windows has a built-in tool called **Task Scheduler** — think of it as an alarm clock for
programs. You'll tell it: *"every weekday at this time, run the bot."* It will then run a small
file we already made for you called **`run_auto.bat`**, which does the daily run and saves a log.

---

## Step-by-step

### 1. Open Task Scheduler
- Click the **Start** menu, type **Task Scheduler**, and press Enter.

### 2. Start a new task
- On the right side, click **"Create Basic Task…"**

### 3. Name it
- Name: type **RSI2-BOT daily**
- Click **Next**.

### 4. Pick how often
- Choose **Daily**, click **Next**.
- Pick a **start time**. Two good choices:
  - **9:00 AM** — runs in the morning before the market opens, or
  - **5:00 PM** — runs in the evening after the market closes.
- Either is fine. Click **Next**.

### 5. Tell it what to run
- Choose **"Start a program"**, click **Next**.
- Click **Browse…**, then find and select this file:
  `RSI2-BOT\run_auto.bat` (it's inside your bot folder).
- Click **Next**.

### 6. Finish
- Click **Finish**. Done — the bot is now scheduled.

### 7. (Recommended) One small tweak so it catches up after your PC was off
- In Task Scheduler, find **RSI2-BOT daily** in the middle list, right-click it → **Properties**.
- Go to the **Settings** tab.
- Check the box **"Run task as soon as possible after a scheduled start is missed."**
- Click **OK**.

---

## Test it right now (don't wait a day to find out)

- In Task Scheduler, right-click **RSI2-BOT daily** → click **Run**.
- Wait a few seconds, then open this file in your bot folder:
  `paper_state\auto_log.txt`
- You should see a fresh entry with today's date showing prices fetched and trades placed. ✅
  If it looks clean (no "not installed" or "not set" messages), your automation works.

---

## How to check on it later

You don't have to do anything daily anymore. Whenever you're curious, open VS Code and run:

```
python bot.py status
```

Or just open `paper_state\auto_log.txt` to read the history of every automatic run.

---

## If something looks wrong

- **The log shows "not connected" or "keys not set"** → your keys weren't saved permanently.
  Redo Step 8 in `START_HERE.md` using `setx`, then test again.
- **The log shows "couldn't get prices"** → the computer had no internet at run time. It'll work
  on the next run.
- **Nothing happened at the scheduled time** → your computer was off, asleep, or signed out. Turn
  it on / sign in; if you did Step 7 above, it will catch up automatically.
- **You want it to run on a