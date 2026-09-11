# Quant Prepathon — Task 2 Research Log

> **Purpose:** This file is the team's research map. Read this before running experiments.
>
> The goal is to prevent us from jumping between signals, strategies and metrics without knowing what question we are answering.

---

## 0. The Research Principle

We are **not trying to find the strategy with the highest backtest return**.

We are trying to establish:

1. Which supplied signals contain predictive information?
2. What *shape* does that information have?
3. Which effects are statistically credible and temporally stable?
4. Which effects represent the same underlying alpha family?
5. Can we turn distinct effects into a small number of simple, robust strategies?
6. Do those strategies remain useful after the mandatory 0.05% per-side cost?
7. Are the resulting strategies genuinely independent in return space?

Only after answering these questions should we optimize a portfolio.

---

# 1. Competition Constraints — Never Forget

- Only the 20 supplied signals are predictive inputs.
- Raw price/volume may be used for forward-return targets and execution/accounting, not as extra predictive features.
- Signal information available through candle `t-1` is used for the decision executed at candle `t` open.
- Transaction cost = **0.05% per side**.
- No lookahead.
- Task 2 needs multiple genuinely distinct candidate strategies, not five variations of the same idea.
- Task 3 must include portfolio allocation, walk-forward validation, and a null baseline for any learned component.

---

# 2. Where We Are Right Now

## Phase A — Infrastructure / Task 1

**Status: COMPLETE**

We have:

- cleaned signal and price data
- timing-aware backtester
- transaction-cost accounting
- baseline strategy
- performance calculations

The baseline is intentionally weak. It is a benchmark, not our alpha thesis.

Relevant files:

- `quant_project/backtester.py`
- `quant_project/execution_engine.py`
- `quant_project/portfolio.py`
- `quant_project/performance.py`
- `baseline_performance.json`

---

# 3. Phase B — Signal Discovery

**Status: IN PROGRESS**

This phase answers:

> "Before constructing a strategy, which individual signals appear to contain predictive information, and what kind?"

We are deliberately **not backtesting strategies yet**.

## B1. Data audit

**DONE**

We established the usable signal/price overlap and checked missingness, duplicates and signal distributions.

Important observation:

- the merged research sample is **866 dates**
- several binary signals are rare, especially VB03
- multiple signals are strongly correlated

Therefore a large raw spread is not automatically evidence of a robust alpha.

---

## B2. Forward-return signal screening

**DONE**

File:

`quant_project/signal_forward_return_matrix.py`

Target convention:

```text
signal at t
     ↓
execution at t+1 open
     ↓
close at t+h
```

For horizon `h`:

`forward_return_h = close[t+h] / open[t+1] - 1`

We inspected horizons:

- 1d
- 3d
- 5d
- 10d
- 20d

This gave us candidate effects but **was only screening**. We do not select a strategy simply because it has a large spread.

Initial candidates:

- BB03 — negative / mean-reversion effect
- PB07 — negative continuous effect
- BB04 — positive / oversold effect
- VB03 — positive rare-event effect
- BB01 — weaker breakout/continuation candidate

---

## B3. Statistical validation

**DONE**

File:

`quant_project/signal_statistical_validation.py`

We added:

- HAC/Newey-West statistics because forward returns overlap
- p-values
- multiple-testing correction using BH/FDR

Important result:

> No individual signal × horizon survived the 5% or 10% FDR threshold across the 100 tested combinations.

This does **not** mean "there is no alpha."

It means:

> We cannot honestly claim a statistically significant discovery after correcting for the size of the search.

Therefore the next evidence must come from economic shape, temporal stability, and independent confirmation — not p-value shopping.

---

## B4. Temporal stability

**DONE**

File:

`quant_project/signal_temporal_stability.py`

We split candidate effects by calendar year.

Key findings:

### BB03 @ 10d

Most convincing current candidate.

- negative every year
- negative yearly IC every year
- pooled effect ≈ -1.53%
- HAC p ≈ 0.024

Interpretation:

> Overbought conditions appear associated with weaker subsequent returns over roughly a 10-day horizon.

This is currently our strongest candidate for a mean-reversion component.

### PB07 @ 5–10d

- negative every year
- effect is directionally stable
- statistical strength is weaker

Interpretation:

> A larger normalized distance from the medium-term trend is associated with weaker future returns.

Need to determine whether this is a genuinely continuous effect or mostly a tail effect.

### BB04 @ 5d

- positive in 3 of 4 years
- 2020 sign flips
- 2021 is particularly strong

