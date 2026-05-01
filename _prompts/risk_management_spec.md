# Risk Management Specification: Trailing Stop & Take Profit

## Overview
This document defines the risk management framework implemented in the backtesting engine to minimize losses and capture partial profits through a systematic exit strategy.

## Exit Strategy Components

### 1. Trailing Stop Loss (3%)
**Purpose**: Protect capital by locking in gains or limiting losses
**Mechanism**:
- Tracks the highest price reached since entry (`peak_price`)
- Calculates trailing stop as: `peak_price × (1 - 3%)`
- Automatically exits if price drops 3% below the peak
- Dynamically updates upward as price rises

**Benefits**:
- Captures most of the uptrend
- Exits automatically if momentum reverses
- Prevents catastrophic losses
- Works well with trending markets

**Configuration**: `TRAILING_STOP_PCT = 0.03`

### 2. Tiered Take Profit Exits
**Purpose**: Capture gains systematically while staying in profitable trends

**Profit Levels & Position Exit**:
| Target | % of Position | Threshold | Strategy |
|--------|---------------|-----------|----------|
| Level 1 | 33% | +2% gain | Quick profit lock-in |
| Level 2 | 33% | +5% gain | Establish breakeven |
| Level 3 | 34% | +8% gain | Extended capture |

**Logic Flow**:
```
When current_price reaches a profit target:
  IF position_pct_gain >= target AND level_not_hit:
    1. Calculate shares_to_exit = total_shares × allocation_pct
    2. Close position at current price (with slippage applied)
    3. Record as "Sell (TP)" trade
    4. Mark level as hit to prevent re-triggering
    5. Keep remaining shares exposed to upside
```

**Configuration**:
```python
TAKE_PROFIT_LEVELS = [0.02, 0.05, 0.08]      # 2%, 5%, 8%
TAKE_PROFIT_SHARES_PCT = [0.33, 0.33, 0.34]  # Position allocation
```

### 3. Signal-Based Exits
**Purpose**: Close remaining position on explicit sell signals
**Trigger**: When EMA crossover generates a "Death Cross" sell signal
**Action**: Exit remaining shares at current close price

## Exit Priority (Order of Evaluation)

1. **Trailing Stop** → Highest priority (loss protection)
2. **Take Profit Levels** → Executed progressively as price rises
3. **Sell Signal** → Exits remaining position only if no TP triggers

## Trade Log Records

Each exit generates a record with the exit reason:
- **"Sell (Trailing Stop)"** → Hit trailing stop threshold
- **"Sell (TP)"** → Hit take profit level (1, 2, or 3)
- **"Sell (Signal Sell)"** → EMA death cross signal
- **"Buy (Add)"** → Added to existing position

## Position Tracking State

The `PositionTracker` class maintains:
- **entry_price**: Average entry price (updated if adding to position)
- **entry_date**: Entry date for reference
- **shares_remaining**: Current position size
- **peak_price**: Highest price since entry
- **trailing_stop_price**: Current trailing stop level
- **take_profit_hits**: Boolean flags for each TP level (prevents duplicate exits)

## Example Scenario

**Position Entry**: BUY 100 shares at $50.00
- Entry Cost: $5,000
- Trailing Stop: $48.50 (3% below entry)
- Peak Price: $50.00

**Price Action**:
1. Price rises to $51.00
   - Peak Price updates to $51.00
   - Trailing Stop updates to $49.47
   - Below 2% → No TP exit
   
2. Price rises to $52.50 (+5% gain)
   - Peak Price: $52.50
   - Trailing Stop: $50.93
   - Hits Take Profit Level 2 (5%)
   - **Exit 33 shares at $52.50** (TP #2)
   - Remaining: 67 shares, stop moved to $50.93
   
3. Price declines to $50.80
   - Peak Price: $52.50 (unchanged)
   - Trailing Stop: $50.93
   - **Still holding 67 shares**
   
4. Price drops to $50.85
   - Crosses trailing stop at $50.93
   - **Exit remaining 67 shares** (Trailing Stop)
   - Position closed

## Risk-Adjusted Metrics

**Performance Metrics Calculated**:
- **Win Rate**: % of closed trades with positive PnL
- **Profit Factor**: Avg Win × Total Wins / |Avg Loss × Total Losses|
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Max Drawdown**: Largest peak-to-trough decline

## Customization Parameters

All parameters are configurable at the top of `engine.py`:

```python
TRAILING_STOP_PCT = 0.03           # Adjust for volatility
TAKE_PROFIT_LEVELS = [0.02, 0.05, 0.08]  # Redefine profit targets
TAKE_PROFIT_SHARES_PCT = [0.33, 0.33, 0.34]  # Change position allocation
COMMISSION_RATE = 0.001             # Broker-specific
SLIPPAGE = 0.0005                   # Market microstructure
```

## Methodology Justification

### Why This Approach?
1. **Trailing Stop**: Adapts to volatility; locks profits automatically
2. **Tiered Exits**: Reduces regret risk; captures breakeven quickly
3. **Signal Exits**: Respects trend reversal confirmation
4. **Partial Liquidation**: Stays exposed to extended trends

### Risk/Reward Trade-offs
- **More aggressive**: Lower trailing stop % (e.g., 2%), higher TP levels (e.g., 10%)
- **More conservative**: Higher trailing stop % (e.g., 5%), lower TP levels (e.g., 1%, 3%, 5%)
