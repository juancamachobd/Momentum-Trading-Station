**Task: Build the IBKR Live Execution Module**

Please create the live paper-trading execution script at `06_Execution/ibkr_trader.py`.

**1. Update Requirements:**
Update `requirements.txt` to include `ib-insync` and ensure it is installed in the `.venv`.

**2. Connection Setup:**
* Import `IB` and `MarketOrder` from `ib_insync`.
* Initialize the connection to TWS/Gateway running locally: `ib.connect('127.0.0.1', 7497, clientId=1)`. Include a `try/except` block to gracefully exit and print a warning if TWS is not open or the connection is refused.

**3. Read Live Signals:**
* The script needs to look at the signal CSVs in `04_Strategy/signals/`.
* For each CSV, read **ONLY the very last row** (which represents today's current data/closing price).
* Check the `Scale_In_Signal` column of that last row. If it is `> 0`, this stock is a valid Buy target.

**4. Portfolio Sizing & Order Execution:**
* Fetch the current account's Total Equity (Net Liquidation Value) using the `ib_insync` account summary methods.
* For each valid Buy target:
  * Calculate the target dollar allocation: `Target_$ = Total_Equity * Scale_In_Signal`
  * Calculate the number of shares to buy: `Shares = int(Target_$ / Current_Price)`
  * *Safety Guardrail:* If `Shares > 0`, construct a `MarketOrder('BUY', Shares)`.
  * Create the `Stock` contract object for the ticker (Exchange='SMART', Currency='USD').
  * Submit the order: `ib.placeOrder(contract, order)`.

**5. Output & Teardown:**
* Print a clear console log of every order placed (Ticker, Shares, Dollar Amount).
* Disconnect from IBKR cleanly at the end of the script `ib.disconnect()`.
* *Please write the script, but DO NOT run it automatically, as the user needs to ensure TWS is open first.*