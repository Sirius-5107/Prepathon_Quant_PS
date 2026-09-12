# Alpha Family Definition — Task 1 Research Conclusions

**Project:** PREPATHON Quant PS — Multi-Alpha Research Lab  
**Status:** Research artifact; no strategy optimization  
**Primary purpose:** Consolidate the signal research completed before candidate-strategy construction.

---

## 1. Research objective

The objective of this phase was to determine which of the 20 supplied signals contain credible, interpretable predictive structure and whether apparent signals represent distinct sources of return information or multiple measurements of the same underlying effect.

The research deliberately does **not** maximize backtest return or optimize trading thresholds. The sequence was:

`20 signals → forward-return screening → statistical validation → temporal stability → shape analysis → conditional alpha analysis → return-space independence → candidate strategy construction`

Only the first seven stages are summarized here. Candidate strategies, robustness testing, walk-forward selection, and portfolio construction remain subsequent work.

---

## 2. Data and return convention

The supplied signal dataset contains 20 signals:

- PB01–PB08
- BB01–BB07
- VB01–VB05

The signal data contains 1,000 rows and spans **2018-01-02 to 2021-11-01**. The price dataset contains 979 rows. After merging the signal and price datasets, **866 common dates** remain.

The research uses the competition-compatible causal convention:

- decision information is taken from the signal state at time `t-1`;
- the corresponding forward-return target begins at the next open;
- predictive returns are defined as:

`forward_return_h(t) = close[t+h] / open[t+1] - 1`

Horizons studied: **1d, 3d, 5d, 10d, 20d**.

Usable observations were 865, 863, 861, 856, and 846 respectively.

Raw price/volume were not used as predictive features; they were used only to construct forward-return targets and for later execution/accounting work.

---

## 3. Initial signal screening

The first screen used Spearman information coefficients and binary/event spreads across the five forward horizons.

Several signals showed economically interesting but generally modest unconditional relationships.

### Strongest Spearman IC patterns

- **BB03:** consistently negative, strongest at 10d (`IC ≈ -0.089`)
- **PB07:** consistently negative, strongest at 10d (`IC ≈ -0.076`)
- **PB01:** negative across all horizons
- **VB03:** positive at short/intermediate horizons, strongest at 5d (`IC ≈ +0.076`)
- **VB04:** positive, strongest at 3d (`IC ≈ +0.069`)
- **BB04:** positive, strongest at 5d (`IC ≈ +0.071`)
- **BB01:** positive IC at longer horizons, including `IC ≈ +0.050` at 20d

The strongest binary spreads included VB03, BB01, BB04, BB03, and BB02, but several of these were based on relatively rare event states.

These screens were treated as **candidate-generation evidence**, not as proof of alpha.

---

## 4. Statistical validation

For the 100 signal × horizon combinations, HAC/Newey-West inference was used with a lag structure appropriate to the forward-return horizon. Multiple testing was controlled using Benjamini-Hochberg false-discovery-rate adjustment.

The strongest individual results included:

| Signal | Horizon | Spread / coefficient | HAC t | p-value | Spearman IC |
|---|---:|---:|---:|---:|---:|
| VB03 | 5d | +2.635% | 2.58 | 0.0099 | +0.0763 |
| BB03 | 10d | -1.534% | -2.26 | 0.0237 | -0.0894 |
| BB04 | 5d | +1.705% | 1.91 | 0.0567 | +0.0705 |
| BB03 | 1d | -0.189% | -1.81 | 0.0697 | -0.0581 |
| VB04 | 3d | +0.530% | 1.80 | 0.0723 | +0.0687 |

However:

- **0/100 tests survived BH-FDR at q < 5%**
- **0/100 tests survived BH-FDR at q < 10%**

Therefore, no individual signal × horizon should be described as statistically validated after multiple-testing correction.

This is not evidence that no alpha exists. It means the research must rely on economically coherent structure, temporal stability, cross-signal conditioning, and later out-of-sample validation rather than p-value shopping.

---

## 5. Temporal stability

The most important stability observations were:

### BB03 — 10d mean reversion

BB03's effect was negative in every calendar year:

| Year | Coefficient | t | p | IC |
|---|---:|---:|---:|---:|
| 2018 | -1.23% | -0.79 | 0.432 | -0.080 |
| 2019 | -1.17% | -1.05 | 0.293 | -0.071 |
| 2020 | -2.24% | -1.69 | 0.091 | -0.106 |
| 2021 | -1.69% | -2.80 | 0.005 | -0.115 |

The direction is stable even though statistical strength is uneven.

### PB07 — 10d mean reversion

PB07 was directionally negative in every year. Its yearly coefficients were approximately -19%, -20%, -30%, and -20% in the raw continuous-score regression used in the temporal analysis. The effect is directionally stable but statistically weak and should not be interpreted as a standalone validated alpha.

### BB04 — 5d

BB04 was positive in 2018, 2019, and 2021, but slightly negative in 2020. It is therefore promising but less temporally clean than BB03.

