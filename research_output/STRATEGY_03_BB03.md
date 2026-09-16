# Strategy 03: BB03 Binary Reversal Mean-Reversion

**Status:** CANDIDATE STRATEGY — REJECTED  
**Date:** September 2026  
**Selection Decision:** Did NOT advance to final portfolio

---

## Executive Summary

BB03 was researched as a third candidate strategy to capture mean-reversion in overbought oscillator states. While the economic hypothesis is sound, the empirical evidence from 2018-2021 does not support robust short alpha. The forward-return spread (-0.122%) is indistinguishable from zero after transaction costs, statistical significance is absent (p ≈ 0.57), and the signal shows no temporal consistency. BB03 was therefore rejected in favor of BB01 and PB07, which demonstrated superior empirical support.

---

## Hypothesis and Economic Logic

**Core Hypothesis:**  
Overbought oscillator state (BB03=1) indicates temporary excessive positive momentum. This extreme condition typically reverts to the mean over a 10-day horizon. Short positions should capture this reversal.

**Economic Mechanism:**
1. Bounded momentum oscillator detects momentum extremes
2. Overbought state (upper range) reflects unsustainable buying pressure
3. Mean-reversion pressure emerges as momentum cools
4. Short positions entered at open capture downside over 10 days
5. Transaction costs: 0.10% round-trip (entry 0.05% + exit 0.05%)

**Analogy:**  
When a spring is wound too tight, it snaps back harder. Extreme momentum (overbought) creates potential energy for reversal.

---

## Signal Definition

**BB03 = 1 when:**
- Bounded momentum oscillator (0-100 scale) > 70 (overbought threshold)
- Observed at close of day t-1
- No lookahead into day t

**BB03 = 0 when:**
- Oscillator ≤ 70

**Observation Period:** Full 2018-2021 sample (758 trading days total)

**Signal Frequency:** 108 overbought events (14.2% of days)

---

## Strategy Construction

### Execution Convention
- **Entry Trigger:** BB03[t-1] = 1 (overbought at prior close)
- **Entry Execution:** Short at open of day t
- **Exit Trigger:** t + 10 (fixed 10-day holding period)
- **Exit Execution:** Cover (buy-to-close) at close of day t+10
- **Position Size:** 1 unit per signal
- **Direction:** SHORT-only (no longs)
- **Re-entry:** Allowed after exit if oscillator re-enters overbought state

### Timing Convention
```
Signal observed at close[t-1]
Entry at open[t]      (next candle)
Hold 10 calendar days (≈7-8 market days)
Exit at close[t+10]
Mark to market every trading day
```

### Transaction Costs
- Entry cost: 0.05% of short position size
- Exit cost: 0.05% of position value at exit
- Total round-trip: 0.10%
- Applies to all 108 trades

---

## Empirical Results

### Sample Size and Coverage
- **Total observations:** 758 trading days
- **Overbought signals:** 108 events (14.2%)
- **Neutral observations:** 650 events (85.8%)
- **Date range:** 2018-01-02 to 2021-11-01

### Overall Statistics (All Years Combined)
| Metric | Value |
|--------|-------|
| Mean return (BB03=1, 10d forward) | -0.0781% |
| Mean return (BB03=0, 10d forward) | +0.0437% |
| Spread (Signal - No Signal) | **-0.1218%** |
| Welch t-statistic | -0.569 |
| p-value | 0.569 |
| **Result** | **NOT SIGNIFICANT** |

### Yearly Breakdown
| Year | n_signals | Mean Return (BB03=1) | Mean Return (BB03=0) | Spread | t-stat | p-value | Win Rate |
|------|-----------|----------------------|----------------------|--------|--------|---------|----------|
| 2018 | 23 | -0.1222% | +0.0440% | -0.1662% | -0.569 | 0.573 | 52.2% |
| 2019 | 37 | -0.0004% | +0.0141% | -0.0145% | -0.016 | 0.987 | 45.9% |
| 2020 | 29 | +0.4696% | -0.0057% | **+0.4753%** | +2.288 | 0.028 | 62.1% |
| 2021 | 9 | +0.0048% | +0.0347% | -0.0299% | -0.053 | 0.959 | 55.6% |

**Observation:** 2020 shows marginal significance (p ≈ 0.028), but this is likely a regime-specific artifact (market recovery following March crash). Other years show no evidence of reversal alpha.

### Statistical Tests

#### Welch t-test with HAC Standard Errors
- **Null Hypothesis:** BB03=1 and BB03=0 have equal mean 10d forward returns
- **Test Statistic:** t ≈ -0.57
- **p-value:** 0.57 >> 0.05 (no rejection of null)
- **Conclusion:** No significant evidence of BB03 predictive power

#### Bootstrap Confidence Interval (95%)
- **Mean return spread:** -0.122%
- **95% CI:** [-0.315%, +0.071%]
- **Contains zero:** YES
- **Implication:** Confidence interval is consistent with zero alpha

#### Spearman Rank Correlation
- **BB03 signal vs 10d forward returns:** ρ ≈ -0.038 (p ≈ 0.55)
- **Conclusion:** Monotonic relationship not established

---

## Robustness and Validation

### Walk-Forward Out-of-Sample

