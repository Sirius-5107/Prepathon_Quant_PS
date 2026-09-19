# Inter-IIT Quantitative Finance Prepathon — Current Project Status

> **Updated September 19, 2026:** Task 2 has been re-audited for causal PB07 signal construction and Task 3 has been regenerated from the corrected canonical return stream. For current submission results, use `research_output/TASK2_RESEARCH_REPORT.md` and `research_output/TASK3_PORTFOLIO_REPORT.md`. Historical reports marked **superseded** are retained only as research provenance.

**Current canonical Task 2 baseline:** 70% PB07 / 30% BB01; 27.6741% cumulative return; Sharpe 0.9161; max drawdown -9.85%; 32 combined trades.

**Current Task 3 dynamic ERC OOS:** 23.48% cumulative return; Sharpe 1.545; max drawdown -1.91%; six genuine OOS windows.

---

# Inter-IIT Quantitative Finance Prepathon — Task 1 Complete ✅

**Status:** Task 1 (Data & Backtesting Infrastructure) — **COMPLETE** and ready for submission  
**Deadline:** 14 September 2026 (Monday) — Submitted 5 days early  
**Next:** Task 2 due 18 September 2026

---

## 📋 Overview

A **production-grade quantitative research and backtesting framework** for the Inter-IIT Tech Meet 15.0 Quantitative Finance challenge.

### What's Included

✅ **8 Core Modules**
- DataLoader, DataCleaner, FeatureEngine
- BaseStrategy, ExecutionEngine, Portfolio
- PerformanceAnalyzer, Backtester

✅ **Working End-to-End Pipeline**
- Data loading → Cleaning → Backtesting → Analysis
- Run with: `python quant_project/main.py`

✅ **Baseline Strategy**
- Trend-following strategy (PB01 + PB02)
- 1.83% total return, 491 trades
- Properly costed at 0.05% per side

✅ **Comprehensive Documentation**
- Implementation notes (design decisions)
- Task 2 roadmap (strategy ideas)
- Quick start guide
- Submission checklist

---

## 🚀 Quick Start

### 1. Run the Framework
```bash
cd quant_project
python main.py
```

Expected output:
- Data loads: 1000 signals, 1000 price rows
- Cleaning: Removes duplicates from price data, keeps 979 rows
- Backtest: Baseline generates 491 trades
- Results saved to `../` (equity curve, trades, metrics)

### 2. Review Results
```bash
cat baseline_performance.json
# Expected:
# {
#   "total_return_%": 1.83,
#   "annualized_return_%": 0.53,
#   "sharpe_ratio": -0.42,
#   "max_drawdown_%": -2.08
# }
```

### 3. Add a New Strategy
Create `quant_project/strategies/alpha_01_mean_reversion.py`:

```python
from strategy import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Mean Reversion")
        self.metadata = {
            'hypothesis': 'Overbought/oversold conditions mean-revert',
            'signals_used': ['BB03', 'BB04', 'PB07'],
        }
    
    def generate_signal(self, data):
        latest = data.iloc[-1]
        if latest['BB03'] == 1:  # Overbought
            return -1  # Short signal
        return 0
```

Then run backtest:
```python
from backtester import Backtester
from strategies.alpha_01_mean_reversion import MeanReversionStrategy

strategy = MeanReversionStrategy()
backtester = Backtester()
results = backtester.run(price, signals, strategy)
print(results['performance'])
```

---

## 📁 File Structure

```
Prepathon_Quant_PS/
├── README.md                          # This file
├── QUICK_START.txt                    # Quick reference
├── IMPLEMENTATION_NOTE.md             # Design decisions & architecture
├── TASK1_SUMMARY.md                   # Executive overview
├── TASK2_ROADMAP.md                   # Strategy ideas for Task 2
├── SUBMISSION_CHECKLIST.md            # Verification checklist
│
├── quant_project/                     # Main codebase
│   ├── main.py                        # Entry point
│   ├── data_loader.py                 # DataLoader class
│   ├── data_cleaner.py                # DataCleaner class
│   ├── feature_engine.py              # FeatureEngine class
│   ├── strategy.py                    # BaseStrategy interface
│   ├── execution_engine.py            # ExecutionEngine class
│   ├── portfolio.py                   # Portfolio accounting
│   ├── performance.py                 # PerformanceAnalyzer
│   ├── backtester.py                  # Backtester orchestrator
│   └── strategies/
│       └── baseline_strategy.py       # Baseline implementation
│
├── baseline_equity_curve.csv          # Portfolio values
├── baseline_trades.csv                # Trade execution log
├── baseline_performance.json          # Performance metrics
├── data_quality_report.json           # Data validation report
├── signals_cleaned.csv                # Processed signals
└── price_cleaned.csv                  # Processed prices
```

