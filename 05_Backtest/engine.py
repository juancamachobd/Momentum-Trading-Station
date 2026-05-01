import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
INITIAL_CAPITAL = 100000
COMMISSION_RATE = 0.001  # 0.1% per trade
SLIPPAGE = 0.0005        # 0.05% slippage
SIGNALS_DIR = '04_Strategy/signals/'
TRADE_LOG_PATH = '05_Backtest/trade_log.csv'
EQUITY_CURVE_PATH = '05_Backtest/equity_curve.png'

# Risk Management Configuration
TRAILING_STOP_PCT = 0.03      # 3% trailing stop
TAKE_PROFIT_LEVELS = [0.02, 0.05, 0.08]  # 2%, 5%, 8% take profit levels
TAKE_PROFIT_SHARES_PCT = [0.33, 0.33, 0.34]  # Exit 33%, 33%, 34% of position at each level
POSITION_SIZE_PCT = 0.05  # Allocate 5% of capital per position

class PositionTracker:
    """Tracks position state including trailing stop and take profit levels."""
    def __init__(self, ticker, entry_price, shares, entry_date):
        self.ticker = ticker
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.shares_remaining = shares
        self.peak_price = entry_price
        self.trailing_stop_price = entry_price * (1 - TRAILING_STOP_PCT)
        self.take_profit_hits = [False] * len(TAKE_PROFIT_LEVELS)
        
    def update(self, current_price):
        """Update peak price and trailing stop."""
        if current_price > self.peak_price:
            self.peak_price = current_price
            self.trailing_stop_price = current_price * (1 - TRAILING_STOP_PCT)
            
    def get_unrealized_pnl(self, current_price):
        """Calculate unrealized PnL."""
        return (current_price - self.entry_price) * self.shares_remaining
    
    def should_exit_trailing_stop(self, current_price):
        """Check if trailing stop is hit."""
        return current_price <= self.trailing_stop_price
    
    def get_take_profit_exits(self, current_price):
        """Determine take profit exits. Returns list of (shares_to_sell, tp_level_pct)."""
        exits = []
        profit_pct = (current_price - self.entry_price) / self.entry_price
        
        for idx, tp_level in enumerate(TAKE_PROFIT_LEVELS):
            if profit_pct >= tp_level and not self.take_profit_hits[idx]:
                shares_to_sell = self.shares_remaining * TAKE_PROFIT_SHARES_PCT[idx]
                exits.append((shares_to_sell, tp_level))
                self.take_profit_hits[idx] = True
                
        return exits

