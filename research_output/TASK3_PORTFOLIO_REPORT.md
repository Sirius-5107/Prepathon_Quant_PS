# Task 3: Portfolio Construction and Allocation

## Executive Summary

We constructed and compared multiple portfolio allocation strategies using the two selected
strategies from Task 2 (PB07 price/book mean reversion and BB01 Bollinger Band breakout).
The analysis includes static allocations and walk-forward dynamic rebalancing.

---

## Methodology

### Data
- Period: 2018-01-02 to 2021-11-01 (866 observations)
- Strategies: PB07 (70% baseline) and BB01 (30% baseline) from Task 2
- Return type: Daily mark-to-market (MTM), transaction costs included
- Long-only, no leverage

### Static Allocators
1. **Baseline (70/30)**: Task 2 canonical allocation
2. **Equal-Weight (50/50)**: Simple equal allocation
3. **Risk-Parity**: Equal marginal risk contribution using full-sample volatility
4. **Optimize Sharpe**: Constrained mean-variance optimization (long-only)
5. **Grid Search**: Exhaustive search over 10% allocation increments

### Dynamic Allocator
- **Method**: Walk-forward risk-parity with rolling rebalancing
- **Training**: 2-year window (504 trading days)
- **Testing**: 1-year holdout (252 trading days)
- **Rebalance**: Quarterly (every 63 trading days)
- **Window 1**: Train 2018-2019, test 2020
- **Window 2**: Train 2019-2020, test 2021

---

## Key Results

| Allocator | Total Return | Annual Vol | Sharpe | Max DD | Calmar |
|-----------|--------------|------------|--------|--------|--------|
| baseline             |        3.82% |      0.55% |  1.992 | -3.24% |  0.339 |
| equal_weight         |        3.42% |      0.53% |  1.833 | -3.11% |  0.316 |
| risk_parity          |        3.46% |      0.53% |  1.859 | -3.13% |  0.318 |
| optimize_sharpe      |        3.93% |      0.56% |  1.999 | -3.27% |  0.344 |
| dynamic              |        3.30% |      0.54% |  1.751 | -3.08% |  0.309 |

---

## Analysis

### Static Allocation Results

The baseline 70/30 allocation (Task 2) generates 3.82% total return
with a Sharpe ratio of 1.992.

Equal-weight allocation produces 3.42% return
with Sharpe 1.833.

Risk-parity allocation yields 3.46% return
with Sharpe 1.859.

Mean-variance optimization achieves 3.93% return
with Sharpe 1.999.

### Dynamic Allocation Results

The walk-forward risk-parity allocator achieves 3.30% total return
with Sharpe 1.751.
Average quarterly turnover: 0.00%

---

## Files Generated

- `task3_static_allocators.csv` — Metrics for all static allocators
- `task3_grid_search.csv` — Grid search results (10% increments)
- `task3_dynamic_weights.csv` — Time-varying weights from walk-forward
- `task3_portfolio_comparison.csv` — Equity curves for all allocators
- `task3_allocator_comparison.csv` — Summary metrics comparison

---

## Conclusion

The portfolio allocation analysis identifies the optimal weight allocation between PB07 and BB01.
Static allocations provide a clear baseline, while dynamic walk-forward allocation demonstrates
the potential for weight adaptation based on recent market conditions.

**Recommended allocation: 70% PB07 + 30% BB01**
based on Task 2 research findings.