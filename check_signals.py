import pandas as pd
import os
from datetime import datetime

signals_dir = '04_Strategy/signals/'

latest_signals = []

for filename in os.listdir(signals_dir):
    if filename.endswith('_signals.csv'):
        ticker = filename.split('_')[0]
        df = pd.read_csv(os.path.join(signals_dir, filename))
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Get the latest signals
        latest = df.iloc[-1]
        
        latest_signals.append({
            'Ticker': ticker,
            'Date': latest['Date'],
            'Close': latest['Close'],
            'Signal_Type': latest['Signal_Type']
        })

signals_df = pd.DataFrame(latest_signals).sort_values('Date', ascending=False)

# Get summary
print('\n' + '='*80)
print('LATEST SIGNALS ACROSS ALL TICKERS')
print('='*80)
print(f'\nTotal Tickers: {len(signals_df)}')
print(f'Latest Signal Date: {signals_df["Date"].max()}')
print(f'\nSignal Distribution:')
print(signals_df['Signal_Type'].value_counts())
print('\n' + '-'*80)
print('\nMost Recent Signals (Top 15):')
print('-'*80)
print(signals_df.head(15)[['Ticker', 'Date', 'Close', 'Signal_Type']].to_string(index=False))

# Show Buy signals if any
print('\n' + '='*80)
buy_signals = signals_df[signals_df['Signal_Type'] == 'Buy']
if len(buy_signals) > 0:
    print(f'ACTIVE BUY SIGNALS: {len(buy_signals)}')
    print('='*80)
    print(buy_signals[['Ticker', 'Date', 'Close']].to_string(index=False))
else:
    print('NO ACTIVE BUY SIGNALS CURRENTLY')
    print('='*80)
    print('\nLatest signal states:')
    signal_counts = signals_df['Signal_Type'].value_counts()
    for signal_type, count in signal_counts.items():
        print(f'  {signal_type}: {count} tickers')
