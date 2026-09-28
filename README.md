# Inter-IIT Quantitative Finance Prepathon

## Current Project Status

**Updated:** September 28, 2026

- **Task 1:** Complete and frozen.
- **Task 2:** Final research run completed on the synchronized repository dataset.
- **Task 3:** Rebuilt on the corrected nine-strategy Task 2 return matrix; rolling OOS model-discipline checks are included.

## Task 2 — Final Canonical Setup

The final Task 2 pipeline uses only the supplied anonymized signal library as predictive inputs.

- Signals: PB01-PB08, BB01-BB07, VB01-VB05
- Synchronized observations: **986**
- Date range: **2018-01-02 to 2021-11-01**
- Price rows: **986**
- Signal rows: **986**
- Common dates: **986**
- Strategies tested: **9**
- Walk-forward folds: **7**
- Training window: **504 observations**
- Test window: **63 observations**
- Execution: signal at *t* -> next-open execution at *t+1*
- Return marking: open-to-open
- Transaction cost: **0.05% per executed side**
- Parameter fitting: training-window only

No 1000-row price file is present in the repository; the 986-row synchronized dataset is therefore the reproducible dataset used by the final runner.

## Final WFO Results

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

These figures are WFO research results, not guarantees of future performance.

## Canonical Task 2 Files

- `quant_project/task2_corrected_runner.py`
- `research_output/TASK2_CORRECTED_RESULTS.json`
- `research_output/TASK2_RETURN_SPACE_CORRELATION.csv`
- `research_output/TASK2_RESEARCH_REPORT.md`

## Task 2 Interpretation

The final research compares nine hypotheses using the same causal execution and walk-forward framework. Full-sample frozen-fit results are retained in the JSON for descriptive context, while the chronological WFO results are the primary validation evidence.

The previous 70% PB07 / 30% BB01 portfolio metrics are historical and should not be cited as the canonical Task 2 result.

## Task 3 — Corrected Multi-Alpha Allocation

Task 3 uses a frozen three-strategy selection from the corrected Task 2 evidence: PB07_TailReversal_10D, PB07_BB03_BB04_Conditional, and BB03_Reversal_10D. BB01, MeanReversion_Composite, and BB04 have negative corrected mean WFO returns and are excluded; BB03_RegimeFiltered is redundant with BB03.

The Task 3 comparison includes the best selected individual, equal-weight, covariance ERC, long-only full-sample maximum-Sharpe descriptive optimization, and the proposed rolling dynamic meta-model. The dynamic model uses a low-capacity trailing mean/volatility score, 504-observation rolling training windows, an internal 80/20 validation split, 63-observation OOS test windows, 0.05% turnover cost, and a 500-repetition permutation allocation null.

Superseded two-strategy portfolio artifacts and old strategy implementation files have been removed from the canonical branch. Do not use historical metrics from prior Task 3 runs.
