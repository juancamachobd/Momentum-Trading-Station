import json
import os
import yfinance as yf
import pandas as pd
import time
import logging
from datetime import datetime, timedelta

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('02_Ingestion/data_ingestion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def read_csv_safe(file_path):
    """
    Safely read CSV file, handling both old and new formats.
    Returns DataFrame with standardized columns: Date, Open, High, Low, Close, Volume
    """
    try:
        # Try reading the new format first
        df = pd.read_csv(file_path)
        
        # Check if we have the expected columns
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if all(col in df.columns for col in required_cols):
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        
        # If not, try reading with skiprows=3 (old format)
        df = pd.read_csv(file_path, skiprows=3)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        logger.debug(f"Error reading {file_path}: {e}")
        return None

def download_historical_data():
    """
    Download and update historical stock price data incrementally.
    
    Returns:
        dict: Summary with 'success', 'updated', 'skipped', 'failed' counts
    """
    input_file = '01a_Market_Universe/sp500_tickers.json'
    output_dir = '02_Ingestion/data/daily/'

    stats = {'success': 0, 'updated': 0, 'skipped': 0, 'failed': 0, 'errors': []}
    
    # Load tickers
    if not os.path.exists(input_file):
        logger.error(f"Ticker file not found: {input_file}")
        return stats

    with open(input_file, 'r') as f:
        tickers = json.load(f)

    # Set initial date range
    end_date = datetime.now()
    initial_start_date = end_date - timedelta(days=3 * 365)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.info(f"Starting incremental update for {len(tickers)} tickers. End date: {end_date.date()}")

    for idx, ticker in enumerate(tickers, 1):
        try:
            output_path = os.path.join(output_dir, f"{ticker}.csv")
            
            # Determine start date (incremental update)
            if os.path.exists(output_path):
                # Read existing data and get last date
                existing_df = read_csv_safe(output_path)
                
                if existing_df is None or existing_df.empty:
                    logger.warning(f"[{idx}/{len(tickers)}] {ticker} - CSV read failed or empty, skipping")
                    stats['skipped'] += 1
                    continue
                
                # Ensure Date column exists
                if 'Date' not in existing_df.columns:
                    logger.warning(f"[{idx}/{len(tickers)}] {ticker} - No Date column found, skipping")
                    stats['skipped'] += 1
                    continue
                    
                last_date = pd.to_datetime(existing_df['Date'].iloc[-1])
                start_date = last_date + timedelta(days=1)
                
                # Skip if data is already current (within 1 day)
                days_behind = (end_date - last_date).days
                if days_behind <= 1:
                    logger.debug(f"[{idx}/{len(tickers)}] {ticker} - data current (last: {last_date.date()})")
                    stats['skipped'] += 1
                    continue
                    
                logger.info(f"[{idx}/{len(tickers)}] {ticker} - updating from {start_date.date()} ({days_behind} days behind)...")
            else:
                # First download - get 3 years of history
                start_date = initial_start_date
                logger.info(f"[{idx}/{len(tickers)}] {ticker} - initial download (3-year history)...")
            
            # Download new/updated data
            new_df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if new_df.empty:
                logger.warning(f"[{idx}/{len(tickers)}] {ticker} - no new data available")
                stats['skipped'] += 1
                continue
            
            # Reset index to convert date index to column
            new_df = new_df.reset_index()
            new_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            
            # If file exists and we're appending, concatenate and remove duplicates
            if os.path.exists(output_path) and start_date <= end_date:
                # Read existing file
                existing_df = read_csv_safe(output_path)
                
                if existing_df is not None and not existing_df.empty:
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df['Date'] = pd.to_datetime(combined_df['Date'])
                    combined_df = combined_df.drop_duplicates(subset=['Date'], keep='last')
                    combined_df = combined_df.sort_values('Date').reset_index(drop=True)
                    combined_df.to_csv(output_path, index=False)
                    
                    # Validate the write
                    if len(combined_df) > 0:
                        logger.info(f"[{idx}/{len(tickers)}] {ticker} updated - {len(new_df)} new rows (total: {len(combined_df)})")
                        stats['updated'] += 1
                        stats['success'] += 1
                    else:
                        raise ValueError("Combined dataframe is empty after merge")
                else:
                    new_df.to_csv(output_path, index=False)
                    logger.info(f"[{idx}/{len(tickers)}] {ticker} saved - {len(new_df)} rows")
                    stats['success'] += 1
            else:
                new_df.to_csv(output_path, index=False)
                logger.info(f"[{idx}/{len(tickers)}] {ticker} saved - {len(new_df)} rows")
                stats['success'] += 1
            
            time.sleep(0.5)  # Rate limit handling
            
        except Exception as e:
            logger.error(f"[{idx}/{len(tickers)}] {ticker} error: {str(e)}")
            stats['failed'] += 1
            stats['errors'].append(f"{ticker}: {str(e)}")
            time.sleep(2)

    # Log summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Download Summary:")
    logger.info(f"  Total tickers: {len(tickers)}")
    logger.info(f"  Successfully updated: {stats['updated']}")
    logger.info(f"  Already current: {stats['skipped']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"{'='*60}\n")
    
    if stats['errors']:
        logger.warning(f"Errors encountered: {stats['errors'][:5]}")  # Show first 5 errors
    
    return stats

if __name__ == "__main__":
    download_historical_data()
