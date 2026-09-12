# Task 2 Research Kit: Strategy Validation & Selection

**Status:** Ready to execute  
**Date:** September 2026  
**Purpose:** Guide for implementing, validating, and selecting 3-6 candidate strategies

---

## Overview

You now have a complete research toolkit for Task 2:

1. **TASK2_STRATEGY_RESEARCH_PLAN.md** — Detailed specifications for 5 candidate strategies
2. **bb03_alpha_validator.py** — Rigorous validation framework for mean-reversion alpha
3. **bb01_temporal_stability.py** — Temporal stability analysis for breakout candidates
4. **conditional_alpha_analysis.py** — Independence analysis (BB03, PB07, BB04 relationships)

This kit avoids redundant discovery and focuses on **rigorous validation** of prior signal research.

---

## Quick Start: Three-Step Execution Plan

### Step 1: Understand the Strategy Specifications

**Read:** `TASK2_STRATEGY_RESEARCH_PLAN.md`

This document defines 5 candidate strategies:

| Strategy | Signal | Hypothesis | Horizon | Direction | Priority |
|----------|--------|-----------|---------|-----------|----------|
| BB03 Binary Reversal | BB03 | Overbought reverts | 10d | Short | 1st |
| PB07 Percentile | PB07 | Extreme tails revert | 10d | Short/Long | 2nd |
| MR Composite | BB03+PB07+BB04 | Consensus reversal | 10d | Short | 2nd |
| BB01 Breakout | BB01 | Breakout continues | 20d | Long | 3rd |
| Regime-Conditional | BB03+context | Context-filtered reversal | 10d | Short | 3rd |

**Key Points:**
- Each strategy has explicit entry/exit conditions
- Walk-forward methodology specified (2018-2019 vs 2020; 2018-2020 vs 2021)
- Learnable parameters defined precisely
- Rejection criteria explicitly stated

---

### Step 2: Validate the Foundation Strategy (BB03)

**Run:**
```bash
cd Prepathon_Quant_PS
python quant_project/bb03_alpha_validator.py
```

**What this does:**
- **Full sample:** Unconditional analysis (2018-2021)
- **Year-by-year:** Calendar year decomposition
- **Rolling correlation:** Time-series stability via 60-day windows
- **Walk-forward:** Out-of-sample validation (expanding windows)
- **Cost sensitivity:** Net alpha after transaction costs
- **Hypothesis test:** Formal one-tailed test (mean return < 0 when BB03=1)

**Expected output:**
- Console: Detailed statistics and interpretations
- CSV files (research_output/):
  - `bb03_yearly_validation.csv`
  - `bb03_rolling_correlation.csv`

**Interpretation framework:**

Pass/Fail for Foundation Strategy:
- ✅ **PASS** if:
  - All years show negative spread (sign consistency)
  - Pooled HAC p-value < 0.05
  - 95% CI does not cross zero
  - Net return (after 0.10% costs) > 0
  - Walk-forward test shows positive spread in both test periods

- ❌ **FAIL** if:
  - Any year shows positive spread
  - Pooled HAC p-value > 0.10
  - Effect driven by single year only
  - Net return < 0 after costs
  - Walk-forward sign flips

---

### Step 3: Run Comparative Studies

#### Study A: Temporal Stability of BB01 Breakout

**Run:**
```bash
python quant_project/bb01_temporal_stability.py
```

**Output:** `research_output/bb01_temporal_stability.csv`

**What to look for:**
- Is BB01 @ 20d consistently positive across years?
- Does effect magnitude support carrying it as alpha?
- Is rarity (few events) a deal-breaker?

**Decision rule:**
- If positive in 0-1 years: REJECT (unstable)
- If positive in 2-3 years but weak: ACCEPT CONDITIONAL (low priority)
- If positive in all years and strong: ACCEPT (high priority)

---

#### Study B: Independence of Mean-Reversion Family

**Run:**
```bash
python quant_project/conditional_alpha_analysis.py
```

**Output:** CSVs in `research_output/` showing:
- BB03 conditional on PB07 quintiles
- PB07 conditional on BB03 states
- Multivariate HAC regression (BB03 + PB07)
- Interaction effects

**What to look for:**
- Do BB03 and PB07 predict independently, or is one redundant?
- Is BB04 distinct or just another manifestation of the same reversal effect?
- Should strategies be:
  - Built separately (distinct alpha sources)?
  - Combined (consensus improves robustness)?
  - Chosen (pick one, drop the others)?

**Decision rule:**
- If R² > 0.6 after projection: Signals are highly correlated; prefer simpler strategy
- If R² < 0.3: Signals capture independent information; test all combinations
- If mid-range (0.3–0.6): Test both individual and composite; pick winner via walk-forward

---

## Strategy Selection Workflow

### Phase 1: Foundation Test (BB03)

**Execute:** `bb03_alpha_validator.py`

**Decision Tree:**

