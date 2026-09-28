# Task 3 Portfolio Report

> **Regeneration required.** The historical Task 3 report previously stored at this path described a two-strategy PB07/BB01 allocator and is superseded.

Run:
`python quant_project/task2_corrected_runner.py`
then:
`python quant_project/task3_backtest.py`

The current runner regenerates this report from the corrected nine-strategy Task 2 return matrix and includes:
- 504-observation rolling training windows
- 80/20 internal train-validation split
- 63-observation OOS test windows
- low-capacity trailing mean/volatility meta-model
- 0.05% portfolio turnover cost
- 500-repetition permutation null
- factor-model residual diagnostics
- train/validation/OOS performance gaps

Do not submit this placeholder until the runner has been executed successfully.