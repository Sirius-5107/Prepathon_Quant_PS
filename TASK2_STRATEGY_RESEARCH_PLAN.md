# PREPATHON Task 2 Strategy Research Plan

**Prepared:** September 2026  
**Objective:** Design 3–6 genuinely distinct, statistically defensible candidate strategies  
**Horizon:** Task 2 (research), Task 3 (implementation)

---

## Executive Summary

Based on prior signal research (Task 1), we have identified **two coherent signal families** with distinct economic hypotheses:

**Family A: Mean-Reversion / Extreme-State**
- Primary signals: BB03, PB07, BB04
- Thesis: Extreme oscillator/trend-distance states tend to mean-revert over 5–10d horizons
- Strength: Consistent negative direction across all years
- Key members: BB03 (strongest), PB07 (tail-reversal shape), BB04 (weaker but positive)

**Family B: Breakout Continuation**
- Primary signal: BB01
- Thesis: Upper-band breakout identifies positive medium-term continuation (20d)
- Strength: Positive every calendar year; geometrically distinct from mean-reversion family
- Weakness: Rare events (40 in 846 obs); declining power post-2018

We propose **5 candidate strategies** that:
1. Respect the signal families and prior research
2. Avoid redundant parameter mining
3. Test distinct economic hypotheses
4. Include walk-forward discipline
5. Account for transaction costs

---

## PART A: Proposed Strategy Set

### Strategy 1: BB03 Binary Reversal (Mean-Reversion Primary)

**Hypothesis:**
Overbought oscillator state (BB03=1) predicts mean-reversion; suitable for short positions over 10-day holding horizon.

**Category:** Family A — Mean-Reversion  
**Distinctness:** Base mean-reversion family; simplest formulation

---

### Strategy 2: PB07 Extreme-State Percentile (Mean-Reversion Tail-Focus)

**Hypothesis:**
Extreme values of normalized trend-distance (PB07 in Q5 or Q1) predict stronger tail reversion than moderate values; operates as a continuous, severity-scaled reversal score.

**Category:** Family A — Mean-Reversion  
**Distinctness:** Tail-reversion emphasis; continuous scoring vs. binary; captures non-monotonic shape

---

### Strategy 3: Mean-Reversion Composite (Family A Integration)

**Hypothesis:**
Combining multiple noisy measurements of the same extreme-state family (BB03, PB07, BB04) improves robustness of the reversal signal without simply stacking correlated noise.

**Category:** Family A — Mean-Reversion  
**Distinctness:** Ensemble approach; tests whether consensus strengthens robustness; balanced weighting to avoid correlation inflation

---

### Strategy 4: BB01 Breakout Continuation (Breakout Primary)

**Hypothesis:**
Upper-band breakout (BB01=1) at candle t predicts positive 20-day forward returns; operates as a rare-event long strategy.

**Category:** Family B — Breakout  
**Distinctness:** Opposite direction to mean-reversion family; distinct return-space alignment; continuation vs. reversal

---

### Strategy 5: Regime-Conditional Mean-Reversion (Context-Aware)

**Hypothesis:**
Mean-reversion signal (BB03 or composite) is more effective in low-volatility or high-participation regimes; filtering by context signal reduces false reversals and improves precision.

**Category:** Family A (conditional on context)  
**Distinctness:** Conditional logic; introduces risk-regime awareness; attempts to reduce strategy false-positive rate

---

**Optional Strategy 6: Cross-Family Diversification**

If initial 5 strategies survive robustness tests:

**Hypothesis:**
A portfolio equally weighting mean-reversion and breakout families exhibits different risk/return profile than either family alone; genuinely different economic state.

**Category:** Meta-portfolio  
**Distinctness:** Combines opposite directional bets; different portfolio behavior

---

## PART B: Detailed Strategy Specifications

---

### Strategy 1: BB03 Binary Reversal

#### A. Economic Hypothesis

