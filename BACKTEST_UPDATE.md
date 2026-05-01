# Backtest Engine Update - Quick Start Guide

## What Changed

### Core Improvements to `05_Backtest/engine.py`

1. **New PositionTracker Class**
   - Tracks individual position state (entry price, peak price, shares remaining)
   - Maintains trailing stop price dynamically
   - Tracks which take profit levels have been hit
   - Calculates unrealized PnL and exit conditions

2. **Implemented Trailing Stop**
   - 3% trailing stop by default (configurable)
   - Follows price upward automatically
   - Exits position when price drops 3% below peak
   - Minimizes losses while letting winners run

3. **Implemented Tiered Take Profit**
   - Level 1: Exit 33% at +2% gain (quick profit lock)
   - Level 2: Exit 33% at +5% gain (establish breakeven)
   - Level 3: Exit 34% at +8% gain (extended trend capture)
   - Each level executes independently to capture partial profits

4. **Enhanced Exit Logic**
   - Priority order: Trailing Stop → Take Profit → Signal Exit
   - Proper slippage and commission on every exit
   - Trade log now records exit reason (TP level, trailing stop, signal)
   - Prevents double-exits with boolean tracking

5. **Improved Performance Reporting**
   - Profit Factor metric (Win/Loss quality)
   - Average Win/Loss calculations
   - Breakdown of closing trades vs signal trades
   - Risk management settings display

## How to Run

```bash
cd c:\Project\Momentum-Trading-Station
python 05_Backtest/engine.py
```

## Expected Output

The backtest will now print:
```
============================================================
BACKTEST RESULTS WITH TRAILING STOP & TAKE PROFIT
============================================================
Initial Capital: $100,000.00
Final Equity: $[calculated]
Total Return: [X.XX]%
Max Drawdown: [X.XX]%
Sharpe Ratio: [X.XX]

Trade Statistics:
  Total Closed Trades: [N]
  Winning Trades: [N]
  Win Rate: [X.XX]%
  Average Win: $[X,XXX.XX]
  Average Loss: $[X,XXX.XX]
  Profit Factor: [X.XX]

Risk Management Settings:
  Trailing Stop: 3.0%
  Take Profit Levels: ['2.0%', '5.0%', '8.0%']
  Commission Rate: 0.10%
  Slippage: 0.05%
============================================================
```

## Trade Log (trade_log.csv)

The trade log now includes exit reasons:
- **Sell (TP)** - Take profit exit
- **Sell (Trailing Stop)** - Trailing stop hit
- **Sell (Signal Sell)** - EMA crossover sell signal
- **Buy (Add)** - Adding to existing position

Example row:
```
2025-12-15,AAPL,Sell (TP),33.5,152.50,1250.75
2025-12-16,MSFT,Sell (Trailing Stop),50.0,380.20,-850.30
```

## Configuration Parameters

To adjust risk management settings, edit these lines in `engine.py`:

```python
# Current settings (Line 13-14)
TRAILING_STOP_PCT = 0.03           # Change to 0.02 or 0.05
TAKE_PROFIT_LEVELS = [0.02, 0.05, 0.08]  # Adjust levels
TAKE_PROFIT_SHARES_PCT = [0.33, 0.33, 0.34]  # Rebalance exit sizes
```

## Common Adjustments

### More Aggressive (Capture Larger Moves)
```python
TRAILING_STOP_PCT = 0.05           # 5% trailing stop
TAKE_PROFIT_LEVELS = [0.03, 0.07, 0.12]  # 3%, 7%, 12%
```

### More Conservative (Protect Capital)
```python
TRAILING_STOP_PCT = 0.02           # 2% trailing stop
TAKE_PROFIT_LEVELS = [0.01, 0.03, 0.05]  # 1%, 3%, 5%
```

## Troubleshooting

**If trade_log.csv is still empty:**
- Check that signal files exist in `04_Strategy/signals/`
- Verify the data files in `02_Ingestion/data/daily/` have price data
- Check that Buy signals are being generated (review crossover_strategy.py output)

**If equity curve shows no gains:**
- Review trade_log.csv for exit reasons
- Check if trailing stop is too tight (losses on noise)
- Verify take profit levels are achievable (check historical returns)

## Next Steps

1. Run the backtest and review trade_log.csv
2. Analyze the win rate and profit factor
3. Adjust trailing stop % based on asset volatility
4. Adjust take profit levels based on expected returns
5. A/B test different configurations with walk-forward analysis

For detailed methodology, see: `_prompts/risk_management_spec.md`
