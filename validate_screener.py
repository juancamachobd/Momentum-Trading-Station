import pandas as pd
import json

print("="*70)
print("SCREENER VALIDATION REPORT")
print("="*70)

# Check Q ticker for NaN issue
print("\n1. Checking Q Ticker (showed NaN in vs SMA):")
try:
    df = pd.read_csv('02_Ingestion/data/daily/Q.csv', skiprows=3, names=['Date', 'Close', 'High', 'Low', 'Open', 'Volume'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    print(f"   Total rows: {len(df)}")
    print(f"   Last row: {df.iloc[-1]['Date'].date()}")
    sma = df['Close'].rolling(window=200).mean().iloc[-1]
    print(f"   200-day SMA: {sma}")
    print(f"   Current Price: {df['Close'].iloc[-1]}")
    if pd.isna(sma):
        print("   ⚠ WARNING: SMA is NaN - insufficient data for 200-day window")
except Exception as e:
    print(f"   ERROR: {e}")

# Check sentiment data
print("\n2. Checking Sentiment Data:")
try:
    with open('01b_Intelligence_Feed/current_sentiment.json', 'r') as f:
        sentiment = json.load(f)
    print(f"   Tickers with sentiment: {len(sentiment)}")
    print(f"   Sample: {list(sentiment.items())[:5]}")
    zero_sentiments = sum(1 for v in sentiment.values() if v == 0.0)
    print(f"   Tickers with 0.0 sentiment: {zero_sentiments}/{len(sentiment)}")
except Exception as e:
    print(f"   ERROR: {e}")

# Check watchlist for data consistency
print("\n3. Checking Watchlist Data:")
try:
    with open('03_Screener/watchlist_stats.json', 'r') as f:
        stats = json.load(f)
    
    print(f"   Total tickers: {stats['meta']['total_tickers']}")
    print(f"   Passed SMA filter: {stats['meta']['passed_sma']}")
    print(f"   Passed volume filter: {stats['meta']['passed_volume']}")
    print(f"   Final watchlist size: {stats['meta']['final_watchlist']}")
    
    # Check for NaN in watchlist
    nan_count = sum(1 for item in stats['watchlist'] if pd.isna(item.get('price_vs_sma_pct', 0)))
    print(f"   Items with NaN values: {nan_count}")
    
except Exception as e:
    print(f"   ERROR: {e}")

# Check for data format issues
print("\n4. Checking CSV Format Consistency:")
try:
    import os
    sample_files = [f for f in os.listdir('02_Ingestion/data/daily/') if f.endswith('.csv')][:5]
    for filename in sample_files:
        df = pd.read_csv(f'02_Ingestion/data/daily/{filename}', skiprows=3, names=['Date', 'Close', 'High', 'Low', 'Open', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'])
        print(f"   {filename}: {len(df)} rows, latest: {df['Date'].iloc[-1].date()}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*70)
print("VALIDATION COMPLETE")
print("="*70)
