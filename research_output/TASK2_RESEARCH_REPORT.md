# Task 2 Research Report: Supplied-Signal Alpha Research

**Date:** September 28, 2026  
**Status:** Final Task 2 research report  
**Dataset:** 986 synchronized signal/price observations, 2018-01-02 to 2021-11-01

## 1. Executive Summary

Task 2 was evaluated using the supplied anonymized signal library only. The final run evaluates **9 strategy hypotheses** with a chronological **7-fold walk-forward validation** design.

The research uses:

- 20 supplied predictive signals: PB01-PB08, BB01-BB07, VB01-VB05
- signal information observed at date *t*
- execution at the next day's open
- open-to-open return marking
- 0.05% transaction cost per executed side
- 504-observation training windows
- 63-observation non-overlapping test windows
- training-window-only parameter fitting
- no price/OHLC-derived predictive features

The available synchronized dataset contains **986 rows**. No 1000-row price file is present in the repository, so the 986-row synchronized dataset is the final reproducible Task 2 input used by the runner.

The results are reported descriptively below. No strategy is presented as a guaranteed or validated future source of alpha.

## 2. Data and Information Set

### Predictive data

- 986 synchronized observations
- Date range: 2018-01-02 to 2021-11-01
- 20 supplied signals:
  - PB01-PB08
  - BB01-BB07
  - VB01-VB05

The strategy layer receives supplied signals as predictive inputs. Price/OHLC is used for execution and return measurement rather than for reconstructing predictive indicators.

### Data alignment

The final files used by the runner are:

- `data/signals_cleaned.csv`: 986 rows
- `data/price_cleaned.csv`: 986 rows
- common dates: 986
- identical date range: 2018-01-02 to 2021-11-01

## 3. Causal Execution Convention

For a signal observed at date *t*:

1. The signal is generated from information available at *t*.
2. Any resulting position change is executed at the open of *t+1*.
3. Position performance is marked open-to-open.
4. Transaction cost is 0.05% per executed side.
5. Strategy-specific holding/exit logic is applied without using future test information.

This convention avoids same-bar execution leakage.

## 4. Strategy Research Set

| Strategy | Main supplied inputs | Horizon / logic |
|---|---|---|
| BB01_Breakout_20D | BB01 | 20-day breakout |
| PB07_TailReversal_10D | PB07 | 10-day tail reversal |
| BB03_Reversal_10D | BB03 | 10-day reversal |
| MeanReversion_Composite_10D | BB03, PB07, BB04 | 10-day composite |
| BB03_RegimeFiltered_10D | BB03, VB02 | 10-day regime-filtered reversal |
| BB04_Reversal_5D | BB04 | 5-day reversal |
| VB03_Continuation_5D | VB03 | 5-day continuation |
| BB07_UpperTail_10D | BB07 | 10-day upper-tail strategy |
| PB07_BB03_BB04_Conditional | PB07, BB03, BB04 | Conditional desired-position rules |

The conditional strategy uses fixed rules encoded in the strategy implementation; its rules are not fitted on the test windows.

## 5. Walk-Forward Design

The final runner uses:

- 7 chronological folds
- 504 observations for training
- 63 observations for each test window
- non-overlapping test windows
- parameters fitted using the training window only

The seven test windows run from 2019-12-20 through 2021-09-03. The remaining synchronized observations after the final test window are not included in the seven complete WFO folds because the runner requires a complete 504 + 63 window.

## 6. Full-Sample Frozen-Fit Results

These figures are descriptive and should not be interpreted as out-of-sample validation.

