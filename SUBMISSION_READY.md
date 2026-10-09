# PREPATHON Submission Status

**Reconciled:** 10 October 2026  
**Status:** Tasks 1–3 checkpoint documentation reconciled against the committed final research artifacts.

## Task 1 — Frozen initial framework

Task 1 remains complete and unchanged. Its original baseline and data-alignment figures are historical checkpoint results; they should not be presented as the corrected Task 2 dataset or performance.

Reference: `TASK1_SUMMARY.md`.

## Task 2 — Corrected final research

- 986 synchronized signal/price observations, 2018-01-02 to 2021-11-01.
- 20 supplied signals; no additional price-derived predictive inputs.
- Signal at t, next-open execution at t+1; open-to-open marking.
- 0.05% cost per executed side.
- 9 strategy hypotheses; 7 WFO folds with 504 training and 63 test observations.

| Strategy | Mean WFO return | Mean WFO Sharpe | Positive folds |
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

Canonical artifacts: `quant_project/task2_corrected_runner.py`, `research_output/TASK2_CORRECTED_RESULTS.json`, `research_output/TASK2_RETURN_SPACE_CORRELATION.csv`, `research_output/TASK2_RESEARCH_REPORT.md`.

The previous 70% PB07 / 30% BB01 figures are historical and are not the canonical Task 2 result.

## Task 3 — Final multi-alpha allocation research

The frozen selection is PB07_TailReversal_10D, PB07_BB03_BB04_Conditional, and BB03_Reversal_10D. The corrected Task 3 build includes:
- `factor_model.py`
- `portfolio_optimizer.py`
- `meta_model.py`
- `dynamic_allocator.py`
- `final_evaluation.py`

The model uses one trailing mean/volatility score per strategy, 504-observation rolling training windows, internal 80/20 train-validation splits, 63-observation OOS blocks, 0.05% turnover cost, and a 500-repetition permutation allocation null. There are 8 Task 3 rolling OOS blocks, distinct from the 7 Task 2 alpha-selection folds.

Stored-run dynamic OOS metrics: cumulative return 35.26%, CAGR 17.10%, annual volatility 6.70%, Sharpe 2.390, maximum drawdown -2.17%. Mean fold returns are 20.54% train, 7.12% validation, and 4.09% OOS test. The permutation null has mean return 24.86%, standard deviation 7.47%, 95th percentile 37.70%, and 56/500 exceedances (11.2%). This is a diagnostic, not a formal p-value or significance claim; the observed return is below the null 95th percentile.

The best-individual, equal-weight, ERC, and maximum-Sharpe rows are full-sample descriptive baselines. Only the proposed dynamic row is stitched OOS. Do not report maximum-Sharpe as OOS evidence.

Canonical report and outputs: `research_output/TASK3_PORTFOLIO_REPORT.md` and `research_output/task3_*`.

## Reproduction

From the repository root:

```bash
python quant_project/task2_corrected_runner.py
python quant_project/task3_backtest.py
```

Regeneration overwrites generated outputs. Compare new files with the committed artifacts before replacing a submission package.

## Single source for cross-task status

See `CHECKPOINT_DOCUMENTATION.md` for the reconciled narrative, complete Task 2 WFO table, Task 3 selection and caveats, output inventory, and documentation maintenance rules.
