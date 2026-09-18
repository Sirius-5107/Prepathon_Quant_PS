# Task 3: Portfolio Construction and Allocation

Task 3 was regenerated after the causal PB07 correction.

Corrected Task 2 baseline: **27.6741% cumulative return**, Sharpe **0.9161**, max drawdown **-9.85%**, based on 866 daily observations.

Static allocators are full-sample descriptive comparisons. The dynamic allocator is the only OOS allocation.

| Allocator | PB07 | BB01 | Return | Sharpe | Max DD |
|---|---:|---:|---:|---:|---:|
| baseline | 0.7000 | 0.3000 | 27.67% | 0.916 | -9.85% |
| equal_weight | 0.5000 | 0.5000 | 25.89% | 0.697 | -12.32% |
| risk_parity | 0.6976 | 0.3024 | 27.66% | 0.914 | -9.86% |
| optimize_sharpe | 0.8587 | 0.1413 | 28.59% | 1.003 | -8.86% |
| dynamic_erc_wfo | 0.5965 | 0.4035 | 23.48% | 1.545 | -1.91% |

Dynamic WFO uses 504 prior observations for training and 63-observation quarterly OOS windows, producing 6 genuine OOS windows from 2020-03-18 through 2021-11-01. No backfill is used.

The Task 3 runner assertion has been updated to the corrected canonical baseline.
