# Task 2 Research Report: Supplied-Signal Alpha Research

**Date:** September 27, 2026  
**Status:** Corrected research submission  
**Primary conclusion:** The supplied signal library contains statistically interesting and structurally distinct signals, but the tested trading hypotheses do **not** demonstrate robust out-of-sample profitability under the corrected information set and causal next-open execution convention.

---

## 1. Executive Summary

Task 2 was rebuilt around the actual supplied information set: **20 anonymized signal columns** (PB01-PB08, BB01-BB07, VB01-VB05) observed alongside a single anonymized price series.

Earlier strategy implementations reconstructed technical/fundamental indicators from price or treated anonymized columns as named economic variables. Those implementations are excluded from the final evidence because they did not respect the supplied-signal information set.

The corrected research pipeline:

- uses supplied signal columns as the only predictive inputs;
- keeps price/OHLC available only for execution and return measurement;
- estimates training-window parameters only inside each WFO fold;
- observes signal at date *t* and executes at the next day's open;
- charges 0.05% transaction cost per side;
- uses fixed-horizon exits;
- evaluates five distinct research hypotheses;
- uses 5-fold rolling walk-forward validation with 504 training observations and 63 test observations per fold.

**Corrected WFO finding:** none of the five candidates has positive mean WFO return or positive mean WFO Sharpe. BB01, which showed a positive frozen-sample result, has 0/5 positive WFO folds.

This is a **negative alpha-validation result**, not evidence that the signal library is useless. It means that the particular trading rules tested here did not generalize sufficiently to be presented as validated profitable strategies.

---

## 2. Data and Information Set

### Supplied predictive data

- 866 common observations
- Date range: 2018-01-02 to 2021-11-01
- 20 supplied signals:
  - PB01-PB08
  - BB01-BB07
  - VB01-VB05

The strategy feature interface receives only the date and the explicitly declared supplied signal columns.

### Execution data

The cleaned OHLC price series is used for:

- next-open execution;
- open-to-open mark-to-market;
- fixed-horizon exit measurement;
- transaction-cost accounting.

Price/OHLC is **not** used to reconstruct Bollinger Bands, oscillators, P/B ratios, or other predictive features.

---

## 3. Causal Execution Convention

For a signal observed at date *t*:

1. Signal is generated using information available at *t*.
2. Entry or exit is executed at the **open of t+1**.
3. Position performance is marked using open-to-open returns.
4. Transaction cost is 0.05% on every executed side.
5. Holding horizons are encoded by the strategy exit signal.

This convention removes same-bar execution leakage.

The corrected event backtester charges entry and exit costs once each and does not repeatedly compound a trade against its entry price.

---

## 4. Research Hypotheses

Five hypotheses were implemented using the supplied signal library only.

| Candidate | Supplied inputs | Rule | Horizon |
|---|---|---|---:|
| BB01_Breakout_20D | BB01 | Long when BB01 > 0 | 20d |
| PB07_TailReversal_10D | PB07 | Long when PB07 is below the training-window 20th percentile | 10d |
| BB03_Reversal_10D | BB03 | Short when BB03 > 0 | 10d |
| MeanReversion_Composite_10D | BB03, PB07, BB04 | Training-only linear composite of supplied signals | 10d |
| BB03_RegimeFiltered_10D | BB03, VB02 | Short BB03 signal conditional on training-window VB02 median | 10d |

All strategy classes expose the required strategy interface and declare their predictive inputs explicitly.

### Parameter fitting

PB07 and VB02 thresholds are estimated on the training window only.

The composite weights are estimated on the training window only using a forward target constructed from the training observations.

No test-period target is used to fit a strategy.

---

## 5. Walk-Forward Design

Five rolling WFO folds were used:

- Training window: 504 observations
- Test window: 63 observations
- Test windows are chronological and non-overlapping
- Five complete folds
- 315 OOS observations across the five test windows

The WFO result is treated as the primary evidence. Full-sample frozen-fit performance is reported only as descriptive context.

---

## 6. Corrected WFO Results

| Strategy | Mean WFO Return | Mean WFO Sharpe | Positive Folds | OOS Trades |
|---|---:|---:|---:|---:|
| BB01_Breakout_20D | -3.29% | -0.56 | 0/5 | 5 |
| PB07_TailReversal_10D | -0.60% | -0.26 | 0/5 | 3 |
| BB03_Reversal_10D | -5.01% | -0.38 | 1/5 | 10 |
| MeanReversion_Composite_10D | -4.73% | -0.33 | 2/5 | 24 |
| BB03_RegimeFiltered_10D | -5.46% | -0.82 | 0/5 | 6 |

### Per-fold returns

**BB01:** -2.90%, 0.00%, -10.27%, -2.14%, -1.17%

**PB07:** -0.51%, -0.28%, -1.73%, -0.49%, 0.00%

**BB03:** -3.02%, -2.04%, -18.60%, -2.48%, +1.12%

**Composite:** +4.74%, -12.90%, -14.46%, +0.13%, -1.18%

**BB03 + VB02:** -3.02%, -4.26%, -18.60%, -1.41%, 0.00%

The fold-level results show substantial instability and very small trade counts. No candidate produces a consistent positive OOS result.

---

## 7. Frozen-Sample Results — Descriptive Only

The frozen full-sample results illustrate why WFO is necessary.

