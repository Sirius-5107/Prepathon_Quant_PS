# Task 3: Multi-Alpha Portfolio Construction

## Scope
Task 3 consumes the corrected Task 2 daily return matrix containing 9 strategy streams and 986 synchronized observations (2018-01-02 to 2021-11-01).

All Task 3 inputs are already-realized Task 2 strategy returns. No Task 3 step reconstructs a signal from price or volume.

## Static baselines
Equal-weight and covariance ERC are reported as full-sample descriptive baselines. They are not OOS forecasts and are not used to select the dynamic model.

## Learned component and capacity
The AlphaMetaModel uses one statistic per strategy: trailing mean divided by trailing volatility. There are no cross-strategy fitted coefficients, hidden layers, or high-dimensional features. This is deliberately low capacity relative to the 504-observation training window.

## Validation and OOS protocol
There are 8 rolling folds. Each fold uses 504 prior observations for training and 63 subsequent observations for testing. Inside each 504-observation training window, the first 80% is used to assess an internal validation block; the final OOS test block is reached only after refitting on the full 504-observation training window.

Transaction cost is 0.05% per unit portfolio turnover at each rebalance. Strategy-level Task 2 costs are already embedded in the supplied return streams.

## Model discipline results
Mean fold train return: 15.70%; validation return: 4.39%; OOS test return: 2.56%.
Mean fold train Sharpe: 1.600; validation Sharpe: 1.469; OOS test Sharpe: 1.835.

These gaps are reported for overfitting assessment; no full-sample performance is substituted for OOS evidence.

## Null baseline
A 500-repetition permutation null randomly reassigns the learned weight magnitudes to strategy labels within each OOS fold. The observed OOS cumulative return is 21.45%; the permutation-null mean is 11.36%, with standard deviation 5.30%. 20 of 500 null runs reached or exceeded the observed OOS cumulative return.

The null is a diagnostic, not a significance claim.

## OOS portfolio result
Dynamic meta-model OOS cumulative return: 21.45%
CAGR: 10.70%
Annual volatility: 4.88%
Sharpe: 2.105
Maximum drawdown: -2.71%

## Factor separation
A simple OLS factor model is fit fold-by-fold using the equal-weight strategy basket as an explicitly endogenous diagnostic factor. Residual RMS is recorded in task3_factor_model.csv. This is not presented as an external market-factor attribution.

## Files
- task3_allocator_comparison.csv
- task3_dynamic_folds.csv
- task3_dynamic_weights.csv
- task3_dynamic_oos_equity.csv
- task3_null_baseline.json
- task3_model_discipline.json
- task3_factor_model.csv
- TASK3_PORTFOLIO_REPORT.md
