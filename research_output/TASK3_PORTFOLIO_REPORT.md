# Task 3: Portfolio Construction and Allocation

## Executive Summary

Task 3 compares static allocations of the two strategies selected in Task 2
(PB07 and BB01) and a strictly out-of-sample dynamic allocator.

The canonical Task 2 return stream reproduces the Task 2 baseline exactly:
**70% PB07 + 30% BB01 = 23.64% cumulative return**.

## Return Construction

Task 3 uses research_output/portfolio_daily_returns.csv, the canonical Task 2
daily realized-return stream. The values are already decimal returns and are
compounded once at the portfolio level. The separate daily MTM files are not
used for portfolio construction because those files contain cumulative
from-entry MTM values during holding periods, which must not be compounded as
independent daily returns.

Period: 2018-01-02 to 2021-11-01 (866 observations).

## Static Allocation Study

Static allocations are full-sample descriptive comparisons.

| Allocator | PB07 | BB01 | Total Return | CAGR | Annual Vol | Sharpe | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 70.00% | 30.00% | 23.64% | 6.37% | 9.53% | 0.695 | -8.33% |
| equal_weight | 50.00% | 50.00% | 23.14% | 6.24% | 10.97% | 0.606 | -12.99% |
| risk_parity | 63.58% | 36.42% | 23.56% | 6.35% | 9.80% | 0.676 | -8.68% |
| optimize_sharpe | 74.90% | 25.10% | 23.64% | 6.37% | 9.46% | 0.699 | -8.06% |

The Sharpe optimizer uses the full sample and is therefore explicitly an
in-sample/descriptive sensitivity check, not an OOS forecast. The grid search
uses 10 percentage-point increments; its best Sharpe grid point is 70% PB07 /
30% BB01.

## Dynamic Allocation

The dynamic allocator uses a 504-observation rolling training window and
63-observation quarterly OOS test/rebalance windows.

At each rebalance:
1. only the preceding 504 observations are used;
2. covariance-based ERC weights are estimated from that training sample;
3. those weights are frozen for the next 63 observations;
4. the process repeats through the final observation.

This produces **6 genuine OOS windows**, beginning 2020-03-18 and ending
2021-11-01. No pre-OOS weights are backfilled.

### OOS Context

Over the common OOS period (2020-03-18 to 2021-11-01, 362
observations):
- 70/30 Task 2 baseline cumulative return: 14.72%.
- 50/50 cumulative return: 25.35%.
- Dynamic ERC WFO cumulative return: 26.08%.

These are period-matched descriptive comparisons; the full-sample static
metrics above should not be interpreted as OOS estimates.

## Validation

- Canonical observations: 866.
- Canonical period: 2018-01-02 to 2021-11-01.
- 70/30 baseline reproduction: 23.64%.
- Dynamic weights start only after 504 training observations.
- Every dynamic weight uses observations strictly before its test start.
- No dynamic pre-OOS backfill.
- All weights are non-negative and sum to 1.
- Dynamic performance is evaluated only on genuine OOS observations.

## Files

- task3_static_allocators.csv
- task3_grid_search.csv
- task3_dynamic_weights.csv
- task3_portfolio_comparison.csv
- task3_allocator_comparison.csv
- TASK3_PORTFOLIO_REPORT.md
