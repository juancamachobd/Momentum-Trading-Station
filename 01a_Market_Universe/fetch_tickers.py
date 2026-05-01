import pandas as pd
import json
import requests
from io import StringIO

def fetch_tickers():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # S&P 500
    sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response_sp500 = requests.get(sp500_url, headers=headers)
    sp500_table = pd.read_html(StringIO(response_sp500.text), attrs={'id': 'constituents'}, header=0)[0]
    sp500_tickers = sp500_table['Symbol'].tolist()
    sp500_tickers = [s.replace('.', '-') for s in sp500_tickers]
    
    # NASDAQ 100
    nasdaq100_url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    response_nasdaq = requests.get(nasdaq100_url, headers=headers)
    nasdaq100_table = pd.read_html(StringIO(response_nasdaq.text), match='Ticker', header=0)[0]
    nasdaq100_tickers = nasdaq100_table['Ticker'].tolist()
    
    # Save to JSON
    with open('01a_Market_Universe/sp500_tickers.json', 'w') as f:
        json.dump(sp500_tickers, f, indent=4)
        
    with open('01a_Market_Universe/nasdaq100_tickers.json', 'w') as f:
        json.dump(nasdaq100_tickers, f, indent=4)

if __name__ == '__main__':
    fetch_tickers()
    print("Successfully fetched tickers and saved to JSON files.")