```
Does BB03 pass all validation criteria?
│
├─ YES → Foundation is solid
│         Proceed to Phase 2
│
└─ NO → Foundation is weak
        Re-examine signal library
        Consider alternative base strategy
```

---

### Phase 2: Comparative Tests (BB01, Independence)

**Execute:**
- `bb01_temporal_stability.py`
- `conditional_alpha_analysis.py`

**Decision Tree:**

```
BB01 @ 20d: Stable & positive?
├─ YES → Add to portfolio
├─ NO → Drop BB01 from candidates

Independence: BB03, PB07, BB04 distinct?
├─ YES → Build separate strategies for each
├─ NO → Build composite/voting strategy instead
```

---

### Phase 3: Strategy Implementation

**Based on Phases 1-2, implement 3-5 strategies:**

| Scenario | Recommended Strategy Set | Rationale |
|----------|------------------------|-----------|
| BB03 strong, BB01 weak, signals distinct | BB03, PB07 (percentile), BB01 (low priority) | Diversified mean-reversion + rare-event |
| BB03 strong, BB01 weak, signals correlated | BB03 composite (voting), BB01 low-priority | Consensus robustness, skip redundancy |
| BB03 weak, signals distinct | PB07 percentile, Regime-conditional | Tail-focus + context filtering |
| BB03 weak, signals correlated | Regime-conditional BB03 only | Simplicity; add context to improve signal |

---

## Detailed Execution Guide

### Script: BB03 Alpha Validator

**Command:**
```bash
python quant_project/bb03_alpha_validator.py
```

**Output Structure:**

```
VALIDATION 1: Full Sample (2018-2021)
  - Sample size, event counts
  - Mean returns by state
  - Spread, Welch t-stat, HAC p-value
  - 95% confidence interval
  - Hit rates

VALIDATION 2: Year-by-Year Stability
  - 2018: spread, HAC t-stat, p-value
  - 2019: spread, HAC t-stat, p-value
  - 2020: spread, HAC t-stat, p-value
  - 2021: spread, HAC t-stat, p-value
  - Summary: years with negative spread, consistency

VALIDATION 3: Rolling Correlation
  - 60-day rolling Spearman correlation
  - Yearly stats (mean, std, range)
  - Overall stability assessment

VALIDATION 4: Walk-Forward Validation
  - Fold 1: Train 2018-2019, Test 2020
    - Train spread, test spread
    - Sign consistency? YES/NO
  - Fold 2: Train 2018-2020, Test 2021
    - Train spread, test spread
    - Sign consistency? YES/NO

VALIDATION 5: Cost Sensitivity
  - Gross spread
  - Net spread at 0.05% per side
  - Net spread at 0.10% per side
  - % of alpha eroded by costs

VALIDATION 6: Hypothesis Testing
  - H0: mean return (BB03=1) >= 0
  - H1: mean return (BB03=1) < 0
  - One-tailed t-stat, p-value
  - Cohen's d effect size
  - Interpretation: reject H0?
```

**How to Read Results:**

✅ **STRONG EVIDENCE:**
- Spread negative in all 4 years
- Pooled HAC p-value < 0.05
- Walk-forward sign consistency in both folds
- Net return (after costs) > 0.5% per 10 days

⚠️ **MODERATE EVIDENCE:**
- Spread negative in 3/4 years
- Pooled HAC p-value between 0.05-0.10
- Walk-forward sign consistency in 1/2 folds
- Net return > 0% but < 0.5%

❌ **WEAK EVIDENCE:**
- Spread positive in any year
- Pooled HAC p-value > 0.10
- Walk-forward sign flips (contradiction)
- Net return < 0 after costs

---

### Script: BB01 Temporal Stability

**Command:**
```bash
python quant_project/bb01_temporal_stability.py
```

**Output:**

```
TEMPORAL STABILITY SUMMARY
  Positive years: X
  Negative years: Y
  Mean yearly spread: Z%
  Median yearly spread: W%

YEAR-BY-YEAR BREAKDOWN
  2018: N=X, BB01=1: Y, spread: Z%, t-stat: W, p-value: V
  2019: ...
  2020: ...
  2021: ...

STABILITY CLASSIFICATION
  [STABLE/DIRECTIONALLY CONSISTENT/UNSTABLE/MIXED/REJECT/MARGINAL]
```

**How to Interpret:**

| Classification | Meaning | Action |
|---|---|---|
| STABLE | Positive & sig in all/most years | Implement as primary strategy |
| DIR. CONSISTENT | Positive in majority, weak individually | Implement as secondary (low turnover) |
| UNSTABLE | Effect driven by single year | REJECT |
| MIXED | Inconsistent direction | REJECT |
| REJECT | Consistently opposite to hypothesis | REJECT |
| MARGINAL | Borderline; needs scrutiny | CONDITIONAL (validate further) |

---

### Script: Conditional Alpha Analysis

