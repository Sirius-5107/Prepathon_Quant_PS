"""
Task 2 canonical submission integrity audit.

Checks the corrected causal PB07 implementation and canonical 70/30
PB07/BB01 return stream. This script is an audit only; it does not
optimize parameters or alter research outputs.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "research_output"

bb01 = pd.read_csv(OUT / "strategy_bb01_trades.csv")
pb07 = pd.read_csv(OUT / "strategy_02_trades.csv")
daily = pd.read_csv(OUT / "portfolio_daily_returns.csv")

assert len(pb07) == 15, f"Expected 15 corrected PB07 trades, got {len(pb07)}"
assert len(bb01) == 17, f"Expected 17 BB01 trades, got {len(bb01)}"
assert len(daily) == 866, f"Expected 866 observations, got {len(daily)}"

portfolio_col = "port_30_70"
assert portfolio_col in daily.columns, f"Missing canonical column: {portfolio_col}"

rets = daily[portfolio_col].to_numpy(dtype=float)
equity = np.cumprod(1.0 + rets)
total_return = equity[-1] - 1.0
ann_vol = np.std(rets) * np.sqrt(252)
years = len(rets) / 252
ann_return = (1.0 + total_return) ** (1.0 / years) - 1.0
sharpe = ann_return / ann_vol
running_max = np.maximum.accumulate(equity)
max_dd = np.min(equity / running_max - 1.0)

metrics = json.loads((OUT / "portfolio_metrics.json").read_text())
reported = metrics["portfolio_30_70"]

checks = {
    "PB07 trades": len(pb07) == 15,
    "BB01 trades": len(bb01) == 17,
    "combined trades": len(pb07) + len(bb01) == 32,
    "observations": len(daily) == 866,
    "return": np.isclose(total_return, 0.2767412687419928, atol=1e-10),
    "sharpe": np.isclose(sharpe, 0.9161, atol=1e-4),
    "max_drawdown": np.isclose(max_dd, -0.0985, atol=5e-4),
    "reported return": np.isclose(reported["total_return"], total_return, atol=1e-10),
}

print("=" * 72)
print("TASK 2 CANONICAL SUBMISSION INTEGRITY AUDIT")
print("=" * 72)
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL':4s}  {name}")
assert all(checks.values()), "Canonical Task 2 audit failed"

print()
print(f"Canonical return : {total_return * 100:.4f}%")
print(f"Canonical Sharpe : {sharpe:.4f}")
print(f"Canonical max DD : {max_dd * 100:.4f}%")
print("Canonical trades  : 32 (17 BB01 + 15 PB07)")
print("Status            : PASS")
