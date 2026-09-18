"""Strictly out-of-sample dynamic allocation.

A 504-observation rolling training window is used to estimate two-asset ERC
weights at each quarterly rebalance. The weights are applied only to the next
quarter. No backfill or use of future observations is permitted.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar


class DynamicAllocator:
    def __init__(self, bb01_returns, pb07_returns, dates):
        self.bb01_returns = np.asarray(bb01_returns, dtype=float)
        self.pb07_returns = np.asarray(pb07_returns, dtype=float)
        self.dates = pd.DatetimeIndex(dates)
        self.n_obs = len(self.dates)

    @staticmethod
    def _erc_weights(bb01, pb07):
        cov = np.cov(np.column_stack([pb07, bb01]), rowvar=False, ddof=1)

        def loss(w_pb07):
            w = np.array([w_pb07, 1.0 - w_pb07])
            rc = w * (cov @ w)
            return float((rc[0] - rc[1]) ** 2)

        res = minimize_scalar(loss, bounds=(0.0, 1.0), method="bounded",
                              options={"xatol": 1e-12})
        w = float(res.x)
        return w, 1.0 - w

    def run_walk_forward(self, train_days=504, rebalance_days=63):
        if self.n_obs <= train_days:
            raise ValueError("Not enough observations for the requested training window")

        records = []
        window_id = 0
        for test_start in range(train_days, self.n_obs, rebalance_days):
            test_end = min(test_start + rebalance_days, self.n_obs)
            train_start = test_start - train_days

            w_pb07, w_bb01 = self._erc_weights(
                self.bb01_returns[train_start:test_start],
                self.pb07_returns[train_start:test_start],
            )
            window_id += 1
            for i in range(test_start, test_end):
                records.append({
                    "date": self.dates[i],
                    "w_pb07": w_pb07,
                    "w_bb01": w_bb01,
                    "window": window_id,
                    "train_start": self.dates[train_start],
                    "train_end": self.dates[test_start - 1],
                    "test_start": self.dates[test_start],
                    "test_end": self.dates[test_end - 1],
                    "method": "erc_wfo",
                })

        weights = pd.DataFrame(records)
        if weights.empty:
            raise ValueError("No OOS periods generated")
        return weights

    def validate_no_lookahead(self, weights_df, train_days=504):
        w = weights_df.sort_values("date")
        first_oos = self.dates[train_days]
        if w["date"].min() != first_oos:
            raise AssertionError("Dynamic weights must begin at first OOS date")
        if w["date"].max() != self.dates[-1]:
            raise AssertionError("Dynamic weights must cover the final observation")
        if w["date"].min() <= self.dates[train_days - 1]:
            raise AssertionError("Weight applied before its training window ended")
        if not np.allclose(w["w_pb07"] + w["w_bb01"], 1.0):
            raise AssertionError("Weights do not sum to one")
        if (w[["w_pb07", "w_bb01"]] < 0).any().any():
            raise AssertionError("Negative dynamic weights")
        return True


def run_dynamic_allocation_study(portfolio_engine):
    allocator = DynamicAllocator(
        portfolio_engine.bb01_returns,
        portfolio_engine.pb07_returns,
        portfolio_engine.dates,
    )
    weights = allocator.run_walk_forward(train_days=504, rebalance_days=63)
    allocator.validate_no_lookahead(weights, train_days=504)

    # Dynamic performance is evaluated only on genuine OOS observations.
    oos = portfolio_engine.construct_dynamic_portfolio(weights)
    return {
        "weights": weights,
        "portfolio": oos,
        "turnover": portfolio_engine.get_turnover(weights),
        "n_oos_windows": int(weights["window"].nunique()),
        "oos_start": str(weights["date"].min().date()),
    }
