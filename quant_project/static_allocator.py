"""Static portfolio allocators for Task 3."""

import numpy as np
from scipy.optimize import minimize_scalar


class StaticAllocator:
    @staticmethod
    def equal_weight():
        return {"pb07": 0.50, "bb01": 0.50}

    @staticmethod
    def baseline():
        return {"pb07": 0.70, "bb01": 0.30}

    @staticmethod
    def risk_parity(bb01_returns, pb07_returns):
        """True two-asset equal-risk-contribution (ERC) allocation."""
        x = np.column_stack([pb07_returns, bb01_returns])
        cov = np.cov(x, rowvar=False, ddof=1)

        def objective(w_pb07):
            w = np.array([w_pb07, 1.0 - w_pb07])
            marginal = cov @ w
            contributions = w * marginal
            return (contributions[0] - contributions[1]) ** 2

        res = minimize_scalar(objective, bounds=(0.0, 1.0), method="bounded",
                              options={"xatol": 1e-12})
        w = float(res.x)
        return {"pb07": w, "bb01": 1.0 - w}

    @staticmethod
    def optimize_sharpe(bb01_returns, pb07_returns):
        """Full-sample, in-sample descriptive Sharpe maximization."""
        mu = np.array([np.mean(pb07_returns), np.mean(bb01_returns)])
        cov = np.cov(np.column_stack([pb07_returns, bb01_returns]), rowvar=False, ddof=1)

        def negative_sharpe(w_pb07):
            w = np.array([w_pb07, 1.0 - w_pb07])
            ret = float(w @ mu)
            vol = float(np.sqrt(w @ cov @ w))
            return -ret / (vol + 1e-12)

        res = minimize_scalar(negative_sharpe, bounds=(0.0, 1.0), method="bounded",
                              options={"xatol": 1e-12})
        w = float(res.x)
        return {"pb07": w, "bb01": 1.0 - w}

    @staticmethod
    def grid_search(bb01_returns, pb07_returns, step=0.10):
        results = []
        for w_pb07 in np.arange(0.0, 1.0 + step / 2, step):
            w_bb01 = 1.0 - w_pb07
            r = w_pb07 * pb07_returns + w_bb01 * bb01_returns
            equity = np.cumprod(1.0 + r)
            running_max = np.maximum.accumulate(equity)
            results.append({
                "w_pb07": float(w_pb07),
                "w_bb01": float(w_bb01),
                "total_return": float(equity[-1] - 1.0),
                "annual_vol": float(np.std(r) * np.sqrt(252)),
                "sharpe": float(np.mean(r) / (np.std(r) + 1e-12) * np.sqrt(252)),
                "max_drawdown": float(np.min(equity / running_max - 1.0)),
            })
        return results


def run_static_allocation_study(portfolio_engine):
    allocator = StaticAllocator()
    bb01 = portfolio_engine.bb01_returns
    pb07 = portfolio_engine.pb07_returns
    out = {}

    for name, weights in [
        ("equal_weight", allocator.equal_weight()),
        ("baseline", allocator.baseline()),
        ("risk_parity", allocator.risk_parity(bb01, pb07)),
        ("optimize_sharpe", allocator.optimize_sharpe(bb01, pb07)),
    ]:
        out[name] = {
            "weights": weights,
            "portfolio": portfolio_engine.construct_portfolio(weights["pb07"], weights["bb01"]),
        }

    out["grid_search"] = allocator.grid_search(bb01, pb07)
    return out
