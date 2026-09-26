# Task 2 — Corrected Alpha Discovery & Research

## Status

Implementation rebuilt around the supplied signal library.

This version replaces the previous Task 2 strategy layer, which incorrectly reconstructed indicators/fundamentals from raw price data.

## 1. Information set

Predictive inputs are restricted to PB01–PB08, BB01–BB07, and VB01–VB05.

Price/OHLC is used only for forward-return targets and execution/accounting. Strategy feature and signal generation does not reconstruct Bollinger Bands, moving averages, oscillators, Price/Book ratios, volatility measures, or other price-derived predictors.

## 2. Strategy interface

All candidates implement the repository BaseStrategy interface:

- generate_features(data)
- generate_signal(data)
- fit(data, targets)
- predict(data), inherited from BaseStrategy
- get_metadata()

Modules:

- quant_project/strategies/alpha_01.py
- quant_project/strategies/alpha_02.py
- quant_project/strategies/alpha_03.py
- quant_project/strategies/alpha_04.py
- quant_project/strategies/alpha_05.py

## 3. Candidate hypotheses

| Strategy | Supplied inputs | Horizon | Construction |
|---|---|---:|---|
| Alpha 01 — BB01 Breakout | BB01 | 20d | Binary breakout event |
| Alpha 02 — PB07 Tail Reversal | PB07 | 10d | Training-window lower-tail threshold |
| Alpha 03 — BB03 Reversal | BB03 | 10d | Binary reversal event / short |
| Alpha 04 — Mean-Reversion Composite | BB03, PB07, BB04 | 10d | Training-only OLS weights |
| Alpha 05 — BB03 Regime Filter | BB03, VB02 | 10d | BB03 event conditioned on supplied VB02 state |

Alpha 02 does not interpret PB07 as Price/Book. PB07 is treated only as an anonymized supplied signal.

## 4. Causality

WFO uses 504 observations for training and 63 for testing, producing 5 complete folds and 315 OOS observations, with 47 observations outside the complete-fold schedule.

Learned parameters are fitted using training data only.

For Alpha 04, the training target is the 10-observation forward return: close[t+10] / open[t+1] - 1. No OOS target is used in parameter fitting.

## 5. Execution convention

Candidate strategies emit explicit entry and exit events.

- Signal information is available through the previous observation.
- Entry uses the next candle open under the Task 1 execution convention.
- Fixed-horizon exits are explicit.
- Transaction cost is 0.05% per side.
- Overlapping positions are prevented.

## 6. Research carried forward

The existing signal research remains relevant:

- BB03 showed the cleanest temporal stability within the mean-reversion family.
- PB07 showed an extreme-state/tail-reversal shape.
- BB04 was related but less temporally stable.
- BB01 behaved as a structurally distinct breakout candidate.
- Earlier QR analysis supports treating BB01 as geometrically distinct from the mean-reversion research family.
- No individual signal × horizon survived BH-FDR correction.

These findings are candidate-generation evidence, not proof of alpha.

## 7. Reproducible validation

Run from the repository root:

    python quant_project/task2_corrected_runner.py

The runner writes:

- research_output/TASK2_CORRECTED_RESULTS.json
- research_output/TASK2_RETURN_SPACE_CORRELATION.csv

The JSON contains full-sample and five-fold WFO results for every candidate.

## 8. Selection rule

Candidates should be retained only when evidence supports correct signal-library information flow, causal implementation, sufficient executable observations, survival after the 0.05% per-side cost, temporal/WFO stability, and distinct return-space contribution where applicable.

The number of final strategies is an empirical result, not a forced number.

## 9. Important limitation

The corrected implementation deliberately does not preserve the performance of the previous Task 2 implementation. The previous implementation used reconstructed price/fundamental information that was inconsistent with the supplied information set.

Reproducibility and information-set correctness take precedence over preserving earlier backtest performance.

## 10. Task 3

Task 3 has not been modified by this rebuild.

After Task 2 results are generated and the final candidate set is selected, Task 3 should be rerun using the corrected strategy return streams.