An overbought oscillator (BB03=1) indicates temporary excessive positive momentum. This state is typically followed by partial mean-reversion. The hypothesis predicts **negative 10-day forward returns conditional on BB03=1**.

#### B. Signals Used

- **BB03** (boolean): Overbought condition from bounded momentum oscillator

#### C. Signal Transformation

None. BB03 is already a boolean state flag.

#### D. Entry Condition

At candle t:
- Observation at t includes signal data through t−1 (closed candle)
- If BB03[t−1] = 1, generate short signal for candle t
- Execute short position at open[t]

#### E. Exit Condition

Hold short position for 10 calendar days.

Exit at open[t+10].

#### F. Holding Horizon

10 days (research basis: BB03 10d spread ≈ -1.53%, t ≈ -2.26)

#### G. Position Direction & Sizing

**Direction:** Short (bet on negative returns)

**Sizing concept:** Unit short (1 standard position per signal occurrence)

**Rationale:** Simple, direct bet on reversal hypothesis without leverage or volatility scaling at this stage.

#### H. Entry/Exit Frequency

Triggered whenever BB03[t−1] = 1.

No overlapping positions (exit-then-re-enter if BB03 re-triggers).

#### I. Expected Failure Mode

1. **Market regime shift:** If trend-following or momentum become dominant, overbought states may continue rather than revert.
2. **Overfitting to historical period:** Mean-reversion works better in range-bound markets (2018–2020); may fail in strong trending (2021).
3. **Event clustering:** If multiple BB03 signals cluster, position sizing may inflate exposure.
4. **Costs and friction:** 0.05% per side × 2 (round trip) = 0.10% total; spread of -1.53% must overcome this.

#### J. Why Distinct

- Base mean-reversion hypothesis (Family A primary)
- Binary, non-continuous signal (vs. PB07 percentile)
- Simplest possible family-member strategy
- Establishes baseline robustness

---

### Strategy 2: PB07 Extreme-State Percentile

#### A. Economic Hypothesis

Normalized trend-distance (PB07) exhibits **non-monotonic relationship** with forward returns. Extreme values (Q1 and Q5) predict stronger reversals than moderate values. Use continuous percentile rank as a **severity-scaled reversal score**.

#### B. Signals Used

- **PB07** (continuous, normalized): Normalized measure of price's distance from medium-term trend reference

#### C. Signal Transformation

```
PB07_percentile = rank(PB07) / N

# Map to reversal score (more extreme = stronger reversal signal)
reversal_score = max(
    (PB07_percentile),           # Q5 extreme
    (1 - PB07_percentile)        # Q1 extreme
)

# Invert for direction (higher score = expect downside)
signal_return_prediction = -reversal_score * C

where C is a learned constant from training window
```

**Transformation rationale:**
- Captures non-monotonic tail effect without assuming linear relationship
- Continuous score (not binary) allows position sizing proportional to confidence
- Symmetric for both directions: extreme positive and negative trend distances

#### D. Entry Condition

At candle t:
- Calculate PB07_percentile[t−1]
- Calculate reversal_score[t−1]
- If reversal_score[t−1] > threshold (to be learned), generate short signal
- If -reversal_score[t−1] > threshold, generate long signal
- Execute at open[t]

#### E. Exit Condition

Hold position for 10 calendar days.

Exit at open[t+10].

#### F. Holding Horizon

10 days (research basis: PB07 Q5−Q1 spread ≈ -1.70%, similar magnitude to BB03)

#### G. Position Direction & Sizing

**Direction:** Conditional on extreme direction
- If PB07 is in Q5 (very high): short
- If PB07 is in Q1 (very low): long

**Sizing concept:** Position size proportional to reversal_score magnitude
- Score near 50th percentile: neutral / small position
- Score near 0th or 100th percentile: full position

#### H. Entry/Exit Frequency

Triggered whenever signal strength exceeds learned threshold.

Positions overlap if new extremes emerge while prior position still held.

