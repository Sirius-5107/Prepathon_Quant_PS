# Task 2 Research Report: Quantitative Strategy Development

**Revision:** September 19, 2026 — causal PB07 audit applied

## Executive Summary

Task 2 was re-audited for look-ahead and reproducibility. The PB07 executable strategy previously used a full-sample Q1 cutoff. That allowed future observations to influence earlier signal classifications.

The executable PB07 strategy is now causal: at each signal date, Q1 is the 20th percentile of observations strictly prior to that date, with a fixed 60-observation minimum history. Signals are formed at t-1 close, entered at t open, and exited at t+20 close. Transaction cost remains 0.05% per side.

## Corrected Results

| Item | Corrected result |
|---|---:|
| PB07 Q1 signal events | 140 |
| PB07 non-overlapping trades | 15 |
| PB07 compounded net return | 29.02% |
| BB01 trades | 17 |
| Final allocation | 70% PB07 / 30% BB01 |
| Portfolio cumulative return | **27.67%** |
| Portfolio annualized volatility | 8.11% |
| Portfolio Sharpe, RF=0 | **0.9161** |
| Portfolio max drawdown | -9.85% |
| Portfolio Calmar | 0.7483 |
| Portfolio observations | 866 |

## PB07 Statistical Validation

Using the same executable holding-period convention, causal Q1 observations have a 20-day forward-return spread of approximately **+1.64 percentage points**, with Welch t-statistic **3.21**. The signal-level sample contains 136 causal Q1 observations after the minimum-history rule.

A block bootstrap sensitivity check produced a 95% interval of approximately **[-0.17%, +3.08%]** for the Q1-vs-non-Q1 spread, so the bootstrap result is not treated as definitive evidence.

## Walk-Forward Validation

The PB07 signal is causal throughout the sample. Executable trade results by expanding calendar folds:

- 2018-2019 -> 2020: 2 test trades, +3.68% summed net trade return.
- 2018-2020 -> 2021: 2 test trades, +2.25% summed net trade return.

The small test-trade counts materially limit inference.

## Portfolio Construction

The corrected daily return stream is stored in `research_output/portfolio_daily_returns.csv`. It contains 866 chronological observations, with realized trade returns on exit dates and zero returns otherwise.

The 70/30 PB07/BB01 portfolio compounds these daily realized returns once. The corrected baseline is **27.6741%**, and the Task 3 runner contains an assertion for this exact value.

## Task 3

Task 3 has been regenerated from the corrected return stream. Static allocation metrics are full-sample descriptive comparisons. The dynamic allocator uses a 504-observation rolling training window and 63-observation OOS windows, with six genuine OOS windows beginning 2020-03-18.

Dynamic ERC OOS result: **23.48% cumulative return, 1.545 Sharpe, -1.91% max drawdown**.

## Limitations

1. PB07 performance is sensitive to the historical-quantile specification; the 60-observation warm-up is retained as an estimation-stability rule, not a return-optimized parameter.
2. Test folds contain few executable trades.
3. The research universe is limited to 2018-2021.
4. Multiple testing and model-selection effects remain relevant.
5. Full-sample static optimization is descriptive and not an OOS forecast.

## Reproducibility

Run:

`python quant_project/strategy_mean_reversion.py`

then

`python quant_project/task3_backtest.py`

The latter consumes the canonical corrected `portfolio_daily_returns.csv` and asserts the corrected 70/30 baseline.