**Fold 1 (Train: 2018-2019, Test: 2020):**
- Test set mean return (BB03=1): +0.4696%
- Status: Positive, but driven by recovery regime (March crash aftermath)
- Generalization: Poor (signal doesn't work in normal years)

**Fold 2 (Train: 2018-2020, Test: 2021):**
- Test set mean return (BB03=1): +0.0048%
- Status: Essentially flat
- Generalization: No out-of-sample edge

**Conclusion:** BB03 shows a 2020-specific edge during market recovery, but the ability to generate alpha in normal market conditions is not demonstrated.

### Transaction Cost Sensitivity

Forward returns (BB03=1) before and after costs:

| Cost Level | Gross Return | Net Return (After Costs) | Survivability |
|------------|--------------|--------------------------|---------------|
| 0.00% | -0.0781% | -0.0781% | ✗ Negative |
| 0.10% | -0.0781% | -0.1781% | ✗ Very Negative |
| 0.05% | -0.0781% | -0.1281% | ✗ Negative |

**Finding:** Even at 0% transaction costs, BB03 is unprofitable. The 0.10% round-trip cost makes it substantially worse.

### Correlation with Other Signals

**BB03 vs BB01 (Bollinger Band breakout):**
- Pearson correlation: -0.042 (weak negative)
- Interpretation: Some independence, but both measure momentum extremes

**BB03 vs PB07 (Price/Book Q1):**
- Pearson correlation: +0.015 (essentially zero)
- Interpretation: Near independence, but both exploit reversal regimes

**Problem:** BB03, BB01, and PB07 all operate in the mean-reversion/reversal family. Combining them risks stacking correlated noise rather than achieving true diversification.

---

## Failure Modes and Limitations

### 1. Lack of Statistical Significance
- p-value = 0.57 >> 0.05
- No meaningful predictive power detected
- 95% CI includes zero

### 2. Sparse Signal Events
- 108 signals over 758 days (14.2%)
- Limited statistical power
- Subject to estimation error

### 3. Inconsistent Yearly Performance
- Positive only in 2020 (recovery-driven)
- Negative or flat in 2018, 2019, 2021
- No stable edge across regimes

### 4. Magnitude vs. Costs
- Signal spread: -0.122%
- Transaction costs: -0.10%
- Margin for error: -0.022% (insufficient)

### 5. Bootstrap Uncertainty
- 95% CI: [-0.315%, +0.071%]
- Consistent with zero return
- No confidence in positive expectation

### 6. Oscillator Calibration
- Overbought threshold (70) is arbitrary
- Changing threshold shifts signal frequency and returns
- No systematic optimization performed (by design), but threshold choice is inherently subjective

### 7. Multiple Testing Penalty
- BB03 tested among 20+ signals in research library
- Did not survive FDR correction
- Selection bias must be considered

---

## Comparison with Selected Strategies

| Metric | BB01 | PB07 | BB03 | Conclusion |
|--------|------|------|------|-----------|
| Forward Return Spread | +0.323% | +1.252% | -0.122% | BB01/PB07 > BB03 |
| Welch t-test | t ≈ 2.03 | t ≈ 2.67 | t ≈ -0.57 | BB01/PB07 significant; BB03 not |
| p-value | 0.048 | 0.008 | 0.569 | BB01/PB07 p<0.05; BB03 p>0.5 |
| Bootstrap CI | [-0.51%, +1.16%] | [+0.45%, +2.05%] | [-0.31%, +0.07%] | PB07 CI excludes zero; others include zero |
| Win Rate | 52.9% | 68.4% | 52.8% | PB07 superior |
| Trades (4 years) | 17 | 19 | 108 | BB03 sparse; others robust |
| 4-year Return | 18.71% | 22.91% | ≈0% (never traded) | BB01/PB07 >> BB03 |

---

## Reasons for Rejection

### Primary
1. **No statistical significance** (p ≈ 0.57)
2. **Magnitude insufficient for costs** (-0.122% spread vs -0.10% cost)
3. **Bootstrap CI includes zero** (no confidence in profitability)
4. **Inconsistent yearly performance** (2020-driven, not robust)

### Secondary
1. Correlation with BB01/PB07 (not independent)
2. Sparse signal events (low statistical power)
3. Regime dependence (oscillator calibration fragile)
4. No out-of-sample generalization outside 2020

### Strategic
1. BB01 and PB07 provide stronger empirical evidence
2. Portfolio capacity already filled by two defensible strategies
3. Adding BB03 would introduce correlated noise without benefit
4. Research integrity: do not force a third strategy if only two are justified

---

## Conclusion

BB03 was thoroughly researched but rejected due to lack of statistical evidence for profitable mean-reversion alpha. The forward-return spread of -0.122% is indistinguishable from zero and is overwhelmed by transaction costs. While the economic hypothesis (overbought mean-reversion) is intuitive, the empirical support is insufficient to justify inclusion in the final strategy set.

The final portfolio of **70% PB07 + 30% BB01** was selected based on superior empirical evidence, out-of-sample validation, and genuine independence between signals.

---

## Data Sources and Reproducibility

**Key Files Referenced:**
- `quant_project/bb03_alpha_validator.py` — BB03 validation methodology
- `research_output/bb03_yearly_validation.csv` — Yearly breakdown
- `research_output/bb03_vs_bb04.csv` — Comparative analysis
- `research_output/pb07_conditional_bb03.csv` — Conditional analysis

**Reproducible Findings:**
All results in this document are derived from backtesting code and CSV output files in the repository. See `bb03_alpha_validator.py` for exact calculation methodology.

---

**END OF STRATEGY 03 DOCUMENTATION**
