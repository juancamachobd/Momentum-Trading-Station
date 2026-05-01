**Task: Secure IBKR Configuration with Environment Variables**

Please update our environment and the execution script to use secure `.env` variables.

**1. Create the `.env` File:**
* Create a file named `.env` in the root directory of the project.
* Add the following default variables into the file:
  `IBKR_HOST=127.0.0.1`
  `IBKR_PORT=7497`
  `IBKR_ACCOUNT=YOUR_PAPER_ACCOUNT_ID`

**2. Verify `.gitignore`:**
* Ensure that `.env` is explicitly listed inside our `.gitignore` file so it never gets committed to version control.

**3. Update `ibkr_trader.py`:**
* Update `06_Execution/ibkr_trader.py` to import `os` and `load_dotenv` from `dotenv`.
* Call `load_dotenv()` at the top of the script.
* Replace the hardcoded connection details with `os.environ.get('IBKR_HOST')` and `int(os.environ.get('IBKR_PORT'))`.
* When fetching the account summary or placing orders, explicitly use the `IBKR_ACCOUNT` variable if necessary to route the orders correctly.