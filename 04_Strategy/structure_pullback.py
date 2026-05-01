import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import os
import json

def get_swing_points(data, order=5):
    """Detects swing highs and lows with a rolling, backward-looking window."""
    highs = argrelextrema(data['High'].values, np.greater, order=order)[0]
    lows = argrelextrema(data['Low'].values, np.less, order=order)[0]
    return highs, lows

def calculate_ichimoku(df):
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['Tenkan_Sen'] = (high_9 + low_9) / 2

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['Kijun_Sen'] = (high_26 + low_26) / 2

    df['Senkou_Span_A'] = ((df['Tenkan_Sen'] + df['Kijun_Sen']) / 2).shift(26)
    
    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['Senkou_Span_B'] = ((high_52 + low_52) / 2).shift(26)
    
    return df

def run_strategy():
    # Load tickers
    watchlist_path = '03_Screener/current_watchlist.json'
    if not os.path.exists(watchlist_path):
        return

    with open(watchlist_path, 'r') as f:
        tickers = json.load(f)

    for ticker in tickers:
        data_path = f'02_Ingestion/data/daily/{ticker}.csv'
        if not os.path.exists(data_path):
            continue

        # Reset index to make Date a column if it's in the index
        # Skip header rows
        df = pd.read_csv(data_path, skiprows=3)
        # Manually set the column names based on the file header, ignoring the first column (Price)
        df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        
        # 1. Market Structure (Weekly)
        df_weekly = df.resample('W').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        
        # Simple rolling lookback for structure
        highs, lows = get_swing_points(df_weekly, order=5)
        
        if len(highs) < 2 or len(lows) < 2:
            continue
            
        last_high = df_weekly.iloc[highs[-1]]['High']
        prev_high = df_weekly.iloc[highs[-2]]['High']
        last_low = df_weekly.iloc[lows[-1]]['Low']
        prev_low = df_weekly.iloc[lows[-2]]['Low']
        
        is_bullish = (last_high > prev_high) and (last_low > prev_low)
        
        if not is_bullish:
            continue

        # 2. Indicators
        df['SMA50'] = df['Close'].rolling(50).mean()
        df['SMA100'] = df['Close'].rolling(100).mean()
        df['SMA200'] = df['Close'].rolling(200).mean()
        df = calculate_ichimoku(df)
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR14'] = true_range.rolling(14).mean()
        
        # 3. Fibs
        diff = last_high - last_low
        fib_0786 = last_high - (0.786 * diff)
        fib_0886 = last_high - (0.886 * diff)
        
        # 4. Gann
        gann_levels = []
        sqrt_low = np.sqrt(last_low)
        for n in [0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.25]:
            gann_levels.append((sqrt_low + n)**2)
            
        # 5. Confluence
        # Zone Width = 0.5 * ATR(14)
        def check_confluence(price, row):
            atr = row['ATR14'] * 0.5
            elements = [
                row['SMA50'], row['SMA100'], row['SMA200'],
                row['Senkou_Span_A'], row['Senkou_Span_B'],
                fib_0786, fib_0886
            ] + gann_levels
            
            count = 0
            for el in elements:
                if abs(price - el) <= atr:
                    count += 1
            return count

        df['Confluence_Count'] = df.apply(lambda row: check_confluence(row['Close'], row), axis=1)
        
        # 6. Scale-in Logic
        def get_signal(row):
            if row['Close'] < fib_0886:
                return 0.00
            if row['Confluence_Count'] == 3:
                return 0.04
            if row['Confluence_Count'] == 4:
                return 0.07
            if row['Confluence_Count'] >= 5:
                return 0.10
            return 0.00
            
        df['Scale_In_Signal'] = df.apply(get_signal, axis=1)
        df['Market_Structure_Bullish'] = is_bullish
        
        # 7. Save
        output_dir = '04_Strategy/signals/'
        os.makedirs(output_dir, exist_ok=True)
        df.to_csv(f'{output_dir}{ticker}_signals.csv')

if __name__ == '__main__':
    run_strategy()
