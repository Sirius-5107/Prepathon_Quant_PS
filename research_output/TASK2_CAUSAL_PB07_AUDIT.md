# Task 2 Causal PB07 Audit

The original PB07 executable implementation used a full-sample quintile classification, allowing later observations to influence earlier Q1 classifications. This was look-ahead.

The corrected implementation uses an expanding historical 20th-percentile threshold based only on observations strictly before each signal date, with a fixed 60-observation minimum history. Execution remains: signal at t-1 close, entry at t open, exit at t+20 close, 0.05% cost per side.

Corrected results:
- Q1 signal events: 140
- Non-overlapping trades: 15
- PB07 compounded net return: 29.02%
- 70/30 PB07/BB01 portfolio return: 27.67%

The prior 23.6351% portfolio result is retained only as a legacy/pre-audit reference. The regenerated portfolio_daily_returns.csv is now the downstream canonical return stream.
