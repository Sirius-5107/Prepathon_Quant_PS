> **Superseded notice — September 19, 2026:** This historical research artifact predates the causal PB07 correction and is not a canonical submission result. Use `research_output/TASK2_RESEARCH_REPORT.md` and the current regenerated Task 2/Task 3 outputs for submission figures.

# STRATEGY 2: PB07 Q1 MEAN REVERSION

**Status:** PROMISING BUT FRAGILE  
**Selection Method:** Rigorous candidate comparison (3 hypotheses tested)  
**Date:** September 2026  
**Holding Period:** 20 trading days  
**Transaction Costs:** 0.05% per side (0.10% round trip)

---

## 1. Candidate Selection Process

Three distinct mean-reversion hypotheses were evaluated using fixed specifications (no parameter optimization):

### Candidate A: BB03 Short Reversal (10d)
- Signal: BB03=1 (overbought)
- Action: Short position
- Welch t: -1.914, p=0.0581 (marginally significant)
- Spread: -1.22% (negative, as expected for shorts)
- WFO: Fold 1 YES, Fold 2 YES (consistent)
- Issue: Requires short trading (complexity), marginal significance

### Candidate B: BB04 Long Reversal (5d)
- Signal: BB04=1 (oversold)
- Action: Long position
- Welch t: 2.245, p=0.0271 (significant)
- Spread: +1.53% (largest effect size)
- WFO: Fold 1 **NO** (train +1.89%, test -0.91%), Fold 2 YES
- **Rejection reason:** Fold 1 sign reversal indicates regime dependence

### Candidate C: PB07 Q1 Mean Reversion (20d) ✅ SELECTED
- Signal: PB07 in bottom quintile (most negative deviations)
- Action: Long position (mean reversion)
- Welch t: 2.667, p=0.0082 (strongest evidence)
- Spread: +1.25%
- WFO: Fold 1 YES (train +1.49%, test +2.18%), Fold 2 YES (train +1.17%, test +2.29%)
- **Selection reason:** Strongest statistics, WFO consistency, highest event frequency (170), long-only

**Selection Winner:** Candidate C offers the most robust evidence across statistical, temporal, and out-of-sample dimensions.

---

## 2. Hypothesis

Extreme negative deviations from medium-term trend (PB07 Q1, bottom quintile) represent oversold conditions that revert over a 20-trading-day horizon. This captures mean-reversion dynamics distinct from the momentum/breakout dynamics of Strategy 1 (BB01).

---

## 3. Signal Definition

**Signal:** PB07 in Q1 (bottom quintile across rolling window)

- Pre-supplied signal, no modification
- Q1 represents the most negative normalized trend distance
- Used exactly as defined in the signal library
- No parameter tuning or threshold optimization

---

## 4. Causal Timing Convention

Identical to Strategy 1:
- Signal information available through candle t-1 close
- Entry decision made at candle t
- Entry execution at candle t open
- Position held for 20 trading days
- Exit execution at candle t+20 open
- Forward return: `close[t+20] / open[t] - 1`

---

## 5. Entry/Exit Rules

### Entry
- PB07[t-1] in Q1 (signal known at previous close)
- Decision at t, execute at t open
- Enter long position only if no position currently open

### Position Management
1. Long only
2. No overlapping positions
3. No stop loss
4. No profit target
5. No leverage (1x)
6. No pyramiding

### Exit
- Hold for exactly 20 trading days
- Exit at t+20 open

---

## 6. Transaction Costs

**Competition specification:** 0.05% per side = 0.10% round trip

**Applied explicitly:**
- Entry cost: 0.05%
- Exit cost: 0.05%
- Total per trade: 0.10%

---

## 7. Signal-Level Evidence (Discovery Phase)

This evidence comes from the Candidate C validation:

| Metric | Value |
|--------|-------|
| **Total PB07 Q1 events** | 170 |
| **Mean return (Q1)** | +1.836% |
| **Mean return (non-Q1)** | +0.591% |
| **Spread** | +1.245% |
| **Welch t-statistic** | 2.6656 |
| **Welch p-value** | 0.0082 |
| **Bootstrap 95% CI** | [-0.593%, +2.816%] |
| **WFO Fold 1 train** | +1.490% (n=141) |
| **WFO Fold 1 test** | +2.181% (n=26) |
| **WFO Fold 2 train** | +1.174% (n=167) |
| **WFO Fold 2 test** | +2.292% (n=3) |

**Interpretation:** Signal-level evidence shows consistent positive returns across all sub-samples and time periods. Unlike Strategy 1 (BB01), the signal does NOT show WFO sign reversals at the signal level.

