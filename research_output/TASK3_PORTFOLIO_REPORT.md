# Task 3: Multi-Alpha Portfolio Construction

## Selected strategy set
Task 3 uses three streams selected before portfolio construction:
- PB07 Tail Reversal: 5.26% mean WFO return, 3/7 positive folds.
- PB07/BB03/BB04 Conditional: 3.11% mean WFO return, 6/7 positive folds.
- BB03 Reversal: 2.37% mean WFO return, 6/7 positive folds.

BB01, Mean-Reversion Composite, and BB04 are excluded because their corrected mean WFO returns are negative. BB03_RegimeFiltered is excluded as redundant with BB03. Other lower-return candidates are not carried into Task 3.

Return-space residual diagnostics are written to task3_strategy_selection.csv. They are diversification diagnostics, not proof of independent alpha. PB07's 3/7 positive-fold result is retained explicitly rather than hidden by portfolio aggregation.

## Required baselines
The comparison table contains best individual, equal-weight, risk-based ERC, long-only maximum-Sharpe optimization, and proposed dynamic allocation. The first four are full-sample descriptive baselines. The proposed dynamic result is stitched OOS only. The maximum-Sharpe baseline is explicitly not treated as OOS evidence.

## ERC
ERC minimizes dispersion in log component risk contributions w_i*(Sigma w)_i under long-only weights summing to one. This replaces the prior implementation that collapsed to equal weights.

## Model discipline
The meta-model uses one trailing mean/volatility score per selected strategy. Task 3 produces 8 rolling OOS blocks from the 504/63 schedule; this is a separate portfolio-construction schedule from the 7-fold Task 2 WFO evidence used for alpha selection. Each block uses 504 training observations, an 80/20 internal train/validation split, refits on all 504 observations, and freezes weights for the following 63-observation OOS block. Transaction cost is 0.05% per unit turnover and is charged on the first day of each OOS rebalance block.

The first OOS block starts from equal weights, so moving from 1/3-1/3-1/3 to the learned first target produces the reported 1.3333 turnover. This is an explicit initialization cost, not a hidden omission.

Mean train return: 20.54%
Mean validation return: 7.12%
Mean OOS test return: 4.09%

Mean train Sharpe: 1.592
Mean validation Sharpe: 1.843
Mean OOS test Sharpe: 1.758

These gaps are the primary overfitting diagnostic; the stitched OOS Sharpe is not presented in isolation.

## Permutation null
Observed stitched OOS return: 35.26%
Null mean: 24.86%
Null standard deviation: 7.47%
Null 95th percentile: 37.70%
Null runs reaching observed: 56/500 (11.2%)

The null is diagnostic, not a significance claim; the exceedance rate is not presented as a formal p-value or proof of statistical significance.

## Dynamic OOS result
Cumulative return: 35.26%
CAGR: 17.10%
Annual volatility: 6.70%
Sharpe: 2.390
Maximum drawdown: -2.17%

These values are regenerated from the three-strategy selection and supersede prior nine-strategy Task 3 numbers.

## Factor diagnostic
The factor model uses the equal-weight basket of the selected strategies as an explicitly endogenous diagnostic factor. It is not external market-factor attribution.

## Outputs
- task3_strategy_selection.csv
- task3_allocator_comparison.csv
- task3_dynamic_folds.csv
- task3_dynamic_weights.csv
- task3_dynamic_oos_equity.csv
- task3_null_baseline.json
- task3_model_discipline.json
- task3_factor_model.csv
- TASK3_PORTFOLIO_REPORT.md