**Command:**
```bash
python quant_project/conditional_alpha_analysis.py
```

**Output:**

```
research_output/
  ├── bb03_conditional_pb07.csv      (BB03 by PB07 quintile)
  ├── pb07_conditional_bb03.csv      (PB07 by BB03 state)
  ├── multivariate_hac.csv           (BB03 + PB07 regression)
  ├── interaction.csv                (BB03 + PB07 + interaction)
  ├── bb04_vs_pb07.csv               (BB04 conditional on PB07)
  ├── bb03_vs_bb04.csv               (Overbought vs oversold)
  └── breakout_forensics.csv         (BB01 & VB03 analysis)
```

**How to Interpret:**

**BB03 conditional on PB07 quintiles:**
- Does BB03 alpha persist in each PB07 state?
- If yes: BB03 is independent of PB07 trend-distance
- If no: BB03 effect is proxied by PB07; use PB07 only

**Multivariate regression coefficients:**
- If both BB03 & PB07 t-stats > 1.96: Both independently significant
- If one t-stat < 1.5: That signal is redundant in presence of other
- If interaction t-stat significant: Signals interact (use composite strategy)

**Redundancy assessment:**
- R² after BB03: X%
- R² after adding PB07: +Y%
- If Y < 5%: PB07 adds nothing; use BB03 only
- If Y > 15%: PB07 adds material info; test both

---

## File Locations & Workflow

**Inputs:**
```
Prepathon_Quant_PS/
├── signals_cleaned.csv
└── price_cleaned.csv
```

**Scripts:**
```
Prepathon_Quant_PS/quant_project/
├── bb03_alpha_validator.py
├── bb01_temporal_stability.py
└── conditional_alpha_analysis.py
```

**Outputs:**
```
Prepathon_Quant_PS/research_output/
├── bb03_yearly_validation.csv
├── bb03_rolling_correlation.csv
├── bb01_temporal_stability.csv
├── bb03_conditional_pb07.csv
├── pb07_conditional_bb03.csv
├── multivariate_hac.csv
├── interaction.csv
├── bb04_vs_pb07.csv
├── bb03_vs_bb04.csv
└── breakout_forensics.csv
```

---

## Recommended Execution Order

**Day 1 (Baseline Validation):**
```bash
# Establish foundation
python quant_project/bb03_alpha_validator.py
# → Outputs: console + 2 CSVs in research_output/
# → Time: ~30 seconds
```

**Day 1-2 (Comparative Studies):**
```bash
# Test breakout candidate
python quant_project/bb01_temporal_stability.py
# → Outputs: bb01_temporal_stability.csv
# → Time: ~20 seconds

# Test independence of mean-reversion family
python quant_project/conditional_alpha_analysis.py
# → Outputs: 7 CSVs showing BB03/PB07/BB04 relationships
# → Time: ~45 seconds
```

**Day 2-3 (Analysis & Interpretation):**
- Read TASK2_STRATEGY_RESEARCH_PLAN.md (strategy specs)
- Examine CSV outputs (look for patterns, sign consistency)
- Make strategy selection decisions (which to implement, which to reject)
- Document findings & rationale

**Day 3+ (Implementation):**
- Build selected strategies (3-5 final candidates)
- Walk-forward test each strategy (expanding window validation)
- Prepare research report

---

## Checklist: Ready for Task 2?

- [ ] Read TASK2_STRATEGY_RESEARCH_PLAN.md (understand 5 candidate strategies)
- [ ] Run bb03_alpha_validator.py (foundation test)
- [ ] Examine bb03_yearly_validation.csv (year-by-year stability)
- [ ] Run bb01_temporal_stability.py (breakout test)
- [ ] Run conditional_alpha_analysis.py (independence test)
- [ ] Review all CSV outputs in research_output/
- [ ] Map results to strategy selection framework
- [ ] Document strategy selection decisions
- [ ] Proceed to implementation phase

---

## Contact & Support

**If results are ambiguous:**
- Re-read the relevant validation script docstring
- Check CSV outputs for year-by-year patterns
- Refer back to TASK2_STRATEGY_RESEARCH_PLAN.md for decision framework
- When in doubt: prefer robustness (broad, stable effects) over peak performance

**If a script fails:**
- Ensure signals_cleaned.csv and price_cleaned.csv are in repo root
- Check that date columns parse correctly (ISO8601 format)
- Verify data has no NaN rows (data_cleaner should have handled this)

---

## Next Steps After Selection

Once you've selected 3-5 strategies via this validation kit:

1. **Implement each strategy** with walk-forward discipline
2. **QR decomposition** on strategy returns (verify orthogonality)
3. **Portfolio construction** (Task 3): Static allocation + dynamic allocator
4. **Final report:** Document all findings, methodologies, caveats

---

**Ready to run?**

```bash
python quant_project/bb03_alpha_validator.py
```

**Good luck!** 🚀
