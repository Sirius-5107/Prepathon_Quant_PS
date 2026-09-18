"""
Task 3 Backtest

Runs comprehensive portfolio allocation study:
1. Static allocators (equal-weight, baseline, risk-parity, optimization, grid)
2. Dynamic allocator (walk-forward risk-parity)
3. Comparative analysis and metrics
4. Generates CSV outputs and markdown report
"""

import sys
import numpy as np
import pandas as pd
import json
from pathlib import Path

# Add quant_project to path
sys.path.insert(0, str(Path(__file__).parent))

from portfolio_engine import PortfolioEngine
from static_allocator import run_static_allocation_study
from dynamic_allocator import run_dynamic_allocation_study


def save_results_to_csv(results, output_dir="research_output"):
    """Save results to CSV files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 1. Static allocator comparison
    static_metrics = []
    for name, data in results['static_allocations'].items():
        if name == 'grid_search':
            continue
        
        metrics = data['portfolio']['metrics'].copy()
        metrics['allocator'] = name
        metrics['w_pb07'] = data['weights']['pb07']
        metrics['w_bb01'] = data['weights']['bb01']
        static_metrics.append(metrics)
    
    static_df = pd.DataFrame(static_metrics)
    static_df.to_csv(output_dir / "task3_static_allocators.csv", index=False)
    
    # 2. Grid search results
    grid_df = pd.DataFrame(results['static_allocations']['grid_search'])
    grid_df.to_csv(output_dir / "task3_grid_search.csv", index=False)
    
    # 3. Dynamic allocation results
    results['dynamic_allocation']['weights'].to_csv(
        output_dir / "task3_dynamic_weights.csv",
        index=False
    )
    
    # 4. Portfolio comparison (equity curves)
    portfolio_comparison = pd.DataFrame({
        'date': results['static_allocations']['baseline']['portfolio']['dates'],
        'baseline_equity': results['static_allocations']['baseline']['portfolio']['equity_curve'],
        'equal_weight_equity': results['static_allocations']['equal_weight']['portfolio']['equity_curve'],
        'risk_parity_equity': results['static_allocations']['risk_parity']['portfolio']['equity_curve'],
        'optimize_sharpe_equity': results['static_allocations']['optimize_sharpe']['portfolio']['equity_curve'],
        'dynamic_equity': results['dynamic_allocation']['portfolio']['equity_curve']
    })
    portfolio_comparison.to_csv(output_dir / "task3_portfolio_comparison.csv", index=False)
    
    # 5. Annual returns
    annual_comparison = pd.DataFrame({
        'allocator': ['baseline', 'equal_weight', 'risk_parity', 'optimize_sharpe', 'dynamic'],
        'total_return': [
            results['static_allocations']['baseline']['portfolio']['metrics']['total_return'],
            results['static_allocations']['equal_weight']['portfolio']['metrics']['total_return'],
            results['static_allocations']['risk_parity']['portfolio']['metrics']['total_return'],
            results['static_allocations']['optimize_sharpe']['portfolio']['metrics']['total_return'],
            results['dynamic_allocation']['portfolio']['metrics']['total_return']
        ],
        'sharpe': [
            results['static_allocations']['baseline']['portfolio']['metrics']['sharpe'],
            results['static_allocations']['equal_weight']['portfolio']['metrics']['sharpe'],
            results['static_allocations']['risk_parity']['portfolio']['metrics']['sharpe'],
            results['static_allocations']['optimize_sharpe']['portfolio']['metrics']['sharpe'],
            results['dynamic_allocation']['portfolio']['metrics']['sharpe']
        ]
    })
    annual_comparison.to_csv(output_dir / "task3_allocator_comparison.csv", index=False)
    
    print(f"✓ Results saved to {output_dir}/")


def generate_report(results, output_dir="research_output"):
    """Generate markdown report."""
    output_dir = Path(output_dir)
    
    report_lines = [
        "# Task 3: Portfolio Construction and Allocation",
        "",
        "## Executive Summary",
        "",
        "We constructed and compared multiple portfolio allocation strategies using the two selected",
        "strategies from Task 2 (PB07 price/book mean reversion and BB01 Bollinger Band breakout).",
        "The analysis includes static allocations and walk-forward dynamic rebalancing.",
        "",
        "---",
        "",
        "## Methodology",
        "",
        "### Data",
        f"- Period: 2018-01-02 to 2021-11-01 ({results['n_obs']} observations)",
        "- Strategies: PB07 (70% baseline) and BB01 (30% baseline) from Task 2",
        "- Return type: Daily mark-to-market (MTM), transaction costs included",
        "- Long-only, no leverage",
        "",
        "### Static Allocators",
        "1. **Baseline (70/30)**: Task 2 canonical allocation",
        "2. **Equal-Weight (50/50)**: Simple equal allocation",
        "3. **Risk-Parity**: Equal marginal risk contribution using full-sample volatility",
        "4. **Optimize Sharpe**: Constrained mean-variance optimization (long-only)",
        "5. **Grid Search**: Exhaustive search over 10% allocation increments",
        "",
        "### Dynamic Allocator",
        "- **Method**: Walk-forward risk-parity with rolling rebalancing",
        "- **Training**: 2-year window (504 trading days)",
        "- **Testing**: 1-year holdout (252 trading days)",
        "- **Rebalance**: Quarterly (every 63 trading days)",
        "- **Window 1**: Train 2018-2019, test 2020",
        "- **Window 2**: Train 2019-2020, test 2021",
        "",
        "---",
        "",
        "## Key Results",
        "",
    ]
    
    # Add metrics summary
    metrics_keys = ['total_return', 'sharpe', 'annual_vol', 'max_drawdown', 'calmar']
    
    report_lines.append("| Allocator | Total Return | Annual Vol | Sharpe | Max DD | Calmar |")
    report_lines.append("|-----------|--------------|------------|--------|--------|--------|")
    
    for name in ['baseline', 'equal_weight', 'risk_parity', 'optimize_sharpe', 'dynamic']:
        if name == 'dynamic':
            metrics = results['dynamic_allocation']['portfolio']['metrics']
        else:
            metrics = results['static_allocations'][name]['portfolio']['metrics']
        
        ret = f"{metrics['total_return']:.2%}"
        vol = f"{metrics['annual_vol']:.2%}"
        sharpe = f"{metrics['sharpe']:.3f}"
        mdd = f"{metrics['max_drawdown']:.2%}"
        calmar = f"{metrics['calmar']:.3f}"
        
        report_lines.append(f"| {name:20s} | {ret:>12s} | {vol:>10s} | {sharpe:>6s} | {mdd:>6s} | {calmar:>6s} |")
    
    report_lines.extend([
        "",
        "---",
        "",
        "## Analysis",
        "",
        "### Static Allocation Results",
        "",
        f"The baseline 70/30 allocation (Task 2) generates {results['static_allocations']['baseline']['portfolio']['metrics']['total_return']:.2%} total return",
        f"with a Sharpe ratio of {results['static_allocations']['baseline']['portfolio']['metrics']['sharpe']:.3f}.",
        "",
        f"Equal-weight allocation produces {results['static_allocations']['equal_weight']['portfolio']['metrics']['total_return']:.2%} return",
        f"with Sharpe {results['static_allocations']['equal_weight']['portfolio']['metrics']['sharpe']:.3f}.",
        "",
        f"Risk-parity allocation yields {results['static_allocations']['risk_parity']['portfolio']['metrics']['total_return']:.2%} return",
        f"with Sharpe {results['static_allocations']['risk_parity']['portfolio']['metrics']['sharpe']:.3f}.",
        "",
        f"Mean-variance optimization achieves {results['static_allocations']['optimize_sharpe']['portfolio']['metrics']['total_return']:.2%} return",
        f"with Sharpe {results['static_allocations']['optimize_sharpe']['portfolio']['metrics']['sharpe']:.3f}.",
        "",
        "### Dynamic Allocation Results",
        "",
        f"The walk-forward risk-parity allocator achieves {results['dynamic_allocation']['portfolio']['metrics']['total_return']:.2%} total return",
        f"with Sharpe {results['dynamic_allocation']['portfolio']['metrics']['sharpe']:.3f}.",
        f"Average quarterly turnover: {results['dynamic_allocation']['turnover']:.2%}",
        "",
        "---",
        "",
        "## Files Generated",
        "",
        "- `task3_static_allocators.csv` — Metrics for all static allocators",
        "- `task3_grid_search.csv` — Grid search results (10% increments)",
        "- `task3_dynamic_weights.csv` — Time-varying weights from walk-forward",
        "- `task3_portfolio_comparison.csv` — Equity curves for all allocators",
        "- `task3_allocator_comparison.csv` — Summary metrics comparison",
        "",
        "---",
        "",
        "## Conclusion",
        "",
        "The portfolio allocation analysis identifies the optimal weight allocation between PB07 and BB01.",
        "Static allocations provide a clear baseline, while dynamic walk-forward allocation demonstrates",
        "the potential for weight adaptation based on recent market conditions.",
        "",
        f"**Recommended allocation: {results['static_allocations']['baseline']['weights']['pb07']:.0%} PB07 + {results['static_allocations']['baseline']['weights']['bb01']:.0%} BB01**",
        "based on Task 2 research findings.",
    ])
    
    report_text = "\n".join(report_lines)
    
    report_path = output_dir / "TASK3_PORTFOLIO_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    print(f"✓ Report saved to {report_path}")


def main():
    """Main execution."""
    print("=" * 80)
    print("TASK 3: PORTFOLIO CONSTRUCTION AND ALLOCATION")
    print("=" * 80)
    print()
    
    # Load portfolio engine
    print("Loading strategy returns from Task 2...")
    portfolio_engine = PortfolioEngine()
    print(f"  ✓ Loaded {portfolio_engine.n_obs} observations")
    print(f"  ✓ Period: {portfolio_engine.dates[0].date()} to {portfolio_engine.dates[-1].date()}")
    print()
    
    # Run static allocations
    print("Running static allocation study...")
    static_results = run_static_allocation_study(portfolio_engine)
    print("  ✓ Equal-weight allocation")
    print("  ✓ Baseline (70/30) allocation")
    print("  ✓ Risk-parity allocation")
    print("  ✓ Mean-variance optimization")
    print("  ✓ Grid search (10% increments)")
    print()
    
    # Run dynamic allocation
    print("Running walk-forward dynamic allocation...")
    dynamic_results = run_dynamic_allocation_study(portfolio_engine)
    print("  ✓ Walk-forward risk-parity (2-year train, 1-year test)")
    print(f"  ✓ Average turnover: {dynamic_results['turnover']:.2%}")
    print()
    
    # Combine results
    results = {
        'n_obs': portfolio_engine.n_obs,
        'dates': portfolio_engine.dates,
        'static_allocations': static_results,
        'dynamic_allocation': dynamic_results
    }
    
    # Save results
    print("Saving results...")
    save_results_to_csv(results)
    print()
    
    # Generate report
    print("Generating report...")
    generate_report(results)
    print()
    
    # Print summary
    print("=" * 80)
    print("TASK 3 COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    for name, data in static_results.items():
        if name == 'grid_search':
            continue
        metrics = data['portfolio']['metrics']
        print(f"  {name:20s}: {metrics['total_return']:>8.2%} return, {metrics['sharpe']:>6.3f} Sharpe")
    
    metrics = dynamic_results['portfolio']['metrics']
    print(f"  {'dynamic':20s}: {metrics['total_return']:>8.2%} return, {metrics['sharpe']:>6.3f} Sharpe")
    print()
    print("✓ All results saved to research_output/")
    print()


if __name__ == "__main__":
    main()
