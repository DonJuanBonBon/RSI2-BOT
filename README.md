RSI2-BOT — RSI paper-trading bot
An automated paper-trading bot you run from one file. It practices a documented stock strategy (RSI-2 mean-reversion) on 24 large-cap US stocks using a free practice account. It uses fake (paper) money only — no real funds, ever.

👉 New here? Start with these two files (in order)
START_HERE.md — the complete beginner setup, written for someone who has never coded. It walks you through installing the tools, opening the bot in VS Code, connecting a free broker, and running it. Read this first.
AUTOMATION_GUIDE.md — once it's working, this shows how to make the bot run itself every weekday automatically (optional).
That's all you need. Everything else below is just context.

What it does, in plain English
Each weekday it checks 24 big-name stocks for ones that have dipped (gone "oversold").
It buys those in your practice account and sells them when they bounce back.
It tracks how the practice account is doing over time.
Type python bot.py help anytime to see the commands.

Honest expectations
This is a real but modest strategy. It will be boring day to day.
Results only mean something after months — not days. Be patient.
It is for learning and practice. Nothing here is financial advice, and it is not a promise of profit.
Safety
Uses paper (practice) money by default. Live/real-money trading is intentionally locked.
Never commit your API keys. They live in environment variables on your own computer, not in these files. The included .gitignore keeps your keys, your trading record, and other personal files out of the repository.
For the curious (optional reading)
algo_core/SYSTEM_GUIDE.md — how the system works and how it was validated.
algo_core/STEP_1_2_GUIDE.md and algo_core/examples/PAPER_TO_LIVE.md — broker setup and the careful path toward (someday) live trading.
python bot.py test — runs the built-in self-checks.
