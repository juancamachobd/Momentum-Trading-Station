**Task: Integrate Sentiment Filter into the Screener**

Please update `03_Screener/daily_screener.py` to use our new Intelligence Feed.

**1. Load the Sentiment Data:**
* At the beginning of the script, open and load `01b_Intelligence_Feed/current_sentiment.json` into a dictionary.

**2. Update the Screening Logic:**
* Inside your main ticker loop, before calculating momentum, look up the ticker's sentiment score in the dictionary. (If a ticker is missing from the JSON, default its score to `0` for neutral).
* **The New Rule:** If the sentiment score is **less than 0** (`< 0`), completely exclude the ticker from the watchlist. 

**3. The Execution Sequence (The Full Pipeline Run):**
Now that the pipeline is fully connected, please run the following scripts in order:
* Run `python 03_Screener/daily_screener.py` (to generate the newly sentiment-filtered watchlist).
* Run `python 04_Strategy/structure_pullback.py` (to recalculate signals for the cleaner watchlist).
* Run `python 05_Backtest/engine.py` (to see how this impacts our historical performance).

**4. Output:**
Print the updated Total Return, Max Drawdown, and Win Rate to the terminal.