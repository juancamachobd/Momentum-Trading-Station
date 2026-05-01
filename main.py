#!/usr/bin/env python
"""
Momentum Trading Station - Main Orchestration Script
Manages scheduled data ingestion and strategy execution
"""

import os
import sys
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import signal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util

# Load the historical_downloader module dynamically
spec = importlib.util.spec_from_file_location(
    "historical_downloader",
    os.path.join(os.path.dirname(__file__), "02_Ingestion", "historical_downloader.py")
)
downloader_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(downloader_module)
download_historical_data = downloader_module.download_historical_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('02_Ingestion/data_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def run_data_ingestion():
    """Execute data ingestion and log results"""
    logger.info("="*70)
    logger.info("SCHEDULED DATA INGESTION STARTING")
    logger.info("="*70)
    
    try:
        stats = download_historical_data()
        logger.info(f"Data ingestion completed: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Data ingestion failed: {str(e)}", exc_info=True)
        return None

def start_scheduler():
    """Start the background scheduler for automated tasks"""
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.warning("Scheduler is already running")
        return
    
    scheduler = BackgroundScheduler()
    
    # Schedule data ingestion for 4:30 PM ET daily
    # Explicitly set timezone to America/New_York to handle EDT/EST properly
    # This runs after market close at 4:00 PM ET
    scheduler.add_job(
        run_data_ingestion,
        CronTrigger(hour=16, minute=30, timezone='America/New_York'),
        id='daily_data_ingestion',
        name='Daily Data Ingestion',
        misfire_grace_time=900  # Allow 15 min grace for missed execution
    )
    
    scheduler.start()
    logger.info("Scheduler started with daily data ingestion at 20:30 UTC (4:30 PM ET)")
    
    # Print next scheduled run
    job = scheduler.get_job('daily_data_ingestion')
    if job:
        logger.info(f"Next scheduled run: {job.next_run_time}")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler is None or not scheduler.running:
        logger.info("Scheduler is not running")
        return
    
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped")
    scheduler = None

def manual_ingestion():
    """Run data ingestion immediately (for manual trigger)"""
    logger.info("\n" + "="*70)
    logger.info("MANUAL DATA INGESTION TRIGGERED")
    logger.info("="*70)
    stats = run_data_ingestion()
    logger.info("\nData ingestion completed successfully")
    return stats

def signal_handler(sig, frame):
    """Handle graceful shutdown on interrupt"""
    logger.info("\nReceived interrupt signal, shutting down...")
    stop_scheduler()
    sys.exit(0)

def main():
    """Main entry point"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("\n" + "="*70)
    logger.info("Momentum Trading Station - Initializing")
    logger.info("="*70)
    
    # Check if running in manual mode or scheduler mode
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'ingest':
            """Run data ingestion immediately"""
            manual_ingestion()
        elif command == 'schedule':
            """Start scheduler and keep running"""
            start_scheduler()
            logger.info("\nScheduler running. Press Ctrl+C to stop...")
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                stop_scheduler()
        elif command == 'status':
            """Show scheduler status"""
            if scheduler and scheduler.running:
                jobs = scheduler.get_jobs()
                logger.info(f"Scheduler is running with {len(jobs)} job(s)")
                for job in jobs:
                    logger.info(f"  - {job.name}: {job.next_run_time}")
            else:
                logger.info("Scheduler is not running")
        else:
            print_usage()
    else:
        print_usage()

def print_usage():
    """Print usage information"""
    print("\n" + "="*70)
    print("Momentum Trading Station - Usage")
    print("="*70)
    print("\nCommands:")
    print("  python main.py ingest      - Run data ingestion immediately")
    print("  python main.py schedule    - Start scheduler (daily at 4:30 PM ET)")
    print("  python main.py status      - Show scheduler status")
    print("\nExamples:")
    print("  python main.py ingest      # Update all tickers now")
    print("  python main.py schedule    # Start automated daily updates")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
