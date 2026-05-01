**Task: Build the Data Ingestion Pipeline for the S&P 500**

**1. Update Requirements:**
Please ensure `yfinance`, `lxml`, and `html5lib` are added to `requirements.txt` (we need the latter two for pandas to scrape web tables).

**2. Fetch the Market Universe:**
Create a script at `01a_Market_Universe/fetch_tickers.py`. This script should:
* Use `pandas.read_html` to scrape the S&P 500 ticker symbols directly from the Wikipedia page: `https://en.wikipedia.org/wiki/List_of_S%26P_500_companies`.
* Clean the symbols (some Wikipedia tickers use a dot like "BRK.B", which Yahoo Finance expects as a hyphen "BRK-B").
* Save the cleaned list as a JSON array to `01a_Market_Universe/sp500_tickers.json`.

**3. Build the Historical Downloader:**
Create a script at `02_Ingestion/historical_downloader.py`. This script should:
* Read the `sp500_tickers.json` file.
* Ensure the directory `02_Ingestion/data/daily/` exists.
* Use `yfinance` to download the last **3 years** of daily data for each ticker in the JSON file.
* Save each downloaded dataframe as a CSV (e.g., `AAPL.csv`) inside `02_Ingestion/data/daily/`.
* Include basic `try/except` error handling so that if one ticker fails to download (e.g., due to a delisting or API timeout), the loop continues to the next ticker without crashing.
* Please write the code, and then **execute both scripts** so my environment actually downloads the CSV files.

***