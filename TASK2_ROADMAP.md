# Task 2: Alpha Discovery & Research — Development Roadmap

**Deadline:** 18 September 2026 (Friday) — **9 days remaining**

---

## Quick Start (Next Steps)

### 1. Copy Task 1 Framework
```bash
cd quant_project
python main.py  # Verify it still runs
```

### 2. Create New Strategy Files
Each strategy gets its own file in `strategies/`:
```python
# strategies/alpha_01_mean_reversion.py
from strategy import BaseStrategy
import pandas as pd

class MeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Mean Reversion")
        self.metadata = {
            'hypothesis': 'Overbought/oversold conditions mean-revert',
            'signals_used': ['BB03', 'BB04', 'PB07'],
        }
    
    def generate_signal(self, data):
        # ... your logic here
        pass
```

### 3. Run Each Strategy Through Backtester
```python
from backtester import Backtester
from strategies.alpha_01_mean_reversion import MeanReversionStrategy

strategy = MeanReversionStrategy()
backtester = Backtester()
results = backtester.run(price, signals, strategy)
print(results['performance'])
```

---

## Signal Library: Interpretations & Hypotheses

Use this guide to generate **3–6 genuinely different strategies**:

### Price-Based (PB01–PB08)
| Signal | Type | Broad Meaning | Potential Alpha Hypothesis |
|--------|------|---------------|---------------------------|
| PB01 | Bool | Short-term trend | Trend persistence |
| PB02 | Bool | Longer-term trend | Regime identification |
| PB03 | Bool | Above short MA | Momentum signal |
| PB04 | Bool | Above long MA | Support level |
| PB05 | Bool | Recent momentum sign | Direction confirmation |
| PB06 | Bool | Breakout to local high | Volatility expansion |
| PB07 | Cont | Distance from trend | Mean reversion distance |
| PB08 | Cont | Trend strength | Conviction measure |

### Band-Based (BB01–BB07)
| Signal | Type | Broad Meaning | Potential Alpha Hypothesis |
|--------|------|---------------|---------------------------|
| BB01 | Bool | Above upper band | Breakout/squeeze release |
| BB02 | Bool | Below lower band | Breakout/squeeze release |
| BB03 | Bool | Overbought (momentum) | Mean reversion |
| BB04 | Bool | Oversold (momentum) | Mean reversion |
| BB05 | Bool | Low volatility | Squeeze → expansion setup |
| BB06 | Cont | Position in band | Reversion strength |
| BB07 | Cont | Volatility level | Regime filter |

### Volume-Based (VB01–VB05)
| Signal | Type | Broad Meaning | Potential Alpha Hypothesis |
|--------|------|---------------|---------------------------|
| VB01 | Bool | Above-avg participation | Confirmation of direction |
| VB02 | Bool | Rising volume flow | Accumulation signal |
| VB03 | Bool | Vol-supported move | Direction confirmation |
| VB04 | Bool | Secondary participation | Edge confirmation |
| VB05 | Cont | Unusual participation | Surprise signal |

---

## Strategy Hypotheses to Test

### Strategy 1: Breakout Confirmation (Volatility Expansion)
**Hypothesis:** Breakouts above/below volatility bands confirmed by volume perform well.

**Signals:**
- Entry: BB01 (above upper) OR BB02 (below lower)
- Confirmation: VB03 (volume-supported) OR VB01 (above-avg participation)
- Filter: BB07 > percentile(10) (not in squeeze)

**Rationale:** Volatility expansion + volume = institutional move, not noise

**Code Structure:**
```python
class BreakoutVolumeStrategy(BaseStrategy):
    def generate_signal(self, data):
        latest = data.iloc[-1]
        
        breakout = (latest['BB01'] == 1) or (latest['BB02'] == 1)
        volume_confirm = (latest['VB03'] == 1) or (latest['VB01'] == 1)
        not_squeezed = latest['BB07'] > 0.3  # Rough threshold
        
        if breakout and volume_confirm and not_squeezed:
            return 1  # Long on upbreak, short on downbreak
        return 0
```

---