| Strategy | Frozen Return | Frozen Sharpe | Max DD | Trades |
|---|---:|---:|---:|---:|
| BB01 | +20.09% | +0.32 | -24.82% | 15 |
| PB07 | -29.83% | -0.34 | -30.61% | 20 |
| BB03 | -66.70% | -0.89 | -71.52% | 23 |
| Composite | -69.46% | -0.44 | -74.95% | 78 |
| BB03 + VB02 | -66.70% | -0.89 | -71.52% | 23 |

BB01 is the clearest example of the distinction: its +20.09% frozen-sample result does **not** survive chronological WFO validation.

Therefore the frozen-sample result is not used as evidence of validated alpha.

---

## 8. Earlier Signal-Level Statistical Research

Separate descriptive signal research was performed before strategy construction.

The strongest previously identified continuous-signal relationship was associated with the supplied signal library's tail/extreme states. A causal Q1-vs-non-Q1 analysis produced:

- 136 causal Q1 observations after minimum-history and edge handling;
- approximately +1.64 percentage-point 20-day forward-return spread;
- Welch t-statistic approximately 3.21;
- unadjusted p-value approximately 0.0015;
- 5,000 block-bootstrap resamples with block length 20;
- approximate 95% bootstrap interval of [-0.17%, +3.08%].

The interval includes zero. In addition, the broader 20-signal multiple-testing exercise did not produce an individual signal that survived Benjamini-Hochberg FDR at the stated 5% level.

These results are therefore treated as **research evidence and hypothesis-generation evidence**, not as proof of deployable alpha.

---

## 9. Orthogonality and Independence

The corrected candidate signal streams have very low pairwise Pearson correlations:

| | BB01 | PB07 | BB03 | Composite | Filtered |
|---|---:|---:|---:|---:|---:|
| BB01 | 1.000 | ~0.000 | -0.024 | 0.000 | -0.024 |
| PB07 | ~0.000 | 1.000 | 0.022 | 0.000 | 0.022 |
| BB03 | -0.024 | 0.022 | 1.000 | -0.042 | 1.000 |
| Composite | 0.000 | 0.000 | -0.042 | 1.000 | -0.042 |
| Filtered | -0.024 | 0.022 | 1.000 | -0.042 | 1.000 |

This indicates that the **trade-state streams are structurally different**, but it does not establish independent profitable alpha.

A particularly important negative finding is that the BB03 + VB02 filtered candidate is effectively identical to BB03 in the observed trade-state stream (correlation 1.000). The filter therefore did not create a meaningfully distinct trading stream in this sample.

Accordingly, the filtered candidate should not be treated as a new independent source of alpha.

---

## 10. Interpretation

The evidence separates into three levels:

### Level 1 — Signal structure

The anonymized signal library contains signals with different temporal behavior and low overlap.

### Level 2 — Statistical association

Some signal states show economically meaningful forward-return differences in descriptive testing.

### Level 3 — Trading strategy validation

The tested rules do not demonstrate robust OOS profitability after causal execution and transaction costs.

The project therefore does **not** claim that the five tested strategies are validated alpha strategies.

---

## 11. Negative Findings

The following are deliberate research conclusions rather than failures to report:

1. **BB01 frozen-sample performance does not generalize in WFO.**
2. **PB07 does not produce positive mean WFO performance under the corrected implementation.**
3. **BB03 reversal is consistently weak except for one small positive fold.**
4. **The learned composite does not improve OOS performance.**
5. **The VB02 regime filter does not materially change the BB03 trade stream.**
6. **No individual signal survived the broader multiple-testing correction.**
7. **Trade counts are too small in several folds to support strong inference.**
8. **Low signal-stream correlation does not translate into profitable diversification.**

These findings prevent overclaiming and identify the main areas requiring additional data or alternative hypotheses.

---

## 12. Why the Earlier Portfolio Result Is Excluded

An earlier research version reported a 70/30 PB07/BB01 portfolio with approximately 23.6% cumulative return and 0.67 Sharpe.

That result is **not part of the corrected Task 2 evidence**.

The earlier implementation reconstructed indicator definitions and used an information set inconsistent with the supplied anonymized signal library. It also used a different execution/accounting convention.

The corrected submission intentionally removes those results rather than presenting them as validated evidence.

---

## 13. Reproducibility

Primary corrected runner:

`quant_project/task2_corrected_runner.py`

Strategy implementations:

- `quant_project/strategies/alpha_01.py`
- `quant_project/strategies/alpha_02.py`
- `quant_project/strategies/alpha_03.py`
- `quant_project/strategies/alpha_04.py`
- `quant_project/strategies/alpha_05.py`
- `quant_project/strategies/signal_base.py`

Run:

```bash
python quant_project/task2_corrected_runner.py
```

Outputs:

- `research_output/TASK2_CORRECTED_RESULTS.json`
- `research_output/TASK2_RETURN_SPACE_CORRELATION.csv`

---

## 14. Final Task 2 Conclusion

The corrected Task 2 research demonstrates a complete signal-to-strategy workflow under the supplied information set, with explicit causal timing, training-only parameter estimation, transaction costs, and chronological walk-forward validation.

The primary empirical conclusion is:

> **The tested hypotheses did not establish robust out-of-sample profitability.**

This is intentionally a conservative conclusion. The research identifies potentially interesting signal states and structurally distinct candidates, but the available 866-observation sample and resulting trade counts are insufficient to justify presenting any candidate as a validated persistent alpha strategy.

The appropriate next research step would be to expand the hypothesis space or obtain a longer/more informative evaluation sample, rather than tuning the existing candidates until they produce a favorable backtest.

---

**END OF CORRECTED TASK 2 REPORT**