| Strategy | Return | Sharpe | Max DD | Trades |
|---|---:|---:|---:|---:|
| BB01_Breakout_20D | -3.12% | -0.035 | -19.52% | 17 |
| PB07_TailReversal_10D | +59.68% | 1.370 | -10.00% | 20 |
| BB03_Reversal_10D | +13.21% | 0.443 | -9.04% | 25 |
| MeanReversion_Composite_10D | -3.81% | 0.015 | -23.34% | 89 |
| BB03_RegimeFiltered_10D | +13.21% | 0.443 | -9.04% | 25 |
| BB04_Reversal_5D | -5.86% | -0.216 | -12.60% | 24 |
| VB03_Continuation_5D | +21.90% | 0.857 | -5.52% | 16 |
| BB07_UpperTail_10D | +6.34% | 0.203 | -18.68% | 23 |
| PB07_BB03_BB04_Conditional | +16.59% | 0.477 | -11.38% | 62 |

The difference between frozen-sample performance and WFO performance is material for several candidates, which is why the WFO results below are the appropriate evidence for generalization.

## 7. Walk-Forward Results

| Strategy | Mean WFO Return | Mean WFO Sharpe | Positive-Return Folds |
|---|---:|---:|---:|
| BB01_Breakout_20D | -3.23% | -1.107 | 1/7 |
| PB07_TailReversal_10D | +5.26% | +1.769 | 3/7 |
| BB03_Reversal_10D | +2.37% | +1.012 | 6/7 |
| MeanReversion_Composite_10D | -0.32% | -0.110 | 3/7 |
| BB03_RegimeFiltered_10D | +1.35% | +0.391 | 4/7 |
| BB04_Reversal_5D | -0.38% | -0.146 | 1/7 |
| VB03_Continuation_5D | +0.29% | +0.393 | 2/7 |
| BB07_UpperTail_10D | +0.50% | +0.652 | 3/7 |
| PB07_BB03_BB04_Conditional | +3.11% | +1.667 | 6/7 |

A positive fold count means the fold's realized total return was above zero. It does not by itself establish statistical significance or future profitability.

## 8. Return-Space Correlation

The runner measures candidate dependence using realized daily return streams rather than raw signal-state correlation. The complete matrix is stored in:

`research_output/TASK2_RETURN_SPACE_CORRELATION.csv`

Notable structural relationships include:

- BB03_Reversal_10D and BB03_RegimeFiltered_10D have correlation 1.000 because the two realized return streams are identical in this implementation.
- PB07_TailReversal_10D and MeanReversion_Composite_10D have correlation approximately 0.525.
- BB01_Breakout_20D and BB03_Reversal_10D have correlation approximately -0.499.
- VB03_Continuation_5D has relatively low correlation with the other candidate streams in several pairings.

Correlation describes dependence between realized streams; it does not establish independent alpha.

## 9. Research Interpretation

The final Task 2 evidence shows that different supplied-signal hypotheses produce materially different return streams and WFO behavior. Several candidates have positive mean WFO returns, while others are negative over the same chronological validation framework.

The evidence should therefore be presented as **comparative research results**, not as a claim that any single strategy is guaranteed to work going forward.

The conditional strategy records positive realized returns in 6 of 7 WFO folds, with no trade activity in one fold. PB07 and BB03 also show positive mean WFO returns, while their fold-level behavior differs materially.

The frozen-sample results should remain secondary because they use a fit informed by the complete sample.

## 10. Reproducibility

Canonical implementation:

- `quant_project/task2_corrected_runner.py`

Canonical outputs:

- `research_output/TASK2_CORRECTED_RESULTS.json`
- `research_output/TASK2_RETURN_SPACE_CORRELATION.csv`

Input files:

- `data/signals_cleaned.csv`
- `data/price_cleaned.csv`

An archived 986-row baseline is retained separately as `TASK2_RESULTS_986_BASELINE.json` in the working tree for audit comparison.

## 11. Task 3 Boundary and final checkpoint reference

Task 3 has since been rebuilt on the corrected Task 2 return streams. Its canonical report is `research_output/TASK3_PORTFOLIO_REPORT.md`, with fold-level model discipline and permutation-null diagnostics in `research_output/task3_model_discipline.json` and `research_output/task3_null_baseline.json`. See `CHECKPOINT_DOCUMENTATION.md` for the reconciled status across Tasks 1–3. This Task 2 report remains the record of the Task 2 run and its results; Task 3 does not change those Task 2 findings.

