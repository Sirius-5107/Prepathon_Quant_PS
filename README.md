# Inter-IIT Quantitative Finance Prepathon

**Canonical checkpoint documentation:** [CHECKPOINT_DOCUMENTATION.md](CHECKPOINT_DOCUMENTATION.md)

## Current status

- **Task 1:** Initial modular research/backtesting framework submitted and frozen. Its original metrics are historical, not the corrected Task 2 results.
- **Task 2:** Corrected supplied-signal research completed on 986 synchronized observations, dated 2018-01-02 to 2021-11-01. Nine hypotheses were evaluated using 7 chronological WFO folds (504 train / 63 test) and 0.05% cost per executed side.
- **Task 3:** Rebuilt using a frozen three-strategy selection from corrected Task 2 evidence. The required factor model, portfolio optimizer, meta-model, dynamic allocator, and final evaluator are implemented, with rolling OOS and permutation-null diagnostics.

## Canonical results

- Task 1: `TASK1_SUMMARY.md` (historical initial checkpoint).
- Task 2: `research_output/TASK2_RESEARCH_REPORT.md`, `research_output/TASK2_CORRECTED_RESULTS.json`, `research_output/TASK2_RETURN_SPACE_CORRELATION.csv`.
- Task 3: `research_output/TASK3_PORTFOLIO_REPORT.md` and the `research_output/task3_*` diagnostics.

Task 2 WFO leaders by mean return:
- PB07_TailReversal_10D: +5.26%, Sharpe 1.769, positive in 3/7 folds.
- PB07_BB03_BB04_Conditional: +3.11%, Sharpe 1.667, positive in 6/7 folds.
- BB03_Reversal_10D: +2.37%, Sharpe 1.012, positive in 6/7 folds.

Task 3 uses those three streams. Its dynamic model reports stitched OOS cumulative return 35.26%, CAGR 17.10%, annual volatility 6.70%, Sharpe 2.390, and maximum drawdown -2.17%. These are stored-run metrics, not guarantees. The 500-run permutation null has a 95th-percentile return of 37.70%; 56/500 null runs meet or exceed the observed return, so the null comparison is diagnostic and does not establish statistical significance. The first four allocation baselines are full-sample descriptive; only the proposed dynamic allocation is stitched OOS.

## Reproduction

Run from the repository root:

```bash
python quant_project/task2_corrected_runner.py
python quant_project/task3_backtest.py
```

Task 3 depends on the corrected Task 2 outputs. See [CHECKPOINT_DOCUMENTATION.md](CHECKPOINT_DOCUMENTATION.md) for dataset conventions, complete WFO table, selection rationale, model-discipline diagnostics, null-baseline interpretation, and output inventory.