---

## 🎯 Key Features

### Timing Convention (Enforced)
```
At candle t:
  - Use signals available through candle t-1
  - Generate trading decision
  - Execute at candlet's open price
  - Mark-to-market at candlet's close
```

### Transaction Costs (Mandatory)
- 0.05% per side (0.05% entry + 0.05% exit = 0.10% round trip)
- Applied to every executed trade
- Tracked in trade log

### Lookahead Prevention
- Chronological sorting before analysis
- t-1 inputs only → t open execution
- Forward returns never used as signal inputs
- No future data in feature generation

### Research Integrity
✅ Chronological ordering  
✅ Missing value handling  
✅ Duplicate removal  
✅ Signal availability enforcement  
✅ Transaction cost accounting  
✅ Position and P&L tracking  
✅ Prevention of lookahead  

---

## 📊 Data Summary

### Signals Dataset
- **Date Range:** 2018-01-02 to 2021-11-01
- **Rows:** 1000 (1 per trading day)
- **Signals:** 20 anonymised columns
  - PB01-PB08: Price-based (8 signals)
  - BB01-BB07: Band-based (7 signals)
  - VB01-VB05: Volume-based (5 signals)
- **Types:** Mostly boolean (0/1), some continuous (bounded)

### Price Dataset
- **Date Range:** 2018-01-02 to 2021-12-10
- **Rows:** 979 (after deduplication)
- **Columns:** open, high, low, close, volume
- **Quality:** No nonsensical prices, all dates valid

### Alignment
- **Overlapping Candles:** 866 (inner join of 1000-row signals with 979-row price data)
- **Ready for Backtesting:** Yes

---

## 📈 Baseline Strategy Performance

| Metric | Value |
|--------|-------|
| Total Return | 1.83% |
| Annualized Return | 0.53% |
| Volatility | 3.47% |
| Sharpe Ratio | -0.42 |
| Sortino Ratio | -0.58 |
| Max Drawdown | -2.08% |
| Calmar Ratio | 0.25 |
| Total Trades | 491 |

**Interpretation:** Baseline is neutral/slightly profitable but not compelling. Good starting point for Task 2 improvements.

---

## 🔍 Performance Metrics Computed

For each strategy backtest:
- Total return (%)
- Annualized return (%)
- Volatility (%)
- Sharpe ratio (vs 2% risk-free)
- Sortino ratio (downside vol)
- Maximum drawdown (%)
- Drawdown duration (days)
- Calmar ratio (return / max DD)
- Trade statistics

All saved to JSON for downstream analysis.

---

## 📚 Documentation Guide

Read in this order:

1. **QUICK_START.txt** — Quick reference (5 min)
2. **TASK1_SUMMARY.md** — Executive overview (10 min)
3. **IMPLEMENTATION_NOTE.md** — Design & architecture (20 min)
4. **TASK2_ROADMAP.md** — Next steps & strategy ideas (15 min)
5. **SUBMISSION_CHECKLIST.md** — Verification (5 min)

Code is self-documented with docstrings and type hints.

---

## 🛠️ Technical Stack

- **Language:** Python 3.7+
- **Key Libraries:** pandas, numpy, scipy
- **No external dependencies** for core logic
- **Type hints** throughout
- **Docstrings** on all public methods

---

## ✅ What's Ready

### For Task 1 Submission
✅ Complete modular codebase  
✅ Working end-to-end pipeline  
✅ Baseline strategy with results  
✅ Data quality validation  
✅ Comprehensive documentation  
✅ Reproducible outputs  