#### I. Expected Failure Mode

1. **Non-linear relationship doesn't hold:** If relationship is truly monotonic (not tail-heavy), percentile mapping will underweight moderate states.
2. **Learned threshold optimization:** If threshold mining occurs within training window without proper cross-validation, may overfit.
3. **Percentile instability:** Percentile ranks depend on historical distribution; may shift if regime changes.
4. **Costs exceed reversal:** Spread magnitude similar to BB03; costs again relevant.

#### J. Why Distinct

- Continuous scoring vs. binary (richer information)
- Explicit tail-reversion emphasis (captures PB07's non-monotonic shape)
- Different position sizing (severity-proportional)
- Shares family (A) but distinct mechanism within family

---

### Strategy 3: Mean-Reversion Composite

#### A. Economic Hypothesis

BB03, PB07, and BB04 are different measurements of the same **extreme-state / reversal family**. Combining multiple noisy measurements of the same phenomenon improves signal robustness without introducing new alpha sources. A **voting or consensus mechanism** reduces false positives.

#### B. Signals Used

- **BB03** (boolean): Overbought
- **PB07** (continuous): Extreme trend-distance
- **BB04** (boolean): Oversold

#### C. Signal Transformation

```
# Standardize each signal to 0/1 scale
bb03_score = BB03 * 1.0

pb07_score = (PB07 > percentile(PB07, 75)) | 
             (PB07 < percentile(PB07, 25))  
# Binary: 1 if in tail, 0 otherwise

bb04_score = BB04 * 1.0

# Unweighted consensus (voting)
composite_signal = (bb03_score + pb07_score + bb04_score) / 3

# Entry threshold: require at least 2/3 agreement
entry_trigger = composite_signal >= 2/3
```

**Transformation rationale:**
- Equal weighting avoids parameter optimization (no weights to learn)
- Voting mechanism enforces consensus; reduces single-signal false positives
- Preserves individual signal properties while reducing noise

#### D. Entry Condition

At candle t:
- Calculate composite_signal[t−1]
- If composite_signal[t−1] >= 2/3: generate short signal (2+ of 3 signals in reversion state)
- Execute short at open[t]

#### E. Exit Condition

Hold for 10 calendar days.

Exit at open[t+10].

#### F. Holding Horizon

10 days

#### G. Position Direction & Sizing

**Direction:** Short (all three signals predict reversal in negative direction)

**Sizing concept:** Unit short (2/3 or higher composite)

**Rationale:** Unweighted composite avoids over-learning; full position for any consensus state.

#### H. Entry/Exit Frequency

Triggered when 2+ of 3 signals simultaneously indicate reversal.

Expected to be rarer than any single signal (lower entry frequency).

#### I. Expected Failure Mode

1. **Consensus overkill:** If signals are highly correlated (~0.3–0.4 pairwise), voting may be redundant; does not materially reduce false positives.
2. **Missing independent information:** If BB03, PB07, BB04 do not in fact measure the same phenomenon, forcing consensus may throw away uncorrelated edges.
3. **Sample size:** Lower entry frequency means fewer independent trades; statistical power reduced.
4. **Threshold selection:** 2/3 is intuitive but arbitrary; must verify empirically.

#### J. Why Distinct

- Ensemble/consensus approach (Family A integration)
- Lower entry frequency (different trade timing)
- Tests whether family cohesion improves robustness
- Different from either individual signal

---

### Strategy 4: BB01 Breakout Continuation

#### A. Economic Hypothesis

An upper volatility-band breakout (BB01=1) identifies a state of positive momentum continuation. Breakout trades tend to be long biased and capture continuation over 20-day horizons. This is **opposite** to mean-reversion family and geometrically distinct in return space.

#### B. Signals Used

- **BB01** (boolean): Breakout above upper volatility band

#### C. Signal Transformation

None. BB01 is already a boolean state flag.

#### D. Entry Condition

At candle t:
- If BB01[t−1] = 1: generate long signal
- Execute long position at open[t]

#### E. Exit Condition

Hold long position for 20 calendar days.

Exit at open[t+20].

#### F. Holding Horizon

20 days (research basis: BB01 20d spread ≈ +0.32%, only horizon showing positive effect)

#### G. Position Direction & Sizing

**Direction:** Long (bet on positive continuation)

**Sizing concept:** Unit long per signal occurrence

**Rationale:** Simple, direction-aligned with hypothesis; no sizing variation at this stage.

#### H. Entry/Exit Frequency

Triggered whenever BB01[t−1] = 1.

Expected frequency: Very rare (40 events in 866 obs ≈ 4.6%)

Entry dates: Sparse; independent trades.

#### I. Expected Failure Mode

1. **Event rarity:** Only 40 events pooled; yearly counts declining (6, 15, 16, 3). Statistical uncertainty is high; 2021 had only 3 events.
2. **Mean reversion after breakout:** Breakouts may be followed by short-term continuation but longer-term consolidation/reversal.
3. **Declining signal power:** Effect magnitude declining post-2018 (0.72% → 0.10%). Suggest regime shift or data mining.
4. **Costs erode edge:** +0.32% pooled spread vs. 0.10% round-trip cost leaves thin margin.
5. **Overfitting to rare events:** Small sample sizes invite overfitting when optimizing parameters.

#### J. Why Distinct

- Opposite direction to Family A (long vs. short)
- Different return-space direction (QR residual 91.47% vs. mean-reversion span)
- Continuation vs. reversal hypothesis
- Rare-event strategy (different entry frequency)
- Different failure mode profile

---

### Strategy 5: Regime-Conditional Mean-Reversion

#### A. Economic Hypothesis

Mean-reversion alpha (BB03 or composite) is more effective **conditional on market context**. In low-volatility or high-participation regimes, mean-reversion signals are more reliable (fewer false positives). Adding context filtering **reduces whipsaws** and improves precision without claiming new alpha.

#### B. Signals Used

**Primary (mean-reversion):**
- BB03 (overbought) OR composite (BB03 + PB07 + BB04)

**Context (regime filter):**
- **BB07** (continuous): Recent volatility level (prefer low Vol for reversal)
- **VB01** (boolean): Above-average participation (prefer high Vol for reversion)
- **PB08** (continuous): Trend strength (prefer low strength for reversion)

#### C. Signal Transformation

```
# Use BB03 as primary reversal signal

# Context rule 1: Low volatility regime
low_vol_regime = BB07 < percentile(BB07, 50)

# Context rule 2: High participation
high_participation = VB01 == 1

# Context rule 3: Weak trend
weak_trend = PB08 < percentile(PB08, 50)

# Refined entry condition
refined_entry = BB03==1 AND (low_vol_regime OR high_participation)
```

**Transformation rationale:**
- Context signals come from supplied signal library only (no price derivatives)
- Simple boolean logic (avoid complex ML)
- Filters designed to reduce false-positive reversals

#### D. Entry Condition

At candle t:
- If BB03[t−1] = 1 AND (low_vol_regime[t−1] OR high_participation[t−1]):
  - Generate short signal
  - Execute short at open[t]

#### E. Exit Condition

Hold short for 10 calendar days.

Exit at open[t+10].

#### F. Holding Horizon

10 days

#### G. Position Direction & Sizing

**Direction:** Short (refined mean-reversion)

**Sizing concept:** Unit short (only when context passes)

**Rationale:** Context filtering is a refinement, not a new alpha; position sizing remains simple.

#### H. Entry/Exit Frequency

Lower than BB03 alone (only trades when context aligns).

Expected reduction: ~40–60% of unconditional BB03 entry frequency.

#### I. Expected Failure Mode

1. **Context selection bias:** If context filters are chosen post-hoc based on backtest results, overfitting occurs.
2. **Regime instability:** Context regime itself may not be stable; correlation with reversal may break down.
3. **Fewer trades, higher variance:** Filtering reduces entry frequency; increased sampling variance per trade.
4. **Context redundancy:** If context variables are already correlated with BB03, filtering adds no information.
5. **Lookahead in context:** Must ensure context signals at t−1 do not use data from t or later.

#### J. Why Distinct

- Conditional/meta-strategy approach (Family A with context overlay)
- Addresses practical issue (false positives) rather than new alpha
- Different from both unconditional reversal strategies
- Risk-regime awareness

---

## PART C: Precise Experiment Plan

### Phase 1: Signal Frequency & Descriptive Analysis

**For each strategy**, calculate:

**Entry frequency:**
- Absolute count of signal triggers across full dataset
- Yearly breakdown (2018, 2019, 2020, 2021)
- Percentage of candles triggering entry

**Example (BB03 Binary Reversal):**
```
Total candles: 866
BB03=1 events: X
Frequency: X/866 = Y%

2018: X1, 2019: X2, 2020: X3, 2021: X4
```

**Forward-return distribution (given signal):**
- Mean, median, std, skew, kurtosis
- 5th, 25th, 50th, 75th, 95th percentiles
- Count of positive returns, negative returns, hit rate

**Example:**
```
BB03=1 conditional distribution @ 10d forward return:
- Mean: -0.0153
- Median: -0.0012
- Std: 0.0287
- Hit rate: 43%
- N: X
```

---

### Phase 2: Year-by-Year Stability

**For each strategy**, calculate performance in each calendar year:

```
Year | N_trades | Mean_Return | Std | Hit_Rate | Sign_Consistent | Notes
2018 |    X    |    Y%      | Z%  |   W%    |       +        | strong
2019 |    X    |    Y%      | Z%  |   W%    |       +        | strong
2020 |    X    |    Y%      | Z%  |   W%    |       -        | flip
2021 |    X    |    Y%      | Z%  |   W%    |       +        | weaker
```

**Stability assessment:**
- Count of years with positive mean return
- Consistency of sign across years
- Range of returns (max − min)
- Whether effect is driven by single year

---

### Phase 3: Statistical Validation (HAC Tests)

**For each strategy**, conduct HAC/Newey-West inference:

**Unconditional test:**
```
H0: mean forward return conditional on strategy signal = 0

Test statistic: HAC t-stat with 10-lag window
Critical value: two-tailed 5% (t ≈ 1.96)
Result: t-stat, p-value, 95% CI on mean
```

**Example:**
```
BB03 Reversal @ 10d:
Mean return (BB03=1): -0.0153
HAC std error: 0.0068
HAC t-stat: -2.26
p-value: 0.024
95% CI: [-0.0286, -0.0020]
```

---

### Phase 4: Threshold Learning (Walk-Forward Window)

**For strategies with learned parameters (PB07 percentile, composite, context):**

**Design: Expanding window**

```
Train window 1: 2018-01-01 to 2019-12-31
Test window 1:  2020-01-01 to 2020-12-31

Learn threshold / weights from train window 1 only.
Evaluate on test window 1 with fixed parameters.

Train window 2: 2018-01-01 to 2020-12-31
Test window 2:  2021-01-01 to 2021-11-01

Learn threshold from train window 2 (if necessary).
Evaluate on test window 2 with fixed parameters.
```

**What can be learned from training window:**
- Percentile thresholds (e.g., "Q1 = bottom 25%")
- Consensus voting threshold (e.g., "require 2/3 agreement")
- Context filter selection (e.g., "high participation improves reversal")
- Position sizing constants

**What cannot be learned:**
- Which signals to include (must be pre-specified)
- Direction of effect (must be pre-specified)
- Horizon (must be pre-specified)

---

### Phase 5: Transaction Cost Impact

**For each strategy**, calculate:

```
Gross return = mean forward return conditional on signal
Transaction cost = 0.05% per side × 2 (round trip) = 0.10%

Net return = Gross - Transaction cost

Example:
BB03 Reversal @ 10d:
Gross: -1.53%
Costs: -0.10%
Net:   -1.63%

Cost as % of gross: 6.5%
```

**Turnover:**
```
Number of trades per year (average)
Expected holding period
Expected overlap in positions
```

---

### Phase 6: Sensitivity to Reasonable Parameter Changes

**For each learned parameter**, test small deviations:

```
PB07 Percentile Strategy:
- Percentile threshold for tail: {25%, 50%}
- Position sizing: {equal, proportional}

Composite Strategy:
- Voting threshold: {2/3, 3/4}
- Signal weighting: {equal, cap largest at 50%}

Context Strategy:
- Volatility filter: {50th percentile, 40th percentile}
- Participation filter: {VB01, VB02}
```

**Acceptance criterion:**
- Change in net return <50% when parameters vary by ±10–20%
- Sign remains consistent
- Ranking of strategies unchanged

**Rejection criterion:**
- Performance cliff at specific parameter
- Large sensitivity to tiny changes
- Effect disappears with minor modification

---

## PART D: Learnable Parameters & Methodology

### Parameters by Strategy

#### Strategy 1: BB03 Binary Reversal

**Learnable parameters:** None

**Pre-specified:**
- Entry: BB03[t−1] = 1
- Exit: Hold 10 days
- Direction: Short
- Sizing: Unit

**Rationale:** Binary signal, clear hypothesis; no optimization needed.

---

#### Strategy 2: PB07 Extreme-State Percentile

**Learnable parameters:**
1. **Tail threshold:** What percentile defines "extreme"?
   - Candidate values: {Q1/Q5 (0–25%, 75–100%), Q2/Q4 (25–50%, 50–75%)}
   - Learning method: Calculate mean returns at each percentile threshold within training window; select threshold that maximizes Sharpe on training data (with 10-lag standard error)

2. **Position sizing constant:** Should position size be linear, capped, or adaptive?
   - Candidate values: {linear, capped at 1.0, capped at 0.5}
   - Learning method: Test on training window; choose simplest that doesn't degrade Sharpe

**Pre-specified:**
- Transformation: Percentile-based continuous scoring
- Entry: reversal_score > threshold
- Exit: Hold 10 days
- Direction: Conditional on extreme direction

---

#### Strategy 3: Mean-Reversion Composite

**Learnable parameters:**
1. **Voting threshold:** How many signals must agree?
   - Candidate values: {2/3, 3/4, unanimity}
   - Learning method: Test each on training window; select one that maximizes hit rate AND Sharpe

2. **Signal weighting:** Should all three signals have equal weight?
   - Candidate values: {equal (1/3, 1/3, 1/3), cap largest (0.5, 0.25, 0.25), data-driven max}
   - Learning method: Equal weighting preferred (no optimization); if tested, use only train window

**Pre-specified:**
- Transformation: Boolean voting
- Entry: composite_signal >= threshold
- Exit: Hold 10 days
- Direction: Short

**Constraint:** Equal weighting is default; alternative weightings only tested if research evidence supports it.

---

#### Strategy 4: BB01 Breakout Continuation

**Learnable parameters:** None

**Pre-specified:**
- Entry: BB01[t−1] = 1
- Exit: Hold 20 days
- Direction: Long
- Sizing: Unit

**Rationale:** Binary signal, rare events, declining power; any optimization risks overfitting to 3–16 events per year.

---

#### Strategy 5: Regime-Conditional Mean-Reversion

**Learnable parameters:**
1. **Context filter selection:** Which context signals improve reversal accuracy?
   - Candidate signals: {BB07 (volatility), VB01 (participation), PB08 (trend strength)}
   - Learning method: Test each context filter independently on training window; select those that increase hit rate AND reduce false positives (measured as ratio of profitable to unprofitable trades)

2. **Context thresholds:** What percentile defines "favorable regime"?
   - Candidate values: {50th percentile (median), 40th percentile, 60th percentile}
   - Learning method: Use 50th percentile by default; test others only if primary filter underperforms

**Pre-specified:**
- Base signal: BB03 (or composite if composite strategy survives)
- Entry: base_signal AND context_filter
- Exit: Hold 10 days
- Direction: Short

---

### Walk-Forward Implementation Protocol

**Scenario: Expanding window**

```
Year  | Train Start | Train End | Test Start | Test End | Params Learned From Train | Tested On
------|------------|-----------|-----------|----------|-------------------------|----------
1     | 2018-01-01 | 2019-12-31 | 2020-01-01 | 2020-12-31 | 2018–2019 data | 2020 data
2     | 2018-01-01 | 2020-12-31 | 2021-01-01 | 2021-11-01 | 2018–2020 data | 2021 data
```

**Specific steps:**

1. **Load training data:** 2018-01-01 to 2019-12-31 (first fold)

2. **Calculate signal frequencies & return distributions** in training window

3. **For each learnable parameter:**
   - Calculate metric (Sharpe, hit rate) for each candidate value
   - Select candidate with highest metric on training data
   - Record selected parameter

4. **Lock parameters:** These learned values are now fixed for test window

5. **Load test data:** 2020-01-01 to 2020-12-31

6. **Re-implement strategy** with locked parameters from step 3

7. **Evaluate on test window:**
   - Return distribution
   - Hit rate
   - HAC t-stat
   - Net performance (after costs)

8. **Expand training window to include 2020**

9. **Repeat steps 2–7 for second fold** (train on 2018–2020, test on 2021)

10. **Aggregate:** Report average performance across both test periods

---

## PART E: Strategy Rejection Framework

### Primary Rejection Criteria

**A strategy is REJECTED if ANY of the following hold:**

#### 1. Sign Inconsistency

- Mean return changes direction between train and test windows
- OR mean return positive in fewer than 2/4 years
- OR sign flips more than once across years

**Rationale:** Economic hypothesis is not stable; likely data mining artifact.

#### 2. Statistical Weakness (Even Before Costs)

- HAC t-stat < 1.5 in test window (p > 0.1)
- OR 95% confidence interval crosses zero
- OR hit rate < 45% (less than 50/50 random)

**Rationale:** No clear signal above noise; costs will eliminate edge.

#### 3. Cost Exceeds Edge

- Net return (after 0.10% round-trip cost) < 0.5% annualized
- OR (Net return) / (Annual turnover) < 1% gain-to-cost ratio

**Rationale:** Practical trading is not feasible.

#### 4. Overfitting / Threshold Sensitivity

- Performance drops >30% when parameters vary by ±10–20%
- OR best parameter is isolated peak (adjacent parameters much worse)
- OR parameter selection is based on test-window cherry picking

**Rationale:** Learned parameters are brittle; likely overfit.

#### 5. Event Sparsity (for rare-event strategies)

- Fewer than 5 events per year in test period
- OR confidence interval width > mean return (in absolute value)
- OR prediction driven by 1–2 outlier events

**Rationale:** Statistical noise dominates signal in small samples.

#### 6. Redundancy with Other Selected Strategies

- Return correlation > 0.6 with another selected strategy
- AND QR decomposition shows explained R² > 0.5 of another strategy's span
- AND economic hypothesis is not materially distinct

**Rationale:** Strategy adds correlated, not orthogonal, alpha.

---

### Secondary Rejection Criteria

**A strategy is considered WEAK (not automatically rejected) if:**

- Passes primary criteria but effect magnitude is very small (<0.3% mean return)
- OR temporal consistency is moderate (positive in 3/4 years, weak in 1 year)
- OR requires complex learned parameters
- OR frequency is very low (<1 trade per month average)

**Action:** Weak strategies survive research but are lower priority for implementation; suitable for later phases or combinations.

---

## PART F: Final Implementation Recommendation

### Expected Outcome: 3–5 Strategies Survive

Based on prior research and robustness philosophy, I project:

| Strategy | Likelihood | Reason | Priority |
|----------|-----------|--------|----------|
| BB03 Binary Reversal | High (85%) | Consistent sign, 10d evidence, simple | **IMPLEMENT FIRST** |
| PB07 Extreme Percentile | Medium (60%) | Tail-reversal shape but continuous; parameter learning risk | Implement if robust |
| Mean-Reversion Composite | Medium (55%) | Tests robustness hypothesis; may be redundant or stronger | Implement conditionally |
| BB01 Breakout | Low-Medium (35%) | Rare events (3/year in 2021); declining power; high variance | **Implement if others weak** |
| Regime-Conditional | Low (40%) | Context selection risk; reduces freq further; test sensitive | Implement last if time |

### Implementation Phase Recommendation

**Phase 1 (Priority: IMPLEMENT FIRST)**
1. BB03 Binary Reversal — Foundation of mean-reversion family

**Phase 2 (Priority: IMPLEMENT IF ROBUST)**
2. PB07 Extreme Percentile — Tests continuous hypothesis within family
3. Mean-Reversion Composite — Tests consensus robustness

**Phase 3 (Priority: IMPLEMENT ONLY IF PORTFOLIO NEEDS DIVERSIFICATION)**
4. BB01 Breakout — Orthogonal direction; low frequency trade-off
5. Regime-Conditional — Refinement; high risk of overfitting

### Rationale

1. **Sequential testing:** Build from simplest to complex; fail fast on weak ideas.
2. **Return-space efficiency:** Mean-reversion family (A) captures most prior evidence; breakout family (B) adds distinct direction.
3. **Cost pragmatism:** Rare-event strategies (BB01) barely survive costs; use as portfolio diversifier, not foundation.
4. **Robustness first:** Prefer broad plateaus and stable signs over isolated peaks.

---

## Summary Table: Strategy Specifications

| | BB03 Reversal | PB07 Percentile | MR Composite | BB01 Breakout | Regime Cond. |
|---|---|---|---|---|---|
| **Hypothesis** | Overbought reverts | Extreme tail-reversal | Family consensus | Breakout continues | Mean-rev + context |
| **Signals** | BB03 | PB07 | BB03+PB07+BB04 | BB01 | BB03 + context |
| **Entry** | BB03=1 | PB07 extreme | 2+/3 agree | BB01=1 | BB03=1 + filter |
| **Horizon** | 10d | 10d | 10d | 20d | 10d |
| **Direction** | Short | Short/Long | Short | Long | Short |
| **Frequency** | ~X/yr | ~Y/yr | ~Z/yr | ~W/yr | ~V/yr |
| **Learnable Params** | None | Percentile, sizing | Voting threshold | None | Context filter |
| **Costs Impact** | Moderate | Moderate | Moderate | High | Moderate |
| **Implementation Risk** | Low | Medium | Medium | High | High |

---

## Next Steps

1. **Phase C execution:** Run descriptive analysis for each strategy (frequencies, distributions, year-by-year)
2. **Phase D learning:** Implement walk-forward parameter learning (expanding window 2018–2019 vs 2020; 2018–2020 vs 2021)
3. **Phase E rejection:** Apply rejection framework; eliminate strategies that fail primary criteria
4. **Phase F selection:** Select 3–5 final candidates for Task 3 portfolio construction
5. **Return-space validation:** QR decomposition on final strategy set; verify geometric distinctness

---

**Research Philosophy:**

> Quality > Returns. Distinctness > Count. Robustness > Peak Performance.

We are building a defensible research case for distinct alpha hypotheses, not manufacturing the highest historical P&L. Walk-forward validation, temporal stability, and explicit rejection criteria are non-negotiable.
