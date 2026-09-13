# STRATEGY 1: BB01 BREAKOUT CONTINUATION

**Status:** PROMISING BUT FRAGILE  
**Date:** September 2026  
**Holding Period:** 20 trading days  
**Transaction Costs:** 0.05% per side (0.10% round trip)

---

## 1. Hypothesis

An upper volatility-band breakout (BB01=1) identifies a state of positive momentum continuation over medium-term horizons (20 days). Breakout trades tend to capture this continuation and should deliver positive forward returns.

---

## 2. Signal Definition

**Signal:** BB01 (boolean, pre-supplied)
- Value: 1 when upper band breakout occurs, 0 otherwise
- No modification, no parameter tuning
- Used exactly as supplied from signal library

---

## 3. Causal Timing Convention

- Signal information available through candle t-1 close
- Entry decision made at candle t
- Entry execution at candle t open
- Position held for 20 trading days
- Exit execution at candle t+20 open
- Forward return: `close[t+20] / open[t] - 1`

**Critical rule:** No lookahead. All decisions are based on information available before execution.

---

## 4. Entry/Exit Rules

### Entry
- BB01[t-1] = 1 (signal known at previous close)
- Decision at t, execute at t open
- Enter long position only if no position currently open

### Position Management
1. Long only (no shorts)
2. No overlapping positions
3. No stop loss
4. No profit target
5. No leverage (1x)
6. No pyramiding

### Exit
- Hold for exactly 20 trading days
- Exit at t+20 open
- No discretionary exit

---

## 5. Transaction Costs

**Competition specification:**
- 0.05% per side
- 0.10% round trip

**Applied explicitly:**
- Entry cost: 0.05%
- Exit cost: 0.05%
- Total per trade: 0.10%

---

## 6. Signal-Level Evidence (Discovery)

This is the evidence already validated in the BB01 validation study:

| Metric | Value |
|--------|-------|
| **Total BB01 events** | 43 |
| **Mean return (event)** | +0.330% |
| **Mean return (non-event)** | +0.007% |
| **Spread** | +0.323% |
| **Welch t-statistic** | 2.0333 |
| **Welch p-value** | 0.0482 |
| **Bootstrap 95% CI** | [0.053%, 0.583%] |

**Interpretation:** Signal-level evidence supports the hypothesis that BB01 events are followed by higher 20d returns. However, this signal-level validation uses ALL 43 events, including those that overlap with other positions.

---

## 7. Executable Strategy Results (Strategy Evidence)

### Signal vs Executable
| Category | Count |
|----------|-------|
| Total BB01 signal events | 43 |
| Events skipped (position overlap) | 26 |
| Executable trades (no overlap) | 17 |

**Reason for discrepancy:** With only 4.7% event frequency and 20-day holding periods, many BB01 signals occur while another position is already open. The no-overlap rule enforces that only one position can be open at a time, reducing the number of executable trades from 43 to 17.

### Performance Metrics

| Metric | Value |
|--------|-------|
| **Total return** | 23.03% |
| **Annualized return** | 4.71% |
| **Annualized volatility** | 134.37% |
| **Sharpe ratio** | 0.0350 |
| **Max drawdown** | -32.75% |
| **Calmar ratio** | 0.1437 |

### Trade Statistics

| Metric | Value |
|--------|-------|
| **Number of trades** | 17 |
| **Win rate** | 47.1% (8 wins, 9 losses) |
| **Profit factor** | 1.5168 |
| **Average trade** | 1.35% |
| **Median trade** | -1.26% |
| **Best trade** | +18.49% |
| **Worst trade** | -9.85% |
| **Avg winner** | +8.45% |
| **Avg loser** | -4.95% |
| **Avg holding period** | 32.2 days |

### Cost Impact

| Category | Value |
|--------|-------|
| **Gross PnL** | 24.73% |
| **Transaction costs** | 1.70% |
| **Net PnL** | 23.03% |
| **Costs as % of gross** | 6.9% |

**Interpretation:** Transaction costs consume 6.9% of gross PnL. This is manageable but material. The strategy's net return of 23.03% exceeds transaction costs, but only by 1.73 basis points per trade on average.

---

## 8. Yearly Performance

| Year | Trades | Return | Win Rate |
|------|--------|--------|----------|
| **2018** | 4 | 3.07% | 50.0% |
| **2019** | 5 | -22.20% | 20.0% |
| **2020** | 5 | 39.24% | 60.0% |
| **2021** | 3 | 2.92% | 66.7% |

**Observations:**
- 2018: Modest positive return, balanced win rate
- 2019: Significant drawdown year, poor win rate (1/5 wins)
- 2020: Strong year, best performance
- 2021: Limited sample (3 trades), strong win rate

**Concern:** The 2019 drawdown of -22.20% on just 5 trades demonstrates vulnerability to market regimes where breakouts fail.

---

## 9. Walk-Forward Validation

### Fold 1: Train 2018-2019 → Test 2020

| Period | Trades | Return | Sign Consistency |
|--------|--------|--------|-----------------|
| **Train (2018-2019)** | 9 | -19.13% | |
| **Test (2020)** | 5 | 39.24% | **NO** |

**Result:** Sign REVERSAL. Strategy was negative in training but strongly positive in test. This suggests the signal's effectiveness depends on market regime, not robust directional persistence.

### Fold 2: Train 2018-2020 → Test 2021

| Period | Trades | Return | Sign Consistency |
|--------|--------|--------|-----------------|
| **Train (2018-2020)** | 14 | 20.11% | |
| **Test (2021)** | 3 | 2.92% | **YES** |

**Result:** Sign CONSISTENCY in positive direction. Both train and test are positive, though test performance is weaker. However, test sample is very small (3 trades).