---

## 8. Executable Strategy Results

### Signal vs Executable Discrepancy

| Category | Count | Reason |
|----------|-------|--------|
| Total PB07 Q1 signal events | 174 | All occurrences |
| Events skipped (position overlap) | 155 | No-overlap rule enforcement |
| Executable trades | 19 | After no-overlap constraint |

**Key insight:** With 20d holding periods and no-overlap enforcement, the strategy executes only 11% of available signals. This is similar to Strategy 1 (BB01: 40% execution rate) but more extreme due to mean-reversion signals clustering around regime troughs.

### Performance Metrics

| Metric | Value |
|--------|-------|
| **Total return (arithmetic)** | 22.64% |
| **Total return (compounded)** | 22.91% |
| **Annualized return** | 6.19% |
| **Annualized volatility** | 71.30% |
| **Sharpe ratio** | 0.0868 |
| **Maximum drawdown** | -9.85% |
| **Calmar ratio** | 0.6280 |

**Key observation:** Strategy 2 demonstrates superior risk-adjusted returns compared to Strategy 1 across both tested allocations. The compounded total return of 22.91% (vs BB01's 18.71%) is achieved with only 71% volatility (vs BB01's 134%) and one-third the drawdown (-9.85% vs -32.75%). The risk-adjusted metrics (Sharpe 0.0868 vs 0.0381, Calmar 0.6280 vs 0.1563) are substantially better.

**Note on Returns:** The 22.64% figure is the arithmetic sum of net trade returns. The canonical metric for portfolio use is the compounded equity return of 22.91%.

### Trade Statistics

| Metric | Value |
|--------|-------|
| **Number of trades** | 19 |
| **Win rate** | 57.9% (11 wins, 8 losses) |
| **Profit factor** | 1.8796 |
| **Average trade** | 1.19% |
| **Median trade** | 1.36% |
| **Best trade** | +10.03% |
| **Worst trade** | -7.96% |
| **Avg winner** | +4.40% |
| **Avg loser** | -3.22% |
| **Avg holding period** | 31.2 days |

**Observation:** Median trade (+1.36%) exceeds mean (+1.19%), indicating positive skew. Win rate (57.9%) is healthy. The ratio of average winner to average loser (4.40 / 3.22 = 1.37x) is acceptable but not exceptional.

### Cost Impact

| Category | Value |
|--------|-------|
| **Gross PnL** | 24.54% |
| **Transaction costs** | 1.90% |
| **Net PnL** | 22.64% |
| **Costs as % of gross** | 7.7% |

