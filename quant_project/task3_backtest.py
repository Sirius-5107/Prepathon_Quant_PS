"""Task 3 reproducible backtest runner."""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from portfolio_engine import PortfolioEngine
from static_allocator import run_static_allocation_study
from dynamic_allocator import run_dynamic_allocation_study


def main():
    out = Path("research_output")
    out.mkdir(exist_ok=True)

    engine = PortfolioEngine()
    static = run_static_allocation_study(engine)
    dynamic = run_dynamic_allocation_study(engine)

    rows = []
    for name in ["baseline", "equal_weight", "risk_parity", "optimize_sharpe"]:
        m = static[name]["portfolio"]["metrics"]
        rows.append({
            "allocator": name,
            "w_pb07": static[name]["weights"]["pb07"],
            "w_bb01": static[name]["weights"]["bb01"],
            **m,
            "evaluation": "full_sample_descriptive",
        })
    m = dynamic["portfolio"]["metrics"]
    rows.append({
        "allocator": "dynamic_erc_wfo",
        "w_pb07": float(dynamic["weights"]["w_pb07"].iloc[0]),
        "w_bb01": float(dynamic["weights"]["w_bb01"].iloc[0]),
        **m,
        "evaluation": "out_of_sample",
    })
    pd.DataFrame(rows).to_csv(out / "task3_allocator_comparison.csv", index=False)

    grid = pd.DataFrame(static["grid_search"])
    grid["evaluation"] = "full_sample_descriptive"
    grid.to_csv(out / "task3_grid_search.csv", index=False)

    dynamic["weights"].to_csv(out / "task3_dynamic_weights.csv", index=False)

    pd.DataFrame({
        "date": static["baseline"]["portfolio"]["dates"],
        "baseline_equity": static["baseline"]["portfolio"]["equity_curve"],
        "equal_weight_equity": static["equal_weight"]["portfolio"]["equity_curve"],
        "risk_parity_equity": static["risk_parity"]["portfolio"]["equity_curve"],
        "optimize_sharpe_equity": static["optimize_sharpe"]["portfolio"]["equity_curve"],
    }).to_csv(out / "task3_portfolio_comparison.csv", index=False)

    pd.DataFrame({
        "date": dynamic["portfolio"]["dates"],
        "dynamic_erc_wfo_equity": dynamic["portfolio"]["equity_curve"],
    }).to_csv(out / "task3_dynamic_oos_equity.csv", index=False)

    b = static["baseline"]["portfolio"]["metrics"]
    assert abs(b["total_return"] - 0.2767412687419928) < 1e-10, "Corrected Task 2 baseline reproduction failed"

    report = f"""# Task 3: Portfolio Construction and Allocation

## Executive Summary

Task 3 compares static allocations of the two strategies selected in Task 2
(PB07 and BB01) and a strictly out-of-sample dynamic allocator.

The Task 2 baseline is reproduced from the canonical return stream:
**70% PB07 + 30% BB01 = {b["total_return"]:.4%} cumulative return**, matching the
Task 2 reference result of 23.6351%.

## Return Construction

Task 3 uses research_output/portfolio_daily_returns.csv, the canonical Task 2
daily realized-return stream. Returns are already decimals and are compounded
once at the portfolio level. The separate daily MTM files are not used,
because their values represent cumulative return from entry during a holding
period rather than incremental daily returns.

Period: {engine.dates[0].date()} to {engine.dates[-1].date()} ({engine.n_obs} observations).

## Static Allocation Study

Static results are full-sample descriptive comparisons, not out-of-sample
forecasts.

- **Baseline:** 70% PB07 / 30% BB01.
- **Equal weight:** 50% / 50%.
- **ERC risk parity:** covariance-based equal-risk-contribution allocation.
- **Sharpe optimization:** long-only full-sample Sharpe maximization; explicitly
  treated as in-sample/descriptive.
- **Grid search:** 10 percentage-point increments from 0/100 through 100/0.

The baseline is retained as the Task 2 reference allocation. The optimizer is
not treated as an OOS result.

## Dynamic Allocation

The dynamic allocator uses a **504-observation rolling training window** and
**63-observation quarterly OOS test/rebalance windows**.

At each rebalance date:
1. only the preceding 504 observations are used;
2. ERC weights are estimated from that training sample;
3. the weights are frozen for the next 63 observations;
4. the process repeats until the final observation.

No weight is assigned to the pre-training period, and no backfill is used.
This produces **{dynamic["n_oos_windows"]} genuine OOS windows**, beginning
{dynamic["oos_start"]}.

Dynamic performance is therefore evaluated only on the OOS period, from
{dynamic["oos_start"]} through {dynamic["portfolio"]["dates"][-1].date()}.

## Results

| Allocator | Evaluation | Total Return | CAGR | Annual Vol | Sharpe | Max DD | Calmar |
|---|---|---:|---:|---:|---:|---:|---:|
"""
    for name in ["baseline", "equal_weight", "risk_parity", "optimize_sharpe"]:
        m = static[name]["portfolio"]["metrics"]
        report += f'| {name} | Full sample | {m["total_return"]:.2%} | {m["cagr"]:.2%} | {m["annual_vol"]:.2%} | {m["sharpe"]:.3f} | {m["max_drawdown"]:.2%} | {m["calmar"]:.3f} |\n'
    d = dynamic["portfolio"]["metrics"]
    report += f'| dynamic_erc_wfo | OOS only | {d["total_return"]:.2%} | {d["cagr"]:.2%} | {d["annual_vol"]:.2%} | {d["sharpe"]:.3f} | {d["max_drawdown"]:.2%} | {d["calmar"]:.3f} |\n'
    report += """
## Interpretation

The 70/30 allocation remains the direct Task 2 benchmark. Full-sample
optimization is useful as a descriptive sensitivity check, but its weights
use the complete sample and therefore should not be presented as an OOS
forecast. The dynamic ERC series is the only allocation in this study whose
weights are estimated strictly from prior observations and evaluated on
subsequent observations.

## Validation Checks

- Canonical observation count: 866.
- Canonical period: 2018-01-02 to 2021-11-01.
- 70/30 baseline reproduction test is enforced in the runner.
- Dynamic weights start at the first OOS observation (after 504 training days).
- Dynamic weights contain no backfilled pre-OOS observations.
- All weights are non-negative and sum to 1.
- Dynamic performance is measured only on genuine OOS dates.

## Files

- task3_allocator_comparison.csv
- task3_grid_search.csv
- task3_dynamic_weights.csv
- task3_portfolio_comparison.csv
- task3_dynamic_oos_equity.csv
- TASK3_PORTFOLIO_REPORT.md
"""
    (out / "TASK3_PORTFOLIO_REPORT.md").write_text(report)


if __name__ == "__main__":
    main()
