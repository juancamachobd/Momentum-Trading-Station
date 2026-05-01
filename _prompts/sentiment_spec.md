**Task: Build the NLP Sentiment Intelligence Feed**

Please create a sentiment analysis pipeline at `01b_Intelligence_Feed/sentiment_analyzer.py`.

**1. Update Requirements:**
Update `requirements.txt` to include `nltk` (Natural Language Toolkit) and ensure it is installed in the `.venv`.

**2. Data Loading & Setup:**
* The script should read the ticker list from `01a_Market_Universe/sp500_tickers.json`.
* Initialize the NLTK VADER `SentimentIntensityAnalyzer`. (You may need to include `nltk.download('vader_lexicon')` in the script to ensure the lexicon is available).

**3. The NLP Logic:**
* Iterate through the tickers. For each ticker, use `yfinance.Ticker(symbol).news` to pull the most recent news articles.
* Extract the 'title' (headline) of each article.
* Pass each headline through the VADER analyzer to get the `compound` sentiment score.
* Calculate the **Average Compound Score** for the ticker based on its recent headlines. 

**4. Output:**
* Save the results as a JSON dictionary to `01b_Intelligence_Feed/current_sentiment.json` where the keys are the tickers and the values are their average compound sentiment scores (e.g., `{"AAPL": 0.45, "TSLA": -0.12}`).
* Print a quick terminal summary of the Top 5 most positive and Top 5 most negative stocks.
* *Please write and execute the script so the JSON file is generated.*