### VB03 — 5d

VB03 was positive overall but extremely sparse: only **16 positive events** in the pooled sample. The strongest evidence came from 2018, with much weaker evidence afterward and no positive events in the final year. This makes VB03 a weak candidate for a primary robust family despite its attractive pooled statistics.

---

## 6. Signal shape analysis

The shape analysis was used to distinguish monotonic predictive relationships from isolated binary/event effects.

### PB07

At 10d, PB07 showed a clear tail-reversal pattern:

- Q1 mean ≈ +1.35%
- Q2 ≈ +0.16%
- Q3 ≈ +0.56%
- Q4 ≈ +0.59%
- Q5 ≈ -0.35%
- Q5 − Q1 ≈ **-1.70%**

This supports a **mean-reversion / extreme-state** interpretation rather than a simple monotonic trend interpretation.

PB08 displayed a similar shape and is highly correlated with PB07, so it should not automatically be treated as a separate alpha.

BB06 did not exhibit a comparably coherent shape. BB07 showed non-monotonic behavior, including a potentially suspicious Q3 20d result.

---

## 7. Conditional alpha analysis

Conditional tests were performed to determine whether the strongest-looking signals were simply proxies for one another.

### BB03 conditioned on PB07

The BB03 effect largely weakened or disappeared in the highest PB07 quintile, and BB03 itself was very sparse in the lowest PB07 states.

### PB07 conditioned on BB03

For 10d returns:

- BB03 = 0: PB07 Q5−Q1 ≈ **-0.051%**, Spearman ≈ -0.021
- BB03 = 1: PB07 Q5−Q1 ≈ **+0.102%**, Spearman ≈ -0.001

This indicates that the large unconditional PB07 effect is not cleanly independent of the BB03 state.

### Joint BB03 + PB07 regression

`return_10d ~ BB03 + PB07`

- BB03 coefficient ≈ +0.00146, t ≈ 1.24, p ≈ 0.214
- PB07 coefficient ≈ -0.000193, t ≈ -0.54, p ≈ 0.586
- R² ≈ 0.0018

Neither signal retained strong incremental linear explanatory power jointly.

### BB03 × PB07 interaction

The interaction term was not significant:

- interaction coefficient ≈ -0.00062
- t ≈ -0.44
- p ≈ 0.662

There is therefore no evidence that a BB03 × PB07 interaction is itself a distinct alpha mechanism in this sample.

### BB04 conditioned with PB07

BB04 becomes too sparse in high PB07 quintiles for useful conditional inference. In the joint 5d regression with PB07, BB04 lost its raw significance:

- BB04 coefficient ≈ +0.00040, t ≈ 0.30
- PB07 coefficient ≈ -0.00060, t ≈ -1.46
- R² ≈ 0.0043

### BB03 versus BB04

Direct comparisons did not show convincing evidence that the two binary oscillator extremes generate clearly distinct effects:

- BB03 5d spread ≈ -0.094%, p ≈ 0.340
- BB04 5d spread ≈ +0.138%, p ≈ 0.251
- BB03 10d spread ≈ +0.121%, p ≈ 0.289
- BB04 10d spread ≈ +0.118%, p ≈ 0.311

These results support treating BB03, PB07, and BB04 as a **mean-reversion / extreme-state family**, rather than three independent alpha sources.

---

## 8. Breakout forensics — BB01

BB01 was examined separately because its economic meaning is different from the mean-reversion signals.

For 20d returns:

- pooled observations: **N = 846**
- BB01 event observations: **40**
- non-event observations: **806**
- event mean ≈ **+0.33%**
- non-event mean ≈ **+0.01%**
- spread ≈ **+0.32%**
- Welch t ≈ **2.03**
- p ≈ **0.0482**
- Spearman IC ≈ **+0.0503**

The effect was positive in every year:

| Year | Events | Spread | t | p | IC |
|---|---:|---:|---:|---:|---:|
| 2018 | 6 | +0.72% | 1.18 | 0.289 | +0.077 |
| 2019 | 15 | +0.42% | 1.63 | 0.122 | +0.077 |
| 2020 | 16 | +0.14% | 0.60 | 0.553 | +0.021 |
| 2021 | 3 | +0.10% | 0.40 | 0.726 | +0.024 |

The correct interpretation is:

> **BB01 is directionally consistent and economically interesting, but statistically weak and event-sparse.**

It should remain a candidate alpha family, not be called validated alpha.

The 20d horizon is the only breakout result that stood out in the focused forensics. Shorter-horizon BB01 spreads were weak.

---

## 9. Return-space independence — QR / Gram-Schmidt

The key question was whether BB01 contains return-space information outside the combined mean-reversion family `{BB03, PB07, BB04}`.

Pairwise correlation is not enough for this question because three correlated components can collectively explain a vector even when individual pairwise correlations are modest. Therefore, the analysis constructed research return streams and applied QR / Gram-Schmidt projection.

### Construction