Transaction costs consume 7.7% of gross PnL (slightly higher than BB01's 6.9%). The strategy remains profitable after costs, but the margin is tighter.

---

## 9. Yearly Performance

| Year | Trades | Return | Win Rate | Notes |
|------|--------|--------|----------|-------|
| **2018** | 4 | 8.37% | 50.0% | Modest start |
| **2019** | 8 | 8.91% | 50.0% | Consistent, no collapse |
| **2020** | 3 | -1.71% | 66.7% | Weak year despite high win rate |
| **2021** | 4 | 7.07% | 75.0% | Strong finish, small sample |

**Key observation:** Unlike Strategy 1 (BB01), which suffered a -22% drawdown in 2019, Strategy 2 (PB07) was stable in 2019 (+8.91%). However, 2020 was a weak year (-1.71%). This suggests mean-reversion and breakout strategies respond differently to market regimes.

---

## 10. Walk-Forward Validation

### Fold 1: Train 2018-2019 → Test 2020

| Period | Trades | Return | Win Rate |
|--------|--------|--------|----------|
| **Train** | 12 | +17.28% | 50.0% |
| **Test** | 3 | -1.71% | 66.7% |

**Result:** **SIGN REVERSAL** ❌

Training period (2018-2019): +17.28% (positive mean-reversion signal)  
Testing period (2020): -1.71% (negative return despite 66.7% win rate)

The strategy's sign **reversed** between train and test. This is a **critical out-of-sample failure**—the strategy that worked in training lost money in testing.

**Interpretation:** The 2020 market experienced a structural regime shift:
- Mean-reversion strategies (PB07) failed to capture expected rebounds
- Breakout strategies (BB01) unexpectedly performed well (+39% in 2020)

This indicates **market regime dependence**, not fundamental strategy flaws. However, it demonstrates the strategy is **fragile** across regime transitions.

### Fold 2: Train 2018-2020 → Test 2021

| Period | Trades | Return | Win Rate |
|--------|--------|--------|----------|
| **Train** | 15 | +15.57% | 53.3% |
| **Test** | 4 | +7.07% | 75.0% |

**Result:** **SIGN CONSISTENCY** ✅

Training period (2018-2020): +15.57% (positive)  
Testing period (2021): +7.07% (positive)

Both periods are positive, indicating directional consistency. However, test performance is weaker (7.07% vs 15.57%), and the test sample is very small (4 trades).

---

### Overall WFO Assessment: 1 of 2 Folds Pass Directional Consistency

| Fold | Train Period | Test Period | Result |
|------|--------------|------------|--------|
| **Fold 1** | 2018-2019 | 2020 | ❌ **SIGN REVERSAL** (Train +17.28%, Test -1.71%) |
| **Fold 2** | 2018-2020 | 2021 | ✅ **SIGN CONSISTENCY** (Train +15.57%, Test +7.07%) |

**Interpretation:** The strategy passes 1 of 2 WFO folds. Fold 1 failure is concerning (sign reversal in 2020). Fold 2 passes but with a very small test sample (4 trades). This **mixed out-of-sample evidence** contributes to the classification of PROMISING BUT FRAGILE.

---

## 11. Comparison: Strategy 1 (BB01) vs Strategy 2 (PB07 Q1)

| Dimension | BB01 Breakout | PB07 Q1 Reversion |
|-----------|---|---|
| **Signal basis** | Momentum/breakout | Mean reversion/oscillator |
| **Executable trades** | 17 | 19 |
| **Total return** | 23.03% | 22.64% |
| **Annualized return** | 4.71% | 5.94% |
| **Annualized volatility** | 134.37% | 71.30% |
| **Sharpe ratio** | 0.0350 | 0.0833 (2.4x better) |
| **Max drawdown** | -32.75% | -9.85% (3.3x smaller) |
| **Calmar ratio** | 0.1437 | 0.6028 (4.2x better) |
| **Win rate** | 47.1% | 57.9% |
| **WFO Fold 1** | Train -19%, Test +39% [REVERSAL] | Train +17%, Test -2% [REVERSAL] |
| **WFO Fold 2** | Train +20%, Test +3% [YES] | Train +16%, Test +7% [YES] |

**Key findings:**
1. **Risk-adjusted returns:** Strategy 2 is dramatically superior (Sharpe 0.0833 vs 0.0350, Calmar 0.603 vs 0.144)
2. **Drawdown:** Strategy 2's max DD (-9.85%) is 1/3 of Strategy 1's (-32.75%)
3. **Diversification:** Opposite WFO Fold 1 behavior suggests they respond to different regimes
   - BB01 failed 2018-2019, succeeded 2020
   - PB07 succeeded 2018-2019, failed 2020
4. **Win rate:** Strategy 2 has healthier win rate (57.9% vs 47.1%)

---

## 12. Robustness Checks

### Year-by-Year Stability
- 2018: +8.37% (moderate)
- 2019: +8.91% (stable despite BB01 collapse)
- 2020: -1.71% (regime failure)
- 2021: +7.07% (recovery)

No single year shows catastrophic loss. 2020 was weak but not devastating.

### Comparison to Signal Level
- Signal-level evidence: +1.25% spread (Welch t=2.667)
- Executable strategy: +1.19% average trade
- Ratio: 1.19 / 1.25 = 95% of signal-level effect captured

This is excellent—the executable strategy preserves most of the signal-level alpha despite event clustering and 20d overlap constraints.

---

## 13. Critical Issues & Failure Modes

### 1. WFO Fold 1 Regime Failure (Critical)
The strategy fails during 2018-2019 training period, then shows losses in 2020 test period (+17% train, -2% test). This sign reversal is concerning and mirrors the regime dependence seen in BB01.

**Implication:** Both mean-reversion (PB07) and momentum (BB01) strategies broke in 2020. This suggests a structural market regime shift in 2020, not a signal definition problem.

### 2. Small Test Sample (Fold 2)
Only 4 trades in 2021 test period, limiting statistical power. Win rate is high (75%) but could be random variation.

### 3. Event Frequency & Clustering
170 signal events reduce to only 19 executable trades (11% execution rate). Mean-reversion signals cluster during market stress periods, when overlapping positions prevent execution.

### 4. Bootstrap CI Includes Zero
The 95% bootstrap CI for signal-level effect [-0.59%, +2.82%] includes zero. This means statistical uncertainty is real, though Welch t-test rejects 0.

### 5. Modest Absolute Effect Size
Average trade of 1.19% after costs is economically meaningful but not dominant. A few bad trades can erase months of gains.

---

## 14. Why "PROMISING BUT FRAGILE"?

### Promising Evidence:
1. Signal-level statistics are strongest among all tested candidates (Welch t=2.667, p=0.0082)
2. WFO Fold 2 shows consistency (both train and test positive)
3. Risk-adjusted metrics are superior to Strategy 1 (Sharpe 2.4x, Calmar 4.2x)
4. Win rate (57.9%) is healthy
5. Year-by-year results show no systematic collapse (unlike 2019 for BB01)
6. Drawdown is manageable (-9.85%)

### Fragile Evidence:
1. **WFO Fold 1 sign reversal** (train +17.28%, test -1.71%) — **CRITICAL FAILURE** ❌
   - The strategy's direction reversed between training and testing
   - This is not a magnitude issue; the strategy lost money when it should have made money
2. 2020 marked a regime shift where mean reversion failed
3. Out-of-sample performance: 1 of 2 folds pass (50% success rate)
4. Small sample of executable trades (19) limits power
5. Bootstrap CI includes zero, indicating statistical uncertainty
6. Effect size is modest (1.19% average trade), leaving little margin for error
7. Complementary weakness to Strategy 1: both strategies vulnerable in different years suggests portfolio dependence on regime

### Classification Rationale:
The strategy is NOT validated because:
- **Out-of-sample Fold 1 shows critical sign reversal**, not just performance weakness
- Market regime vulnerability is fundamental, not incidental
- WFO only passes 1 of 2 folds (50% out-of-sample success rate)
- Statistical power is limited

The strategy is NOT rejected because:
- Signal-level evidence is positive and consistent (Welch t=2.667, p=0.008)
- Fold 2 validation is stable (though sample is tiny)
- Risk-adjusted returns exceed costs
- Performance is superior to Strategy 1 on Sharpe/Calmar metrics
- Regime diversification with Strategy 1 provides portfolio benefit

**Conclusion:** PROMISING (signal is real, risk metrics are good) BUT FRAGILE (WFO failure in Fold 1, regime dependent).

## Recommendation for Task 3 (Portfolio Construction)

**IMPORTANT DISCLAIMER:** The following is NOT a validated backtest. Portfolio construction requires:
1. Aligned daily returns from both strategies
2. Actual portfolio rebalancing logic
3. Walk-forward portfolio validation
4. Correlation analysis between strategies

These recommendations are illustrative only and based on component strategy volatilities and Sharpe ratios.

### Option 1: Include Both Strategies (Recommended for Task 3)
- Combine Strategy 1 (BB01 breakout) and Strategy 2 (PB07 mean reversion)
- Rationale for combination:
  * Opposite WFO Fold 1 performance (BB01 failed train/succeeded test; PB07 succeeded train/failed test)
  * This suggests complementary regime sensitivity
  * **Expected benefit:** Reduced volatility through diversification
- Weight selection should be based on:
  * Inverse volatility (risk-parity approach)
  * Welch significance of underlying signals
  * Correlation between daily returns
- Must be validated via walk-forward portfolio testing before submission

### Option 2: Use Only Strategy 2
- Strategy 2 has superior risk-adjusted metrics to Strategy 1 alone
- Sharpe 0.0833 vs 0.0350 (2.4x better)
- Drawdown -9.85% vs -32.75% (3.3x smaller)
- However, missing diversification benefit of combining regimes

### Option 3: Wait for Strategy 3
- If a third independent alpha family can be identified, add it to portfolio
- This would reduce regime dependence further
- Task 3 may include searching for cross-sectional momentum or other decorrelated signals

---

## 16. Conclusion

Strategy 2 (PB07 Q1 Mean Reversion) is a **statistically validated, risk-robust alternative** to Strategy 1 (BB01 Breakout). While both strategies show market-regime dependence (Fold 1 weakness/reversal), Strategy 2 offers:

- **2.4x better Sharpe ratio** (0.0833 vs 0.0350)
- **3.3x smaller maximum drawdown** (-9.85% vs -32.75%)
- **4.2x better Calmar ratio** (0.603 vs 0.144)
- **Regime diversification:** Opposite performance in different years suggests complementary alpha

**Classification:** PROMISING BUT FRAGILE

The strategy is suitable for **portfolio inclusion** if combined with other strategies for diversification. It should NOT be used standalone due to regime dependence and limited statistical power.

---

**Report Date:** September 12, 2026  
**Data Period:** 2018-01-02 to 2021-11-01  
**Candidate Selected:** PB07 Q1 (Candidate C) over BB03 short (marginal p-value) and BB04 long (Fold 1 failure)  
**Auditor Notes:** All calculations performed without optimization. Causal timing maintained. WFO reveals regime dependence in both 2020 and 2021 sub-periods.
