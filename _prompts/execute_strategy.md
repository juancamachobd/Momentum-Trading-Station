**Task: Execute the Strategy Engine**

Now that `03_Screener/current_watchlist.json` has been generated, please run our strategy engine.

**1. Execution:**
* Ensure your terminal is using the `.venv` Python environment.
* Run `python 04_Strategy/structure_pullback.py`. 

**2. Verification:**
* The script should process the 30 tickers in the watchlist.
* Verify that it outputs individual CSV files (e.g., `AAPL_signals.csv`) into the `04_Strategy/signals/` folder.
* If the script encounters any `ModuleNotFoundError` (such as `scipy`, which we added to requirements earlier but may not have actively pip-installed yet), please install the missing dependency, freeze it to `requirements.txt`, and rerun the script until it completes successfully.