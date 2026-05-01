import pandas as pd
import os
import json

def run_screener(sma_window=200, min_volume=1000000, top_n=30, min_history=90):
    """
    Daily stock screener with configurable thresholds.
    
    Filters:
    1. Positive sentiment (or neutral if sentiment unavailable)
    2. Price above 200-day SMA (uptrend)
    3. 20-day avg volume > 1M shares (liquidity)
    4. 90+ days of price history
    
    Ranking: 90-day Rate of Change (momentum)
    
    Args:
        sma_window: Days for Simple Moving Average (default: 200)
        min_volume: Minimum average daily volume in shares (default: 1,000,000)
        top_n: Number of top stocks to include in watchlist (default: 30)
        min_history: Minimum days of price history required (default: 90)
    """
    
    data_dir = '02_Ingestion/data/daily/'
    output_file = '03_Screener/current_watchlist.json'
    output_stats_file = '03_Screener/watchlist_stats.json'
    sentiment_file = '01b_Intelligence_Feed/current_sentiment.json'
    
    results = []
    
    # Filter statistics
    stats = {
        'total_tickers': 0,
        'passed_sentiment': 0,
        'passed_sma': 0,
        'passed_volume': 0,
        'passed_history': 0,
        'final_watchlist': 0,
        'filtered_reasons': {
            'negative_sentiment': 0,
            'below_sma': 0,
            'low_volume': 0,
            'insufficient_history': 0,
            'error': 0
        }
    }
    
    # Load sentiment data (gracefully handle missing file)
    sentiment_data = {}
    if os.path.exists(sentiment_file):
        try:
            with open(sentiment_file, 'r') as f:
                sentiment_data = json.load(f)
            print(f"Loaded sentiment data for {len(sentiment_data)} tickers")
        except Exception as e:
            print(f"Warning: Could not load sentiment file: {e}")
            print("  Proceeding with neutral sentiment for all tickers")
    else:
        print(f"Warning: Sentiment file not found at {sentiment_file}")
        print("  Proceeding with neutral sentiment for all tickers")
    
    # Iterate through all CSV files
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            ticker = filename.replace('.csv', '')
            file_path = os.path.join(data_dir, filename)
            stats['total_tickers'] += 1
            
            try:
                # 1. Check sentiment (filter out negative)
                sentiment_score = sentiment_data.get(ticker, 0.0)  # Default to neutral
                if sentiment_score < 0:
                    stats['filtered_reasons']['negative_sentiment'] += 1
                    continue
                
                stats['passed_sentiment'] += 1
                
                # 2. Read price data
                df = pd.read_csv(file_path, skiprows=3, names=['Date', 'Close', 'High', 'Low', 'Open', 'Volume'])
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')
                
                # 3. Check history length
                if len(df) < min_history:
                    stats['filtered_reasons']['insufficient_history'] += 1
                    continue
                
                stats['passed_history'] += 1
                
                # 4. Macro Trend Filter: Check price above SMA
                sma = df['Close'].rolling(window=sma_window).mean().iloc[-1]
                current_price = df['Close'].iloc[-1]
                
                # Skip if SMA cannot be calculated (insufficient data)
                if pd.isna(sma):
                    stats['filtered_reasons']['below_sma'] += 1
                    continue
                
                if current_price <= sma:
                    stats['filtered_reasons']['below_sma'] += 1
                    continue
                
                stats['passed_sma'] += 1
                
                # 5. Liquidity Filter: 20-day Average Daily Volume
                avg_volume = df['Volume'].rolling(window=20).mean().iloc[-1]
                
                if avg_volume <= min_volume:
                    stats['filtered_reasons']['low_volume'] += 1
                    continue
                
                stats['passed_volume'] += 1
                
                # 6. Calculate momentum (90-day ROC)
                price_90_days_ago = df['Close'].iloc[-min_history]
                roc_90 = ((current_price - price_90_days_ago) / price_90_days_ago) * 100
                
                # Store detailed metrics
                results.append({
                    'ticker': ticker,
                    'roc_90': round(roc_90, 2),
                    'current_price': round(current_price, 2),
                    'sma_200': round(sma, 2),
                    'price_vs_sma_pct': round(((current_price - sma) / sma * 100), 2),
                    'avg_volume': round(avg_volume, 0),
                    'sentiment': round(sentiment_score, 4)
                })
                
            except Exception as e:
                stats['filtered_reasons']['error'] += 1
                print(f"  Error processing {ticker}: {e}")
                continue
    
    # Sort by ROC descending
    results.sort(key=lambda x: x['roc_90'], reverse=True)
    
    # Take top N
    top_results = results[:top_n]
    stats['final_watchlist'] = len(top_results)
    top_tickers = [item['ticker'] for item in top_results]
    
    # Save main watchlist (tickers only)
    with open(output_file, 'w') as f:
        json.dump(top_tickers, f, indent=4)
    
    # Save detailed stats and metrics
    detailed_stats = {
        'meta': stats,
        'watchlist': top_results
    }
    with open(output_stats_file, 'w') as f:
        json.dump(detailed_stats, f, indent=4)
    
    # Print summary report
    print("\n" + "="*70)
    print("SCREENER RESULTS")
    print("="*70)
    print(f"\nFilter Pipeline:")
    print(f"  Total tickers scanned:          {stats['total_tickers']}")
    print(f"  Passed sentiment filter:       {stats['passed_sentiment']} ({stats['passed_sentiment']/max(stats['total_tickers'],1)*100:.1f}%)")
    print(f"  Passed history filter:         {stats['passed_history']} ({stats['passed_history']/max(stats['total_tickers'],1)*100:.1f}%)")
    print(f"  Passed SMA trend filter:       {stats['passed_sma']} ({stats['passed_sma']/max(stats['total_tickers'],1)*100:.1f}%)")
    print(f"  Passed liquidity filter:       {stats['passed_volume']} ({stats['passed_volume']/max(stats['total_tickers'],1)*100:.1f}%)")
    
    print(f"\nFiltered Out:")
    for reason, count in stats['filtered_reasons'].items():
        if count > 0:
            print(f"  {reason.replace('_', ' ').title():<30} {count}")
    
    print(f"\n{'='*70}")
    print(f"FINAL WATCHLIST: {stats['final_watchlist']} stocks")
    print(f"{'='*70}")
    
    if stats['final_watchlist'] == 0:
        print("\nWARNING: No stocks passed all filters!")
        print("   Consider relaxing filter thresholds or checking data quality.\n")
    elif stats['final_watchlist'] < 5:
        print(f"\nWARNING: Only {stats['final_watchlist']} stocks in watchlist (typically 30).")
        print("   Market may be in downtrend or filters too strict.\n")
    else:
        print(f"\nWatchlist ready with {stats['final_watchlist']} candidates\n")
    
    # Print top 10 stocks
    print("Top 10 by 90-Day Momentum:")
    print(f"{'Rank':<6}{'Ticker':<8}{'ROC 90d':<10}{'Price':<10}{'vs SMA':<10}{'Volume':<12}{'Sentiment':<10}")
    print("-" * 70)
    for i, stock in enumerate(top_results[:10], 1):
        print(f"{i:<6}{stock['ticker']:<8}{stock['roc_90']:<10.2f}{stock['current_price']:<10.2f}"
              f"{stock['price_vs_sma_pct']:<10.2f}{stock['avg_volume']:<12.0f}{stock['sentiment']:<10.4f}")
    
    print(f"\nFull watchlist saved to: {output_file}")
    print(f"Detailed stats saved to: {output_stats_file}\n")

if __name__ == '__main__':
    # Use default thresholds
    # Customize by passing parameters: run_screener(sma_window=200, min_volume=1000000, top_n=30)
    run_screener()