**Overall WFO Assessment:** Mixed. Fold 1 shows sign reversal (concerning); Fold 2 shows consistency but with tiny sample. The strategy's out-of-sample stability is questionable.

---

## 10. Sensitivity Checks (Robustness)

Tested 10d, 15d, and 20d holding periods with identical entry logic and no-overlap enforcement:

| Horizon | Trades | Return | Win Rate |
|---------|--------|--------|----------|
| **10d** | 20 | 12.06% | 40.0% |
| **15d** | 18 | 16.34% | 44.4% |
| **20d** | 17 | 23.03% | 47.1% |

**Pattern:** Longer holding periods deliver higher returns and better win rates. This is intuitive—20d breakouts capture more continuation than 10d—but it also shows the strategy's return is sensitive to horizon choice. The baseline 20d specification (validated in prior research) is chosen, not optimized.

---

## 11. Failure Modes & Risk Factors

### 1. Regime Dependence (Critical)
The 2019 drawdown and WFO Fold 1 sign reversal show that the strategy performs very differently across market regimes. It failed in 2019 (breakouts did not continue) and succeeded in 2020 (breakouts did continue). This suggests the signal captures regime-dependent behavior rather than a stable predictive relationship.

### 2. Low Event Frequency
Only 4.7% of candles trigger BB01 events. This means:
- Only 17 executable trades over 4 years
- Statistical power is limited
- Each trade is not independent (overlapping holding periods)
- Random variation can dominate signal

### 3. High Volatility (134% annualized)
The strategy exhibits extreme drawdown risk:
- Max drawdown: -32.75%
- Calmar ratio: 0.1437 (low)
- Sharpe ratio: 0.0350 (very low)

This suggests most equity fluctuations are driven by noise, not signal.

### 4. Median Trade Negative (-1.26%)
The median trade is negative, even though the mean is positive (1.35%). This indicates the return distribution is right-skewed: a few large winners pull up the average. The strategy is vulnerable to missing those winners.

### 5. 2019 Drawdown Clustering
Five trades in 2019 returned -22.20% combined. This was not a rare event; it was systematic failure of the signal in that year. The strategy provides no safeguard against such regime shifts.

---

## 12. Final Classification

**Classification: PROMISING BUT FRAGILE**

### Rationale

**Positive evidence:**
- Signal-level validation confirms +0.323% spread (Welch t=2.03)
- Executable strategy delivers 23.03% net return over 4 years
- Transaction costs are only 6.9% of gross PnL
- Sharpe > 0 (though very low at 0.0350)
- 10d/15d sensitivity checks show consistent pattern

**Negative evidence (critical):**
- Walk-forward sign reversal in Fold 1 (train -19%, test +39%)
- Regime dependence evident from 2019 failure
- Extremely low Sharpe ratio (0.0350) and high drawdown (-32.75%)
- Small sample of trades (17) limits statistical inference
- Median trade negative despite positive mean
- Poor out-of-sample stability

### Why "Promising But Fragile"

- **Promising:** The signal works in some regimes (2020: +39%); it is not consistently wrong
- **Fragile:** The signal fails unpredictably in other regimes (2019: -22%); WFO shows sign reversal; drawdown risk is high

The strategy is not yet VALIDATED because:
1. Out-of-sample performance (WFO) is unstable
2. Volatility far exceeds return magnitude
3. No protective mechanism against regime shifts
4. Statistical evidence is weak (Sharpe < 0.1)

The strategy is not REJECTED because:
1. Signal-level evidence is positive
2. Executable returns exceed costs
3. Some structural stability in 2021 test period

---

## 13. Recommendations

### For Task 2 (Strategy Construction)

**Option 1: Proceed with Caution**
- Include Strategy 1 in the final portfolio, but weight it conservatively
- Combine with other strategies (e.g., mean-reversion) for diversification
- Treat as a "high-volatility, low-Sharpe" position

**Option 2: Conditional Entry**
- Add a regime filter (e.g., only enter BB01 breakouts during low-volatility regimes)
- This is NOT parameter optimization; it is risk management
- Requires separate validation study

**Option 3: Defer**
- Focus on mean-reversion strategies (PB07) which may have better Sharpe ratios
- Revisit BB01 after building a full portfolio; assess correlation with other strategies

### For Full-Sample Optimization (Not Recommended Yet)

Do NOT:
- Optimize BB01 thresholds
- Add stop losses or profit targets
- Extend to other asset classes or markets
- Assume past returns will persist

These are valid questions for Phase 2, but not yet.

---

## 14. Conclusion

Strategy 1 (BB01 Breakout) converts validated signal-level evidence into executable trades. The strategy is **not yet robust** due to:
- Regime dependence (2019 failure, Fold 1 sign reversal)
- Very low Sharpe ratio (0.0350)
- High maximum drawdown (-32.75%)
- Small executable sample (17 trades)

However, it is **economically plausible** and merits inclusion in Task 2 portfolio construction as a diversifier, provided it is combined with strategies of higher statistical quality.

The strategy demonstrates that even a validated signal (Welch t=2.03) can fail to produce robust executable returns when:
1. Event frequency is low
2. Regime dependence is high
3. Holding periods overlap, reducing trade independence
4. Market conditions shift (2019 vs 2020)

This is a critical learning for Task 2: separation of discovery evidence (signal-level) from strategy evidence (executable) is essential.

---

**Report Date:** September 12, 2026  
**Data Period:** 2018-01-02 to 2021-11-01  
**Auditor Notes:** All calculations performed without optimization. Causal timing maintained throughout. Walk-forward validation shows structural instability.
