# PREPATHON Submission Status

**Date:** September 27, 2026  
**Status:** Corrected Task 2 research complete; legacy Task 2 portfolio claims superseded.

## Task 1

Task 1 remains frozen and unchanged.

## Task 2 — Corrected

Task 2 has been rebuilt around the supplied 20-signal information set.

Primary evidence:
- 866 common observations, 2018-01-02 to 2021-11-01
- supplied signals PB01-PB08, BB01-BB07, VB01-VB05
- signal at t -> next-open execution
- 0.05% transaction cost per side
- 5 rolling WFO folds: 504 train / 63 test
- training-only parameter estimation
- no price/OHLC-derived predictive features

### Corrected WFO result

| Strategy | Mean WFO Return | Mean WFO Sharpe | Positive Folds |
|---|---:|---:|---:|
| BB01_Breakout_20D | -3.29% | -0.56 | 0/5 |
| PB07_TailReversal_10D | -0.60% | -0.26 | 0/5 |
| BB03_Reversal_10D | -5.01% | -0.38 | 1/5 |
| MeanReversion_Composite_10D | -4.73% | -0.33 | 2/5 |
| BB03_RegimeFiltered_10D | -5.46% | -0.82 | 0/5 |

**Conclusion:** No tested candidate is currently supported as a robust profitable OOS strategy.

The previous 70% PB07 / 30% BB01 portfolio metrics are legacy results from an invalid information-set implementation and must not be used as canonical Task 2 evidence.

## Task 3

Any Task 3 result that consumes the superseded PB07/BB01 portfolio must be treated as **stale** until Task 3 is rerun using corrected Task 2 outputs.

## Canonical Documentation

- `research_output/TASK2_RESEARCH_REPORT.md` — corrected research narrative
- `quant_project/task2_corrected_runner.py` — corrected causal WFO runner
- `research_output/TASK2_CORRECTED_RESULTS.json` — corrected WFO output
- `research_output/TASK2_RETURN_SPACE_CORRELATION.csv` — candidate signal-stream correlation

## Submission Principle

The submission should prioritize reproducibility and information-set correctness over presenting an unsupported positive backtest.

**Do not cite the superseded 23.6351% / 0.6684 Sharpe portfolio as a validated Task 2 result.**