def run_backtest():
    all_data = []
    
    # Load all signals
    for filename in os.listdir(SIGNALS_DIR):
        if filename.endswith('_signals.csv'):
            ticker = filename.split('_')[0]
            df = pd.read_csv(os.path.join(SIGNALS_DIR, filename))
            df['Date'] = pd.to_datetime(df['Date'])
            df['Ticker'] = ticker
            all_data.append(df)
            
    if not all_data:
        print("No signal files found.")
        return

    full_df = pd.concat(all_data).sort_values('Date')
    
    # Pre-calculate rolling EMA for each ticker to avoid inefficiency in the loop
    for ticker in full_df['Ticker'].unique():
        full_df.loc[full_df['Ticker'] == ticker, 'EMA20'] = full_df[full_df['Ticker'] == ticker]['Close'].ewm(span=20, adjust=False).mean()
        
    cash = INITIAL_CAPITAL
    positions = {} # ticker -> PositionTracker
    daily_equity = []
    trade_logs = []
    closed_trades = []
    
    # Daily loop
    dates = full_df['Date'].unique()
    for date in dates:
        day_data = full_df[full_df['Date'] == date]
        
        for _, row in day_data.iterrows():
            ticker = row['Ticker']
            signal = row['Signal']
            price = row['Close']
            ema20 = row['EMA20']
            high = row['High']
            
            # Exit Logic - Check existing positions for exit conditions
            if ticker in positions and positions[ticker].shares_remaining > 0:
                position = positions[ticker]
                position.update(price)
                
                exit_reason = None
                exit_shares = 0
                exit_price_for_log = price
                
                # Check trailing stop
                if position.should_exit_trailing_stop(price):
                    exit_reason = "Trailing Stop"
                    exit_shares = position.shares_remaining
                
                # Check take profit levels
                if exit_reason is None:
                    tp_exits = position.get_take_profit_exits(price)
                    for shares_to_sell, tp_level in tp_exits:
                        if shares_to_sell > 0:
                            exit_price = price * (1 - SLIPPAGE)
                            realized_pnl = (exit_price - position.entry_price) * shares_to_sell
                            commission = (exit_price * shares_to_sell) * COMMISSION_RATE
                            
                            cash += (shares_to_sell * exit_price) - commission
                            trade_logs.append([date, ticker, 'Sell (TP)', shares_to_sell, exit_price, realized_pnl - commission])
                            closed_trades.append(realized_pnl - commission)
                            position.shares_remaining -= shares_to_sell
                
                # Check explicit sell signal
                if exit_reason is None and row['Signal_Type'] == 'Sell':
                    exit_reason = "Signal Sell"
                    exit_shares = position.shares_remaining
                
                # Execute trailing stop or signal-based exit
                if exit_reason and exit_shares > 0:
                    exit_price = price * (1 - SLIPPAGE)
                    realized_pnl = (exit_price - position.entry_price) * exit_shares
                    commission = (exit_price * exit_shares) * COMMISSION_RATE
                    
                    cash += (exit_shares * exit_price) - commission
                    trade_logs.append([date, ticker, f'Sell ({exit_reason})', exit_shares, exit_price, realized_pnl - commission])
                    closed_trades.append(realized_pnl - commission)
                    
                    position.shares_remaining = 0
                    del positions[ticker]
            
            # Entry Logic
            if row['Signal_Type'] == 'Buy':
                # Use fixed position size (5% of initial capital per trade)
                allocation = INITIAL_CAPITAL * POSITION_SIZE_PCT
                
                # Apply slippage to entry price (use high to be conservative)
                entry_price = price * (1 + SLIPPAGE)
                
                shares_to_buy = allocation / entry_price
                commission = allocation * COMMISSION_RATE
                
                # If already holding, add to position
                if ticker in positions and positions[ticker].shares_remaining > 0:
                    position = positions[ticker]
                    old_shares = position.shares_remaining
                    new_total_shares = old_shares + shares_to_buy
                    position.entry_price = ((old_shares * position.entry_price) + (shares_to_buy * entry_price)) / new_total_shares
                    position.shares_remaining = new_total_shares
                    position.peak_price = max(position.peak_price, entry_price)
                    position.trailing_stop_price = position.peak_price * (1 - TRAILING_STOP_PCT)
                    cash -= (allocation + commission)
                    trade_logs.append([date, ticker, 'Buy (Add)', shares_to_buy, entry_price, -commission])
                # If not holding, open new position
                elif cash >= (allocation + commission):
                    cash -= (allocation + commission)
                    positions[ticker] = PositionTracker(ticker, entry_price, shares_to_buy, date)
                    trade_logs.append([date, ticker, 'Buy', shares_to_buy, entry_price, -commission])
        
        # Calculate Equity
        total_holdings_value = 0
        for ticker, position in positions.items():
            if position.shares_remaining > 0:
                current_price = full_df[(full_df['Ticker'] == ticker) & (full_df['Date'] == date)]['Close'].iloc[0]
                total_holdings_value += position.shares_remaining * current_price
        
        equity = cash + total_holdings_value
        daily_equity.append({'Date': date, 'Equity': equity})
        
    # Save log
    pd.DataFrame(trade_logs, columns=['Date', 'Ticker', 'Action', 'Shares', 'Price', 'Realized PnL']).to_csv(TRADE_LOG_PATH, index=False)
    
    # Performance Metrics
    equity_df = pd.DataFrame(daily_equity)
    equity_df['Returns'] = equity_df['Equity'].pct_change()
    
    final_equity = equity_df['Equity'].iloc[-1] if len(equity_df) > 0 else INITIAL_CAPITAL
    total_return = (final_equity - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    max_drawdown = (equity_df['Equity'].cummax() - equity_df['Equity']) / equity_df['Equity'].cummax() * 100
    
    sharpe_ratio = (equity_df['Returns'].mean() / equity_df['Returns'].std()) * (252**0.5) if equity_df['Returns'].std() > 0 else 0
    
    winning_trades = len([pnl for pnl in closed_trades if pnl > 0])
    total_closed_trades = len(closed_trades)
    win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0
    
    avg_win = sum([pnl for pnl in closed_trades if pnl > 0]) / winning_trades if winning_trades > 0 else 0
    avg_loss = sum([pnl for pnl in closed_trades if pnl < 0]) / (total_closed_trades - winning_trades) if (total_closed_trades - winning_trades) > 0 else 0
    profit_factor = abs(avg_win * winning_trades / (avg_loss * (total_closed_trades - winning_trades))) if avg_loss != 0 else 0
    
    print("\n" + "="*60)
    print("BACKTEST RESULTS WITH TRAILING STOP & TAKE PROFIT")
    print("="*60)
    print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"Final Equity: ${final_equity:,.2f}")
    print(f"Total Return: {total_return:.2f}%")
    print(f"Max Drawdown: {max_drawdown.max():.2f}%")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"\nTrade Statistics:")
    print(f"  Total Closed Trades: {total_closed_trades}")
    print(f"  Winning Trades: {winning_trades}")
    print(f"  Win Rate: {win_rate:.2f}%")
    print(f"  Average Win: ${avg_win:,.2f}")
    print(f"  Average Loss: ${avg_loss:,.2f}")
    print(f"  Profit Factor: {profit_factor:.2f}")
    print(f"\nRisk Management Settings:")
    print(f"  Trailing Stop: {TRAILING_STOP_PCT*100:.1f}%")
    print(f"  Take Profit Levels: {[f'{tp*100:.1f}%' for tp in TAKE_PROFIT_LEVELS]}")
    print(f"  Commission Rate: {COMMISSION_RATE*100:.2f}%")
    print(f"  Slippage: {SLIPPAGE*100:.2f}%")
    print("="*60 + "\n")
    
    # Plotting
    plt.figure(figsize=(12, 7))
    sns.lineplot(data=equity_df, x='Date', y='Equity', linewidth=2)
    plt.title('Portfolio Equity Curve with Trailing Stop & Take Profit', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Equity ($)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(EQUITY_CURVE_PATH, dpi=300)
    print(f"Equity curve saved to {EQUITY_CURVE_PATH}")

if __name__ == '__main__':
    run_backtest()
