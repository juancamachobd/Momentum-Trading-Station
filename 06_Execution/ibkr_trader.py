import os
import pandas as pd
from ib_insync import IB, MarketOrder, Stock
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def execute_ibkr_trades():
    ib = IB()
    try:
        host = os.environ.get('IBKR_HOST', '127.0.0.1')
        port = int(os.environ.get('IBKR_PORT', 7497))
        account = os.environ.get('IBKR_ACCOUNT')
        
        logging.info(f"Connecting to IBKR at {host}:{port}...")
        ib.connect(host, port, clientId=1)
        logging.info("Connected successfully.")
    except Exception as e:
        logging.error(f"Failed to connect to TWS: {e}")
        logging.warning(f"Please ensure TWS/Gateway is running and API port {port} is configured.")
        return

    try:
        # Get Equity
        account_summary = ib.accountSummary(account=account)
        net_liq_value = 0
        for item in account_summary:
            if item.tag == 'NetLiquidation':
                net_liq_value = float(item.value)
                break
        
        logging.info(f"Total Equity: ${net_liq_value:,.2f}")

        # Signal Directory
        signal_dir = '04_Strategy/signals/'
        
        for filename in os.listdir(signal_dir):
            if filename.endswith('_signals.csv'):
                ticker = filename.replace('_signals.csv', '')
                file_path = os.path.join(signal_dir, filename)
                
                df = pd.read_csv(file_path)
                if df.empty:
                    continue
                
                # Get last row
                last_row = df.iloc[-1]
                
                # Check for signal
                scale_in = last_row.get('Scale_In_Signal', 0)
                current_price = last_row.get('Close', 0)
                
                if scale_in > 0:
                    target_dollar = net_liq_value * scale_in
                    shares = int(target_dollar / current_price)
                    
                    if shares > 0:
                        contract = Stock(ticker, 'SMART', 'USD')
                        order = MarketOrder('BUY', shares)
                        
                        logging.info(f"Placing order: {ticker}, Shares: {shares}, Amount: ${target_dollar:,.2f}")
                        ib.placeOrder(contract, order)
                    else:
                        logging.info(f"Signal found for {ticker} but calculated shares is 0.")
                else:
                    logging.debug(f"No buy signal for {ticker}.")

    finally:
        ib.disconnect()
        logging.info("Disconnected from IBKR.")

if __name__ == '__main__':
    execute_ibkr_trades()