### Strategy 2: Mean Reversion (Overbought/Oversold)
**Hypothesis:** Overbought/oversold oscillator signals mean-revert within medium term.

**Signals:**
- Entry: BB03 (overbought) OR BB04 (oversold)
- Strength: PB07 (distance from trend) > 1 std
- Filter: BB07 (not in squeeze)

**Rationale:** Extremes tend to snap back; large deviations from trend reverse

**Code Structure:**
```python
class MeanReversionStrategy(BaseStrategy):
    def generate_signal(self, data):
        latest = data.iloc[-1]
        
        overbought = latest['BB03'] == 1
        oversold = latest['BB04'] == 1
        far_from_trend = abs(latest['PB07']) > 0.5
        
        if overbought and far_from_trend:
            return -1  # Short signal
        if oversold and far_from_trend:
            return 1  # Long signal
        return 0
```

---

### Strategy 3: Trend-Volume Momentum
**Hypothesis:** Strong trends with rising volume sustain; weak trends with falling volume reverse.

**Signals:**
- Trend: PB01 AND PB02 (both positive for long bias)
- Strength: PB08 (trend strength) > median
- Volume: VB02 (rising volume flow) confirm

**Rationale:** Volume confirms trend strength; low-volume trends are weak

**Code Structure:**
```python
class TrendVolumeStrategy(BaseStrategy):
    def generate_signal(self, data):
        latest = data.iloc[-1]
        
        bullish_trend = (latest['PB01'] == 1) and (latest['PB02'] == 1)
        strong_trend = latest['PB08'] > 0.0  # Positive trend strength
        rising_volume = latest['VB02'] == 1
        
        if bullish_trend and strong_trend and rising_volume:
            return 1
        return 0
```

---

### Strategy 4: Squeeze Expansion
**Hypothesis:** Low-volatility squeezes precede volatility expansions; riding the expansion beats other regimes.

**Signals:**
- Setup: BB05 == 1 (in squeeze) for recent candles
- Trigger: BB01 or BB02 (breakout from squeeze)
- Confirmation: VB05 (unusual participation spike)

**Rationale:** Squeeze represents accumulated energy; release is directional

**Code Structure:**
```python
class SqueezeExpansionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Squeeze Expansion")
        self.squeeze_lookback = 10
    
    def generate_signal(self, data):
        if len(data) < self.squeeze_lookback:
            return 0
        
        latest = data.iloc[-1]
        recent_squeeze = (data.iloc[-self.squeeze_lookback:]['BB05'] == 1).sum() >= 5
        
        breakout = (latest['BB01'] == 1) or (latest['BB02'] == 1)
        unusual_vol = abs(latest['VB05']) > 0.5
        
        if recent_squeeze and breakout and unusual_vol:
            return 1 if latest['BB01'] == 1 else -1
        return 0
```

---

## Research Questions to Answer (Per Strategy)

For **each strategy**, investigate:

### Hypothesis Validation
- [ ] What market behaviour motivates the strategy?
- [ ] Which signals provide the core information?
- [ ] What time horizon are we testing (1-day, 5-day, 20-day)?

### Empirical Evidence
- [ ] Compute conditional mean return given signal state
- [ ] Unconditional (baseline) mean return
- [ ] Hit rate (% of trades profitable)
- [ ] t-statistic of alpha
- [ ] Bootstrap 95% CI on Sharpe ratio

### Robustness
- [ ] Performance by year (2018, 2019, 2020, 2021)
- [ ] Performance by market regime (trend vs. mean-reversion)
- [ ] Sensitivity to transaction costs (test at 0.05%, 0.10%)
- [ ] Sensitivity to parameter changes (±10% threshold changes)
- [ ] Performance in different volatility regimes

### Failure Analysis
- [ ] Where does the strategy lose money?
- [ ] Are losses systemic (e.g., always in downtrends) or random?
- [ ] Can failures be predicted (e.g., regime-dependent)?
- [ ] Maximum consecutive losing trades?

---

## Signal Diagnostics (Before Strategy Building)

Before building strategies, run **signal-level research**:

```python
from feature_engine import FeatureEngine
import pandas as pd

# For each signal:
for signal in ['PB01', 'BB03', 'VB01']:
    # Conditional returns given signal state
    long_returns = returns[signals[signal] == 1].mean()
    short_returns = returns[signals[signal] == 0].mean()
    
    # Hit rate (% of positive returns)
    hit_rate = (returns[signals[signal] == 1] > 0).mean()
    
    # T-stat
    n = (signals[signal] == 1).sum()
    t_stat = long_returns / (returns[signals[signal] == 1].std() / np.sqrt(n))
    
    print(f"{signal}: long_ret={long_returns:.4f}, hit_rate={hit_rate:.2%}, t={t_stat:.2f}")
```

This tells you which raw signals have predictive power **before** combining them.

---

## Independent Alpha Analysis (QR Decomposition)

Once you have 3–6 strategies selected, test for **true independence**:

```python
import numpy as np
from scipy.linalg import qr

# Build return matrix: T candles × N strategies
R = np.column_stack([strategy1_returns, strategy2_returns, strategy3_returns])

# QR decomposition with pivoting
Q, R_mat, P = qr(R, pivoting=True, mode='reduced')

# Interpretation:
# - rank(R) = number of linearly independent strategies
# - If rank < N, some strategies are redundant
# - Magnitude of R diagonal shows contribution order
# - Residuals after projection show remaining alpha

print(f"Matrix rank: {np.linalg.matrix_rank(R)}")
print(f"Diagonal R values: {np.diag(R_mat)}")
```

This is **critical** for Task 2: shows which strategies add genuinely new information.

---

## Output Structure for Task 2

Create a **research report** with:

1. **Strategy Descriptions** (hypothesis, signals, logic)
2. **Empirical Results** (returns, Sharpe, hit rates by strategy)
3. **Robustness Analysis** (performance across periods, regimes, costs)
4. **Statistical Validation** (t-stats, bootstrap CIs, significance tests)
5. **QR Analysis** (independence of alphas)
6. **Selected Strategy Set** (3–6 strategies justified)

**Example JSON output:**
```json
{
  "strategies": [
    {
      "name": "Breakout Confirmation",
      "hypothesis": "...",
      "signals": ["BB01", "VB03", ...],
      "performance": {
        "total_return": 0.123,
        "annualized_return": 0.045,
        "sharpe": 1.23,
        "max_drawdown": -0.15
      },
      "robustness": {
        "2018_sharpe": 0.95,
        "2019_sharpe": 1.45,
        "with_costs_sharpe": 1.10
      },
      "selected": true,
      "selection_reason": "..."
    }
  ],
  "qr_analysis": {
    "matrix_rank": 3,
    "effective_dimensionality": 3,
    "redundancy": "None; all strategies orthogonal"
  }
}
```

---

## Timeline (9 Days)

- **Days 1–3 (Sept 9–11):** Build 3–4 new strategies
- **Days 4–6 (Sept 12–14):** Signal diagnostics, robustness testing
- **Days 7–8 (Sept 15–17):** QR analysis, selection, reporting
- **Day 9 (Sept 18):** Final review, submission

---

## Tips for Success

1. **Start simple, iterate:** Build one strategy at a time. Test it fully before moving to the next.

2. **Separate concerns:** Different strategies should test different hypotheses (not parameter variations).

3. **Be aggressive about killing bad ideas:** If Sharpe < 0.5 and costs ≥ 5 bps, it's probably noise.

4. **Document assumptions:** Every threshold, lookback period, and choice should be justified.

5. **Use the baseline as anchor:** Your strategies should beat baseline on at least one meaningful metric.

6. **Focus on genuinely different alpha:** The competition rewards distinctness, not just number of strategies.

---

## Next Checkpoint: Task 2 Submission

✅ **By Sept 18, 11:59 PM:**
- [ ] 3–6 strategy implementations
- [ ] Research report (hypotheses, evidence, robustness)
- [ ] Statistical validation (t-stats, bootstrap CIs)
- [ ] QR/orthogonality analysis
- [ ] Selected final strategy set with justification
- [ ] Code reproducible from project structure

Good luck! 🚀
