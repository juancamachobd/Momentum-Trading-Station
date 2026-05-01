import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

def calculate_crossover_signals(watchlist_path, data_dir, output_dir, ema_short=20, ema_long=50):
    """
    Calculate EMA crossover signals for watchlist tickers.
    
    Strategy:
    - Buy signal (1): Short EMA crosses above Long EMA (Golden Cross)
    - Sell signal (-1): Short EMA crosses below Long EMA (Death Cross)
    - Hold signal (0): No crossover
    
    Args:
        watchlist_path: Path to current_watchlist.json
        data_dir: Path to daily price data directory
        output_dir: Path to save signal CSVs
        ema_short: Short-term EMA period (default: 20)
        ema_long: Long-term EMA period (default: 50)
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Read watchlist
    if not os.path.exists(watchlist_path):
        print(f"❌ Watchlist not found at {watchlist_path}")
        return
    
    with open(watchlist_path, 'r') as f:
        tickers = json.load(f)
    
    if not tickers:
        print("❌ Watchlist is empty!")
        return
    
    print(f"Processing {len(tickers)} tickers...")
    print(f"Strategy: {ema_short}/{ema_long} EMA Crossover\n")
    
    # Statistics tracking
    stats = {
        'total_tickers': len(tickers),
        'processed': 0,
        'skipped': 0,
        'total_buy_signals': 0,
        'total_sell_signals': 0,
        'todays_buys': [],
        'todays_sells': [],
        'signals_by_ticker': {}
    }
    
    today = pd.Timestamp(datetime.now().date())
    
    for ticker in tickers:
        file_path = os.path.join(data_dir, f"{ticker}.csv")
        if not os.path.exists(file_path):
            print(f"  ⚠ {ticker}: Data file not found")
            stats['skipped'] += 1
            continue
        
        try:
            # Read CSV with correct header row
            df = pd.read_csv(file_path, skiprows=3, names=['Date', 'Close', 'High', 'Low', 'Open', 'Volume'])
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            
            # Validate sufficient data for EMA calculation
            min_required = max(ema_short, ema_long) + 1
            if len(df) < min_required:
                print(f"  ⚠ {ticker}: Insufficient data ({len(df)} < {min_required} required)")
                stats['skipped'] += 1
                continue
            
            # Calculate EMAs
            df['EMA_Short'] = df['Close'].ewm(span=ema_short, adjust=False).mean()
            df['EMA_Long'] = df['Close'].ewm(span=ema_long, adjust=False).mean()
            
            # Detect crossovers
            df['Prev_EMA_Short'] = df['EMA_Short'].shift(1)
            df['Prev_EMA_Long'] = df['EMA_Long'].shift(1)
            
            # Signal generation
            df['Signal'] = 0
            df['Signal_Type'] = 'Hold'
            
            # Buy signal (Golden Cross): Short crosses above Long
            buy_condition = (df['Prev_EMA_Short'] <= df['Prev_EMA_Long']) & (df['EMA_Short'] > df['EMA_Long'])
            df.loc[buy_condition, 'Signal'] = 1
            df.loc[buy_condition, 'Signal_Type'] = 'Buy'
            
            # Sell signal (Death Cross): Short crosses below Long
            sell_condition = (df['Prev_EMA_Short'] >= df['Prev_EMA_Long']) & (df['EMA_Short'] < df['EMA_Long'])
            df.loc[sell_condition, 'Signal'] = -1
            df.loc[sell_condition, 'Signal_Type'] = 'Sell'
            
            # Create clean output with only relevant columns
            output_df = df[['Date', 'Close', 'High', 'Low', 'Open', 'Volume', 
                           'EMA_Short', 'EMA_Long', 'Signal', 'Signal_Type']].copy()
            
            # Calculate signal statistics for this ticker
            buy_signals = int((output_df['Signal'] == 1).sum())
            sell_signals = int((output_df['Signal'] == -1).sum())
            
            # Check for today's signals
            todays_data = output_df[output_df['Date'].dt.date == today.date()]
            if len(todays_data) > 0:
                today_signal = todays_data.iloc[-1]['Signal']
                if today_signal == 1:
                    stats['todays_buys'].append(ticker)
                elif today_signal == -1:
                    stats['todays_sells'].append(ticker)
            
            stats['signals_by_ticker'][ticker] = {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'last_signal': output_df.iloc[-1]['Signal_Type'],
                'last_price': float(output_df.iloc[-1]['Close']),
                'last_ema_short': float(output_df.iloc[-1]['EMA_Short']),
                'last_ema_long': float(output_df.iloc[-1]['EMA_Long'])
            }
            
            stats['total_buy_signals'] += buy_signals
            stats['total_sell_signals'] += sell_signals
            
            # Save to CSV
            output_path = os.path.join(output_dir, f"{ticker}_signals.csv")
            output_df.to_csv(output_path, index=False)
            
            print(f"  ✓ {ticker}: {buy_signals} buys, {sell_signals} sells (Last: {output_df.iloc[-1]['Signal_Type']})")
            stats['processed'] += 1
            
        except Exception as e:
            print(f"  ❌ {ticker}: Error - {e}")
            stats['skipped'] += 1
            continue
    
    # Save statistics
    stats_path = os.path.join(output_dir, 'strategy_stats.json')
    with open(stats_path, 'w') as f:
        # Convert timestamp to string for JSON serialization
        stats_json = {
            'run_date': datetime.now().isoformat(),
            'total_tickers': stats['total_tickers'],
            'processed': stats['processed'],
            'skipped': stats['skipped'],
            'total_buy_signals': stats['total_buy_signals'],
            'total_sell_signals': stats['total_sell_signals'],
            'todays_buys': stats['todays_buys'],
            'todays_sells': stats['todays_sells'],
            'signals_by_ticker': stats['signals_by_ticker']
        }
        json.dump(stats_json, f, indent=4)
    
    # Print summary report
    print("\n" + "="*70)
    print("CROSSOVER STRATEGY SIGNALS - SUMMARY")
    print("="*70)
    print(f"\nRun Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Strategy: {ema_short}/{ema_long} EMA Crossover")
    print(f"\nProcessing Stats:")
    print(f"  Total watchlist:    {stats['total_tickers']}")
    print(f"  Successfully processed:  {stats['processed']}")
    print(f"  Skipped:            {stats['skipped']}")
    
    print(f"\nSignals Generated:")
    print(f"  Total Buy Signals:  {stats['total_buy_signals']}")
    print(f"  Total Sell Signals: {stats['total_sell_signals']}")
    
    if stats['todays_buys'] or stats['todays_sells']:
        print(f"\n🔔 TODAY'S SIGNALS ({today.strftime('%Y-%m-%d')}):")
        if stats['todays_buys']:
            print(f"  🟢 BUY:  {', '.join(stats['todays_buys'])}")
        if stats['todays_sells']:
            print(f"  🔴 SELL: {', '.join(stats['todays_sells'])}")
    else:
        print(f"\n  No signals today ({today.strftime('%Y-%m-%d')})")
    
    # Top performers
    if stats['signals_by_ticker']:
        print(f"\nTop Movers (by recent price):")
        sorted_tickers = sorted(stats['signals_by_ticker'].items(), 
                               key=lambda x: x[1]['last_price'], reverse=True)
        for ticker, data in sorted_tickers[:5]:
            print(f"  {ticker}: ${data['last_price']:.2f} | {data['last_signal']} "
                  f"| EMA {data['last_ema_short']:.2f}/{data['last_ema_long']:.2f}")
    
    print(f"\n✓ Signal files saved to: {output_dir}")
    print(f"✓ Statistics saved to: {stats_path}")
    print("="*70 + "\n")

if __name__ == '__main__':
    watchlist_path = '03_Screener/current_watchlist.json'
    data_dir = '02_Ingestion/data/daily/'
    output_dir = '04_Strategy/signals/'
    
    # Configurable EMA periods
    calculate_crossover_signals(watchlist_path, data_dir, output_dir, ema_short=20, ema_long=50)
