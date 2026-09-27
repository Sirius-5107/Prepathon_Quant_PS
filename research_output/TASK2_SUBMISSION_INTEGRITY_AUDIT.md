# Task 2 Submission Integrity Audit — Superseded

**Date:** September 27, 2026  
**Status:** SUPERSEDED

This document audited an earlier PB07/BB01 portfolio implementation and reported approximately 23.6351% cumulative return and 0.6684 Sharpe.

Those figures are **not valid canonical Task 2 evidence** because the earlier implementation reconstructed indicators / economic variables rather than restricting predictive inputs to the supplied anonymized signal library.

The audit's historical PASS conclusions therefore do not apply to the corrected implementation.

## Corrected canonical evidence

See:

- `research_output/TASK2_RESEARCH_REPORT.md`
- `quant_project/task2_corrected_runner.py`
- `research_output/TASK2_CORRECTED_RESULTS.json`

The corrected implementation uses:

- supplied signals only as predictive inputs;
- next-open execution;
- open-to-open marking;
- 0.05% transaction cost per side;
- training-only parameter estimation;
- 5 chronological WFO folds.

The corrected WFO results do **not** support any of the five tested candidates as a robust profitable OOS strategy.

**Do not use the legacy 23.6351% return / 0.6684 Sharpe figures in the final submission.**
