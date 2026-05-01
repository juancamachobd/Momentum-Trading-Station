**Task: Build and Execute the Daily Momentum Screener**

Please create a script at `03_Screener/daily_screener.py` that bridges our ingested data with our strategy logic.

**1. Data Loading:**
* The script should look inside the `02_Ingestion/data/daily/` folder.
* Iterate through all the CSV files downloaded in the previous step.

**2. Screening Logic:**
For each ticker, calculate the following using pandas:
* **Macro Trend Filter:** Calculate the 200-day Simple Moving Average (SMA). The current closing price MUST be greater than the 200-day SMA. If it's below, discard the ticker.
* **Liquidity Filter:** Calculate the 20-day Average Daily Volume. The volume MUST be greater than 1,000,000 shares to ensure we don't get trapped in illiquid, choppy moves.
* **Momentum Ranking:** For the stocks that pass the first two filters, calculate their 90-day Rate of Change (ROC). 

**3. Output:**
* Sort the surviving stocks by their 90-day ROC from highest to lowest.
* Take the **Top 30** tickers.
* Save this finalized list of tickers as a JSON array to `03_Screener/current_watchlist.json`. (Note: This is the exact file that `04_Strategy/structure_pullback.py` is waiting to read).

**4. Execution:**
Once the code is written, please run the script in the terminal so the `current_watchlist.json` file is actually generated based on our newly downloaded data.