Interpretation:

> Potential oversold/mean-reversion effect, but less stable than BB03.

### VB03 @ 5d

- pooled spread ≈ +2.64%
- but only **16 positive observations** in the 866-date sample
- observations are concentrated in earlier years
- no obvious 2021 positive events in the available sample

Interpretation:

> Interesting rare-event signal, but currently too sparse to call robust alpha.

---

# 4. Phase C — Signal Shape Analysis

**STATUS: CURRENT PHASE**

File:

`quant_project/signal_shape_analysis.py`

This phase answers:

> "Is the signal effect actually structured, or are Q1/Q5 / rare binary events creating a misleading average?"

## C1. Continuous signals

Signals:

- PB07
- PB08
- BB06
- BB07
- VB05

We use descriptive full-sample quintiles to inspect:

- Q1 mean return
- Q2 mean return
- Q3 mean return
- Q4 mean return
- Q5 mean return
- median returns
- hit rates
- Q5 − Q1 spread
- monotonicity

**Important:** These full-sample quintiles are for research visualization only. They must not become trading thresholds. Any eventual strategy must estimate thresholds inside the training portion of each walk-forward window.

### What we currently know

PB07 has the strongest continuous shape candidate:

- 5d Q5−Q1 ≈ **−1.02%**
- 10d Q5−Q1 ≈ **−1.70%**
- 20d Q5−Q1 ≈ **−1.32%**

PB08 shows a similar direction, consistent with its strong correlation with PB07.

We therefore suspect a **trend-distance / trend-strength mean-reversion family**, but have not established independence.

---

## C2. Binary conditional distributions

Candidate signals:

- BB03
- BB04
- VB03
- VB04
- VB01
- BB01
- BB02

We inspect:

- sample size
- mean
- median
- standard deviation
- 25th/75th percentiles
- hit rate
- state 1 minus state 0 spread

Why?

Because:

```text
large mean spread + n=16
```

is much less convincing than:

```text
large mean spread + n=100 + similar median + stable years
```

---

# 5. Immediate Next Experiment

Run:

```bash
python quant_project/signal_shape_analysis.py
```

Then inspect:

`research_output/signal_quintile_detail.csv`

The terminal summary is useful, but **the detail file is what tells us the actual Q1→Q5 shape**.

For PB07/PB08 we specifically want to distinguish:

### Case A — genuinely monotonic

```text
Q1  Q2  Q3  Q4  Q5
↑   ↗   →   ↘   ↓
```

This supports using a continuous score.

### Case B — tail-only

```text
Q1  Q2  Q3  Q4  Q5
↑   ↑   →   ↑   ↓↓↓
```

This supports an extreme-state / tail strategy rather than a linear score.

### Case C — noisy

```text
Q1  Q2  Q3  Q4  Q5
↑   ↓   ↑   ↓   ↓
```

This is weak evidence despite a large Q5−Q1 spread.

---

# 6. Phase D — Candidate Alpha Families

**NOT STARTED YET**

After shape analysis, we will group signals by economic behavior.

Current hypotheses only:

## Family 1 — Oscillator Mean Reversion

Candidate:

- BB03
- BB04

Hypothesis:

> Extreme oscillator states predict reversal over short/medium horizons.

Need to establish whether BB03 and BB04 are genuinely complementary or simply opposite states of the same factor.

---

## Family 2 — Trend-Distance Mean Reversion

Candidate:

- PB07
- PB08
- possibly BB06 / VB05

Hypothesis:

> Extreme distance/separation from trend predicts subsequent reversion.

Need to determine:

- continuous vs threshold behavior
- PB07 vs PB08 redundancy
- incremental information after controlling for oscillator signals

---

## Family 3 — Volume-Confirmed Momentum / Event

Candidate:

- VB03
- VB04
- possibly VB01

Hypothesis:

> Unusually strong participation accompanying a move may predict continuation.

Major concern:

- VB03 is extremely sparse.

Need conditional analysis before spending strategy-development time here.

---

## Family 4 — Breakout / Volatility

Candidate:

- BB01
- BB02
- PB06
- BB05
- BB07

Hypothesis:

> Breakouts or volatility-state transitions may predict continuation.

Current evidence is weaker than the mean-reversion family.

---

# 7. Phase E — Return-Space Independence

**NOT STARTED**

Pairwise signal correlation is **not enough**.

We care about whether candidate strategies produce distinct return streams.

Planned analysis:

1. Construct candidate strategy return vectors.
2. Standardize / align them.
3. Apply QR / Gram-Schmidt decomposition.
4. Measure incremental residual return contribution.
5. Compare correlation before and after residualization.

Question:

> Does Strategy B still contain meaningful return information after Strategy A's return component is removed?

If not, they are probably the same alpha family.

---

# 8. Phase F — Strategy Construction

**NOT STARTED**

Only after signal research is complete.

Target: approximately **3–6 genuinely distinct strategies**.

Each strategy needs:

- economic hypothesis
- exact signal rule
- exact timing
- cost-aware backtest
- parameter rationale
- failure analysis
- robustness checks
- train/test or walk-forward evidence
- relation to other candidate strategies

We will prefer **simple rules with evidence** over highly optimized formulas.

---

# 9. Phase G — Robustness

**NOT STARTED**

For each serious candidate:

### Time robustness

- yearly performance
- rolling performance
- train/test or walk-forward

### Parameter robustness

Small parameter changes should not destroy the effect.

### Cost robustness

Test at least:

- 0 bps
- 5 bps per side (competition assumption)
- higher stress costs

### Event robustness

Check whether performance comes from:

- one year
- a few trades
- a few extreme winners
- one particular market regime

### Null comparison

If a component is learned/optimized, compare it against an appropriate null/randomized baseline.

---

# 10. Phase H — Portfolio Construction (Task 3)

**NOT STARTED**

Only after individual strategies are validated.

Compare:

1. best individual strategy
2. equal-weight portfolio
3. risk-based allocation
4. optimized allocation
5. dynamic allocation

For every allocation method, document:

- estimation window
- constraints
- turnover
- transaction costs
- out-of-sample procedure
- null baseline for learned allocation components

---

# 11. Decision Rules — Preventing Research Drift

Before every experiment, write the question in one sentence.

Example:

> "Does PB07 have a monotonic relationship with 10-day forward returns?"

Then run the experiment.

Then record:

```text
Question:
Method:
Result:
Interpretation:
Decision:
Next question:
```

Do **not** change the hypothesis after seeing the result and pretend it was the original hypothesis.

Do **not** choose a signal because it happens to have the best backtest.

Do **not** keep adding filters until performance improves.

Do **not** confuse statistical significance with economic significance.

Do **not** confuse signal correlation with strategy independence.

---

# 12. Current Evidence Board

| Candidate | Evidence | Main Concern | Current Status |
|---|---|---|---|
| **BB03 @ 10d** | Negative every year; pooled HAC p≈0.024 | Multiple-testing correction; needs shape/distribution check | **Highest priority** |
| **PB07 @ 5–10d** | Strong continuous Q5−Q1; negative every year | Need actual Q1–Q5 shape; redundancy with PB08 | **Highest priority** |
| **BB04 @ 5d** | +1.70% spread; Welch p≈0.013 | 2020 sign flip; possibly same oscillator family as BB03 | **Promising** |
| **VB03 @ 5d** | +2.64% spread | Only 16 positive events | **Forensic investigation only** |
| **BB01 @ 5–10d** | Positive direction | Weak statistical evidence | **Secondary** |
| **PB08** | Similar to PB07 | Highly correlated with PB07 | **Redundancy check** |
| **BB06/BB07/VB05** | Some continuous shape | Less convincing | **Monitor** |

---

# 13. What We Are NOT Doing Yet

Until Phase C is complete, we are **not**:

- optimizing weights
- building a complex ML model
- combining all 20 signals
- tuning dozens of thresholds
- maximizing Sharpe
- selecting strategies by in-sample PnL
- doing portfolio optimization

That would be premature.

---

# 14. Mental Model

Think of the project as a funnel:

```text
20 supplied signals
        ↓
forward-return screening
        ↓
statistical validation
        ↓
temporal stability
        ↓
shape analysis          ← WE ARE HERE
        ↓
economic alpha families
        ↓
return-space independence
        ↓
3–6 simple candidate strategies
        ↓
robustness / WFO
        ↓
Task 2 selection
        ↓
Task 3 portfolio construction
```

**If an experiment does not move us down this funnel, we probably should not be doing it.**

---

# 15. Research Status

Last updated: **10 September 2026**

Current phase: **C — Signal Shape Analysis**

Immediate next step:

> Inspect the full Q1→Q5 shapes and conditional distributions from `signal_shape_analysis.py`.

After that:

> Investigate whether BB03, BB04 and PB07 represent distinct alpha mechanisms, then test return-space independence before constructing strategies.
