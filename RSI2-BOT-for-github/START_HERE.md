# 👋 START HERE — RSI2-BOT for Complete Beginners

**Never written code? Never traded a stock? Perfect — this guide assumes you know nothing.**
You'll run everything inside a free program called **VS Code**. Follow the steps in order,
copy-paste exactly what's shown, and you'll have a working bot.

---

## First, the important promises

- 💵 **This uses PRACTICE money, not real money.** You **cannot** lose a single real dollar with
  this. It's a flight simulator for trading.
- 🐢 **It's slow on purpose.** A good day or bad day means nothing. It takes *months* before the
  results mean anything. That's normal and healthy.
- 🤖 **You don't need to understand the strategy.** You just run one command a day. The bot does
  the thinking.

What you'll need: a **Windows computer**, about **30 minutes** once, and **internet**.

A few words you'll see (don't worry, that's all they mean):
- **VS Code** = a free program for opening and running code. It's where you'll do everything.
- **Terminal** = a small typing area *inside* VS Code where you paste commands.
- **Python** = free software that actually runs the bot.
- **Broker / Alpaca** = the practice stock account the bot trades in. Free.

---

## Step 1 — Install Python (the engine that runs the bot)

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python"** button, then open the downloaded file.
3. ⚠️ **VERY IMPORTANT:** on the first screen, check the box at the bottom that says
   **"Add python.exe to PATH"**. (If you skip this, nothing else will work.)
4. Click **"Install Now"**, wait, then close the installer.

---

## Step 2 — Install VS Code (where you'll run the bot)

1. Go to **https://code.visualstudio.com**
2. Click the big **"Download for Windows"** button, then open the downloaded file.
3. Click through the installer with the default options (just keep clicking Next / Install).
4. When it finishes, open **VS Code**.
5. *(Recommended)* Install the Python helper: click the **Extensions** icon on the left bar
   (it looks like four little squares), type **Python**, and click **Install** on the one by
   Microsoft. This just helps VS Code understand Python.

---

## Step 3 — Put the bot folder somewhere easy

1. You were given a folder called **RSI2-BOT** (or a `.zip` file).
2. If it's a `.zip`: right-click it → **"Extract All"** → finish.
3. Move the **RSI2-BOT** folder to your **Desktop** so it's easy to find.

---

## Step 4 — Open the bot folder in VS Code

1. In VS Code, click the **File** menu (top-left) → **Open Folder…**
2. Find and select your **RSI2-BOT** folder, then click **Select Folder**.
3. If VS Code asks **"Do you trust the authors of the files in this folder?"**, click
   **"Yes, I trust the authors."**
4. On the left you'll now see the bot's files (bot.py, START_HERE.md, etc.). 

---

## Step 5 — Open the Terminal inside VS Code

1. Click the **Terminal** menu at the top → **New Terminal**.
   *(Shortcut: hold **Ctrl** and press the **`** key — it's just under the Esc key.)*
2. A panel opens at the bottom with some text and a blinking cursor. 🎉 **That's the Terminal.**
   This is where you paste the commands below.
3. Good news: because you opened the RSI2-BOT folder, the Terminal is **already in the right
   place** — you don't need to navigate anywhere.

> 📌 Important: you run the bot by **typing commands in this Terminal** — *not* by clicking the
> little ▶ "Run" play button at the top. The bot needs you to tell it *what* to do (check, run,
> status), and you do that by typing.

To paste into the Terminal: click in it, then **right-click** (or press Ctrl+V), and press
**Enter** to run.

---

## Step 6 — Install the bot's parts (one time only)

Paste this line into the Terminal, press **Enter**, and wait for it to finish:

```
python -m pip install -r algo_core\requirements.txt
```

Then do the same with this line:

```
python -m pip install alpaca-py
```

(Lots of text will scroll by — that's normal. When it stops and you get a fresh empty line,
it's done.)

---

## Step 7 — Get your free practice trading account

1. Go to **https://alpaca.markets** and sign up for a free account.
2. Once in, switch to **"Paper Trading"** (the practice / fake-money mode — look for a toggle or
   menu that says Paper).
3. Find the **"API Keys"** section and click **"Generate"**.
4. You'll see two codes: a **Key ID** and a **Secret Key**.
   - Copy **both** somewhere safe (like a note on your computer).
   - ⚠️ The **Secret** is shown **only once** — copy it right away.
   - 🚫 **NEVER share these codes with anyone, ever** — not in a chat, email, or with "support."
     They're like the password to your account.

---

## Step 8 — Tell the bot your codes

In the VS Code Terminal, paste these **two** lines — but replace the words in quotes with **your
own** codes from Step 7 (keep the quote marks):

```
setx ALPACA_API_KEY "PASTE-YOUR-KEY-ID-HERE"
setx ALPACA_SECRET_KEY "PASTE-YOUR-SECRET-HERE"
```

Then **fully close VS Code and open it again** (reopen the RSI2-BOT folder and a new Terminal,
Steps 4–5). This makes your codes take effect.

---

## Step 9 — Check that everything is connected

In the Terminal, paste this and press Enter:

```
python bot.py check
```

✅ You should see a box that says **"Connected and ready"**, **"Practice money (paper)"**, and
your **Account value**. If you see that, you're set!

---

## Step 10 — Run the bot 🚀

```
python bot.py run
```

The bot explains what it's doing in plain English: getting prices, deciding which stocks to hold
today, and placing the **practice** trades. When it says **DONE**, it worked.

---

## Step 11 — Check how it's doing (anytime)

```
python bot.py status
```

Shows how much your practice account is worth, your profit or loss, and which stocks you own.

---

## That's it! Your daily habit

Open VS Code, open the Terminal (Steps 4–5), and once each weekday run:

```
python bot.py run
```

Check in with `python bot.py status` whenever you like.

*(Want it to run by itself every day? That's optional — see `AUTOMATION_GUIDE.md`, or ask for
help.)*

---

## If something looks wrong (plain-English fixes)

- **"python is not recognized..."** → Python wasn't added to PATH. Re-do **Step 1** and make sure
  you check the **"Add python.exe to PATH"** box, then fully close and reopen VS Code.
- **I don't see a Terminal** → Click the **Terminal** menu → **New Terminal** (Step 5).
- **"Not connected" in Step 9** → Your codes aren't set or are the wrong type. Re-do **Step 8**,
  and make sure you used your **Paper** keys (the Key ID starts with **PK**, not AK). Remember to
  reopen VS Code after setting them.
- **A wall of scary red text** → Don't panic, nothing broke on your end. Copy the text and ask
  whoever gave you the bot for help.
- **I accidentally clicked the ▶ Run button** → No harm done. Just use the Terminal and type the
  commands instead.

---

## Remember

This is **practice money** — you can experiment freely and you cannot lose real funds. Be
patient: the bot is designed to be boring day-to-day and only shows its worth over many months.
Run it, check it now and then, and let time do the work. 🌱
