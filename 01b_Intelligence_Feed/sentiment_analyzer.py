import json
import nltk
import yfinance as yf
import os
import time
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download VADER lexicon
nltk.download('vader_lexicon')

def analyze_sentiment():
    # Load current watchlist or use cached candidate list
    watchlist_path = '03_Screener/current_watchlist.json'
    cache_path = '01b_Intelligence_Feed/current_sentiment.json'
    
    # Get tickers to analyze
    if os.path.exists(watchlist_path):
        # Use current screener watchlist + buffer of previous candidates
        with open(watchlist_path, 'r') as f:
            tickers_to_analyze = json.load(f)
        print(f"Analyzing sentiment for {len(tickers_to_analyze)} watchlist tickers...")
    else:
        # Fallback: Load top candidates from full SP500 (high liquidity)
        with open('01a_Market_Universe/sp500_tickers.json', 'r') as f:
            all_tickers = json.load(f)
        # Analyze top 50 (most liquid)
        tickers_to_analyze = all_tickers[:50]
        print(f"No watchlist found. Analyzing first {len(tickers_to_analyze)} tickers...")
    
    # Load existing sentiment cache
    existing_sentiment = {}
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            existing_sentiment = json.load(f)
    
    analyzer = SentimentIntensityAnalyzer()
    sentiment_results = existing_sentiment.copy()  # Start with cached values
    updated_count = 0
    
    for ticker in tickers_to_analyze:
        # Skip if already in cache (avoid unnecessary API calls)
        if ticker in existing_sentiment:
            print(f"Skipping {ticker} - cached sentiment: {existing_sentiment[ticker]:.4f}")
            continue
        
        print(f"Fetching sentiment for {ticker}...")
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news
            
            if not news:
                print(f"  No news found for {ticker}")
                sentiment_results[ticker] = 0.0  # Neutral if no news
                updated_count += 1
                time.sleep(2)  # Rate limit
                continue
            
            scores = []
            for article in news:
                title = article.get('title', '')
                score = analyzer.polarity_scores(title)['compound']
                scores.append(score)
            
            if scores:
                avg_score = sum(scores) / len(scores)
                sentiment_results[ticker] = avg_score
                print(f"  {ticker}: {avg_score:.4f} ({len(scores)} articles)")
                updated_count += 1
            else:
                sentiment_results[ticker] = 0.0
            
            # Rate limiting - aggressive to avoid 429 errors
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error analyzing {ticker}: {e}")
            sentiment_results[ticker] = 0.0  # Default to neutral on error
            time.sleep(3)  # Longer delay on error
    
    # Save results
    with open(cache_path, 'w') as f:
        json.dump(sentiment_results, f, indent=4)
    
    print(f"\n✓ Sentiment analysis complete ({updated_count} new/updated)")
    
    # Terminal summary
    sorted_sentiment = sorted(sentiment_results.items(), key=lambda x: x[1], reverse=True)
    
    print("\nTop 5 Positive:")
    for ticker, score in sorted_sentiment[:5]:
        print(f"  {ticker}: {score:.4f}")
        
    print("\nTop 5 Negative:")
    for ticker, score in sorted_sentiment[-5:]:
        print(f"  {ticker}: {score:.4f}")

if __name__ == "__main__":
    analyze_sentiment()