### For Task 2 Development
✅ Framework accepts new strategies  
✅ Template for adding strategies  
✅ 4 detailed strategy hypotheses  
✅ Signal diagnostic guide  
✅ Robustness testing framework  
✅ QR analysis preparation  

### For Task 3 Extension
✅ Modular design (no rewrites needed)  
✅ Extensible interfaces  
✅ Configuration-driven architecture  

---

## 🚀 Next Steps (Task 2 — 9 Days)

**Week 1 (Sept 9-14):**
1. Build 2-3 new strategies
2. Run signal diagnostics
3. Test robustness (costs, parameters, periods)

**Week 2 (Sept 15-18):**
1. QR decomposition (alpha independence)
2. Statistical validation (t-stats, bootstrap CIs)
3. Final strategy selection (3-6 strategies)
4. Research report

**Due:** 18 September 2026 (Friday)

See `TASK2_ROADMAP.md` for detailed strategy ideas and research questions.

---

## 🎓 Learning Resources

### For Understanding the Framework
- Read `IMPLEMENTATION_NOTE.md` for design decisions
- Review docstrings in each Python file
- Run `main.py` and inspect outputs

### For Building New Strategies
- See `TASK2_ROADMAP.md` for 4 detailed hypotheses
- Read signal library descriptions in technical docs
- Study baseline strategy as template

### For Troubleshooting
- Check `data_quality_report.json` for data issues
- Review `baseline_trades.csv` for execution details
- Verify timing convention in `backtester.py`

---

## 📞 Support

All code is documented with:
- Docstrings explaining purpose and parameters
- Type hints for IDE assistance
- Comments on non-obvious logic
- Error messages for common issues

For questions:
1. Check the documentation files
2. Review the code comments
3. Run `main.py` with test data

---

## 📊 Quality Assurance

### Testing Completed
✅ End-to-end pipeline (data → backtest → results)  
✅ Timing convention (t-1 inputs → t open execution)  
✅ Cost calculation (0.05% per side verified)  
✅ Data alignment (signals and price merged correctly)  
✅ Lookahead prevention (no future data in signals)  
✅ Reproducibility (same inputs → same outputs)  

### Validation Checks
✅ Date range consistency  
✅ No nonsensical prices  
✅ Duplicate removal verified  
✅ Missing value handling  
✅ Portfolio accounting accuracy  

---

## 📝 Assumptions

- Risk-free rate: 2.0% annually
- Trading days per year: 252
- Position size: 1 unit per trade
- Initial capital: 1,000,000
- Execution: At candle open, no partial fills
- Slippage: 0 bps (modeled but disabled)

---

## 🏆 Success Criteria (All Met)

✅ Framework runs end-to-end without errors  
✅ Baseline strategy produces reasonable results  
✅ Data is clean and properly aligned  
✅ Timing convention is enforced  
✅ Costs are properly accounted for  
✅ Code is modular and extensible  
✅ Everything is thoroughly documented  

---

## 📈 Timeline

| Task | Deadline | Status |
|------|----------|--------|
| Task 1 | 14 Sept (Mon) | ✅ COMPLETE (5 days early) |
| Task 2 | 18 Sept (Fri) | 📋 In progress (9 days) |
| Task 3 | 21 Sept (Mon) | 📋 Next (3 days) |

---

## 🎯 Vision

This framework eliminates infrastructure complexity so your team can focus on **research quality**:

- No time spent on data cleaning ✅
- No time spent on backtest implementation ✅
- No time spent on metric calculation ✅
- **All time in Task 2 & 3 goes to hypothesis generation, testing, and validation** ✅

The judges want to see:
1. Quality of hypotheses (what alpha are you testing?)
2. Robustness of evidence (does it hold up under stress?)
3. Distinctness of alphas (are strategies truly different?)
4. Thoughtfulness of analysis (why do these work/fail?)

This framework makes all of that possible.

---

**Ready to build strategies?** 🚀

Start with `QUICK_START.txt`, then dive into `TASK2_ROADMAP.md`.

Good luck! 💪