Using a common **20d** horizon:

- BB03 was scored in the reversal direction.
- PB07 was converted to a centered percentile score and reversed so extreme high values represent expected reversal.
- BB04 was scored positively as an oversold event.
- BB01 was scored positively as a breakout event.
- Each score was normalized to unit RMS.
- Score × forward return produced a research return vector for each signal.

These are **research vectors only**, not executable P&L streams.

The BB01 return vector was projected onto the full 3-dimensional span of BB03, PB07, and BB04.

### Result

- N = **846**
- mean-reversion return-space rank = **3/3**
- BB01 explained R² = **0.1633**
- BB01 residual norm share = **0.9147**
- `R² + residual_share² = 1.0000`
- maximum absolute `Q' residual` ≈ **2.64 × 10⁻¹⁶**

Pairwise correlations of the BB01 research return vector were:

- BB01 vs BB03: **-0.166**
- BB01 vs PB07: **-0.400**
- BB01 vs BB04: **-0.103**

### Interpretation

Only about **16.3%** of the BB01 research return-vector variation is explained by the full mean-reversion return space. The remaining **91.47% residual norm share** is geometrically orthogonal to that space.

This is useful evidence that BB01 is not simply another representation of the mean-reversion family.

However, it is critical not to overstate this result:

- 91.47% is **not** “91.47% independent alpha”.
- It is **not** a statistical significance measure.
- It is **not** proof of causality.
- It is a geometric statement about the constructed research return vectors.

The result supports keeping BB01 as a **distinct candidate alpha family** for subsequent out-of-sample testing.

A 10d sensitivity run was also implemented in the same research script; the 20d horizon is the primary result because BB01's strongest candidate behavior is at 20d.

---

## 10. Current alpha-family conclusion

### Family 1 — Mean-Reversion / Extreme-State

**Signals:** BB03, PB07, BB04  
**Core hypothesis:** extreme oscillator / trend-distance states tend to be followed by partial reversal over an intermediate horizon.  
**Evidence:** BB03 has the cleanest temporal stability; PB07 shows a strong tail-reversal shape; BB04 provides a related oversold-state signal but is less stable.  
**Independence conclusion:** these signals should not be treated as three separate alpha sources without further evidence.

### Family 2 — Breakout

**Primary signal:** BB01  
**Core hypothesis:** a local upper-band breakout identifies a state with positive subsequent medium-term return.  
**Evidence:** +0.32% pooled 20d event spread, Welch t ≈ 2.03, p ≈ 0.048, positive direction in all four years, and substantial return-space residual outside the mean-reversion family.  
**Caveat:** only 40 events; later years contain only 16 and 3 events respectively, so statistical power is limited.

### Signals not promoted to primary families yet

VB03, VB04, PB01, PB04, BB02, BB07, PB08, and other weaker signals remain useful as research controls or potential conditional/context variables, but current evidence is insufficient to promote them to separate primary alpha families.

In particular, rare-event effects should not be promoted merely because their pooled t-statistics look attractive.

---

## 11. What this means for the next phase

The research should now move from **signal discovery** to **simple candidate strategy construction**, without turning the research into an optimization exercise.

The next candidate concepts should be hypothesis-driven and deliberately simple:

1. **BB03 reversal** — binary extreme-state reversal.
2. **PB07 continuous reversal** — trade the continuous trend-distance extreme.
3. **Combined mean-reversion** — combine the family while avoiding redundant double-counting.
4. **BB01 breakout** — isolated breakout hypothesis.
5. Potentially one or two genuinely distinct combinations only if their economic hypothesis is different; parameter variations do not count as distinct strategies.

Thresholds, weights, and any signal combinations should be estimated only inside training / walk-forward windows. The full sample must not be used to select the final strategy and then reported as out-of-sample evidence.

For eventual strategy evaluation, use the competition execution convention and include **0.05% transaction cost per side**. Strategy evaluation must include return, drawdown, turnover/trade count, hit rate, profit factor where appropriate, and failure analysis—not just CAGR or terminal P&L.

The next major research gate is therefore:

`alpha families → simple candidate strategies → cost-aware backtests → robustness / walk-forward → Task 2 candidate selection → Task 3 portfolio construction`

---

## 12. Research integrity statement

The conclusions in this document are intentionally conservative.

The strongest claims currently supported are:

1. **There is a coherent mean-reversion / extreme-state family involving BB03, PB07, and BB04, but the signals show substantial overlap and no individual signal survives FDR correction.**
2. **BB03 has the cleanest temporal directional stability within that family.**
3. **BB01 is a plausible, directionally stable breakout candidate with modest pooled statistical evidence and return-space information outside the mean-reversion family.**
4. **The QR result establishes geometric distinctness of the constructed research return vectors, not statistical independence or guaranteed trading alpha.**
5. **Further claims must be earned through cost-aware, walk-forward, out-of-sample testing.**

This artifact therefore records a research conclusion, not a claim that a profitable trading strategy has already been discovered.
