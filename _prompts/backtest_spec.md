**Task: Build the Historical Backtesting Engine**

Please create a robust historical backtester at `05_Backtest/engine.py`.

**1. Update Requirements:**
Update `requirements.txt` to include `matplotlib` and `seaborn` (for plotting the equity curve) and ensure they are installed in the `.venv`.

**2. Simulation Parameters:**
* **Initial Capital:** $100,000
* **Data Source:** Read all signal CSV files located in `04_Strategy/signals/`.
* **Date Range:** Sort and align all data chronologically to simulate a day-by-day portfolio walk-forward.

**3. Portfolio Logic (Daily Loop):**
* Track `Cash`, `Holdings` (shares owned per ticker), and `Total_Equity` daily.
* Calculate a 20-day EMA for each ticker to act as a trailing take-profit level.
* **Entries:** On any given day, if a ticker's `Scale_In_Signal` is `0.01` or `0.02`, use that percentage of the *current* `Total_Equity` to buy shares at the day's Closing price. (Ignore commissions/slippage for this v1 build).
* **Exits (Stop Loss):** If the `Scale_In_Signal` outputs `0.00` (our 0.886 Fib invalidation), sell all shares of that ticker at the Closing price.
* **Exits (Take Profit):** If we hold a position and the daily Closing price crosses *below* the 20-day EMA, sell all shares at the Closing price to lock in profits.

**4. Performance Metrics & Output:**
* Calculate the final **Total Return (%)**, **Maximum Drawdown (%)**, and **Win Rate**.
* Print these metrics clearly to the terminal.
* Save a chronological log of every executed trade to `05_Backtest/trade_log.csv` (Columns: Date, Ticker, Action (Buy/Sell), Shares, Price, Realized PnL).
* Plot the Portfolio Equity Curve over time and save the chart as an image to `05_Backtest/equity_curve.png`.