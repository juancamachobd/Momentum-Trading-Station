**We are abandoning the simple EMA crossover strategy. I need to build an advanced, confluence-based support zone strategy. Please create a script at `04_Strategy/structure_pullback.py`.**

**First, update `requirements.txt` to include `scipy` (for finding swing highs/lows).**

**The script should read tickers from `03_Screener/current_watchlist.json` and process their daily data from `02_Ingestion/data/daily/`.**

### **Implement the following logic for each ticker:**

---

### **1. Market Structure (Weekly HH/HL) - STRICT NO LOOKAHEAD BIAS**
- Resample daily data to **Weekly**.
- Identify macro swing highs and swing lows over the last 52 weeks. **CRITICAL:** You must avoid lookahead bias. Do not pass the entire dataset into `scipy.signal.argrelextrema` at once. Ensure the peak/trough detection operates on a rolling, backward-looking basis. The algorithm must only identify a swing point *after* the confirmation window has passed in the historical data (e.g., a rolling window checking if a point $N$ periods ago is the local maximum/minimum).
- Market structure is **bullish** if:
  - The most recent confirmed swing high > previous confirmed swing high.
  - The most recent confirmed swing low > previous confirmed swing low.
- If the structure is NOT bullish → **skip the ticker**.

---

### **2. Indicator Calculations (Daily Data)**
- Compute **50, 100, and 200 Simple Moving Averages (SMA)**.
- Compute the **Ichimoku Cloud** (specifically Senkou Span A & B) using standard periods (9, 26, 52).
- Compute **ATR(14)** to be used for dynamic zone sizing.

---

### **3. Deep Retracement Math (Weekly & Daily Sync)**
- Using the most recent confirmed macro swing low to the most recent confirmed macro swing high, compute the **0.786** and **0.886** Fibonacci retracement price levels.

---

### **4. Gann Square of Nine Levels**
- Project upward from the most recent macro swing low using the following mathematical formula:
  `Level = (sqrt(SwingLow) + n)**2`
- Iterate `n` using standard Gann eighth/quarter increments (e.g., 0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.25, etc.) to calculate the Gann levels that are closest to the current daily price.

---

### **5. Confluence & Dynamic ATR Support Zone**
We are using a dynamic, volatility-adjusted support zone:
- **Support Zone Width = `0.5 * ATR(14)`**
- For each confluence element (the 0.786 Fib, the 0.886 Fib, calculated Gann levels, the 3 SMAs, and Senkou Span A/B), define its individual magnetic zone as: `Element Level ± (0.5 * ATR(14))`.
- A valid "Support Zone" requires **$\ge$ 3 overlapping elements** (their ATR bands must physically intersect at the current price).

---

### **6. Scale-In Execution Logic**
Create a `Scale_In_Signal` column evaluated on the daily close:
- If the daily price drops into a validated Support Zone with exactly **3 overlapping confluence elements** → output **0.01** (representing a 1% portfolio scale-in).
- If the daily price drops into a validated Support Zone with **4 or more overlapping elements** → output **0.02** (representing a 2% portfolio scale-in).
- If the daily price closes **below the 0.886 Fib level** → output **0.00** (invalidated setup, stop out).

---

### **7. Save Output**
Save the results to: `04_Strategy/signals/<TICKER>_signals.csv`
Include the following columns in the output:
- Date, Open, High, Low, Close, Volume
- All calculated Confluence levels (Fibs, Gann, SMAs, Cloud edges)
- The calculated ATR-based Support Zone boundaries
- Market structure status (Boolean)
- `Scale_In_Signal` weights

***