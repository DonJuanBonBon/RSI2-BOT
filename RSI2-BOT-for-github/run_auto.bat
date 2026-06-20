@echo off
REM RSI2-BOT unattended daily run. Point Windows Task Scheduler at THIS file.
REM Runs once: refresh data -> advance paper record -> place Alpaca PAPER orders.
REM All output is appended to paper_state\auto_log.txt with timestamps.

cd /d "%~dp0"
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate
if not exist data mkdir data
if not exist paper_state mkdir