# PREPATHON Submission Status

**Date:** September 28, 2026  
**Status:** Task 2 final research artifacts completed. Task 3 remains frozen.

## Task 1

Task 1 remains frozen and unchanged.

## Task 2 — Final

The final Task 2 run uses the synchronized dataset available in the repository:

- 986 signal observations
- 986 price observations
- 986 common dates
- 2018-01-02 to 2021-11-01
- 20 supplied predictive signals
- 9 tested strategy hypotheses
- 7 chronological WFO folds
- 504 training / 63 test observations per fold
- next-open execution
- open-to-open marking
- 0.05% transaction cost per executed side
- training-only parameter fitting

### Final WFO results

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

These are descriptive WFO results. They should not be presented as guarantees of future performance.

### Canonical Task 2 artifacts

- `quant_project/task2_corrected_runner.py`
- `research_output/TASK2_CORRECTED_RESULTS.json`
- `research_output/TASK2_RETURN_SPACE_CORRELATION.csv`
- `research_output/TASK2_RESEARCH_REPORT.md`

The previous 70% PB07 / 30% BB01 portfolio figures are historical and are **not** the canonical Task 2 result.

## Task 3

Task 3 artifacts are frozen and were not modified as part of this Task 2 completion.

## Submission Principle

The submission should report the reproducible research evidence from the final runner and clearly distinguish frozen-sample results from chronological WFO results.
