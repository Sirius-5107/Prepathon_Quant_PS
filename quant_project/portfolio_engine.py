"""Task 3 portfolio engine using the canonical Task 2 return stream.

The canonical Task 2 file is research_output/portfolio_daily_returns.csv.
Its returns are already decimal daily realized strategy returns:
zero on non-exit days and the net trade return on exit days.

Task 3 never reconstructs or compounds cumulative-from-entry MTM values.
"""

from pathlib import Path
import numpy as np
import pandas as pd


class PortfolioEngine:
    def __init__(self, data_dir="research_output"):
        self.data_dir = Path(data_dir)
        self._load_returns()
        self._validate()

    def _load_returns(self):
        path = self.data_dir / "portfolio_daily_returns.csv"
        df = pd.read_csv(path, parse_dates=["date"]).sort_values("date")
        required = {"date", "bb01_daily_return", "pb07_daily_return"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing canonical return columns: {sorted(missing)}")
        if df["date"].duplicated().any():
            raise ValueError("Duplicate dates in canonical return stream")

        self.dates = pd.DatetimeIndex(df["date"])
        self.bb01_returns = df["bb01_daily_return"].astype(float).to_numpy()
        self.pb07_returns = df["pb07_daily_return"].astype(float).to_numpy()
        self.n_obs = len(df)

    def _validate(self):
        if len(self.bb01_returns) != len(self.pb07_returns):
            raise AssertionError("Returns not aligned")
        if self.dates.is_monotonic_increasing is False:
            raise AssertionError("Dates are not sorted")
        if np.isnan(self.bb01_returns).any() or np.isnan(self.pb07_returns).any():
            raise AssertionError("Canonical returns contain NaNs")
        if np.min(self.bb01_returns) <= -1 or np.min(self.pb07_returns) <= -1:
            raise AssertionError("Return <= -100% is invalid")
        if self.n_obs != 866:
            raise AssertionError(f"Expected 866 canonical observations, found {self.n_obs}")

    @staticmethod
    def _metrics(returns):
        returns = np.asarray(returns, dtype=float)
        equity = np.cumprod(1.0 + returns)
        n = len(returns)
        total = equity[-1] - 1.0
        cagr = equity[-1] ** (252.0 / n) - 1.0
        vol = np.std(returns, ddof=0) * np.sqrt(252.0)
        sharpe = np.mean(returns) / (np.std(returns, ddof=0) + 1e-12) * np.sqrt(252.0)
        downside = returns[returns < 0]
        downside_dev = np.sqrt(np.mean(np.square(downside))) * np.sqrt(252.0) if len(downside) else np.nan
        sortino = np.mean(returns) * np.sqrt(252.0) / (downside_dev + 1e-12) if len(downside) else np.nan
        running_max = np.maximum.accumulate(equity)
        max_dd = np.min(equity / running_max - 1.0)
        calmar = cagr / (abs(max_dd) + 1e-12)
        return {
            "total_return": total,
            "cagr": cagr,
            "annual_vol": vol,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "calmar": calmar,
            "n_obs": n,
        }

    def construct_portfolio(self, w_pb07, w_bb01):
        if abs(w_pb07 + w_bb01 - 1.0) > 1e-10 or min(w_pb07, w_bb01) < 0:
            raise ValueError("Weights must be non-negative and sum to one")
        returns = w_pb07 * self.pb07_returns + w_bb01 * self.bb01_returns
        return {
            "returns": returns,
            "equity_curve": np.cumprod(1.0 + returns),
            "dates": self.dates,
            "weights": {"pb07": float(w_pb07), "bb01": float(w_bb01)},
            "metrics": self._metrics(returns),
        }

    def construct_dynamic_portfolio(self, weights_df):
        w = weights_df.copy()
        w["date"] = pd.to_datetime(w["date"])
        w = w.sort_values("date")
        if w["date"].duplicated().any():
            raise ValueError("Duplicate dynamic weight dates")
        if w[["w_pb07", "w_bb01"]].isna().any().any():
            raise ValueError("Dynamic weights contain NaNs")
        if not np.allclose(w["w_pb07"] + w["w_bb01"], 1.0):
            raise ValueError("Dynamic weights do not sum to one")
        if (w[["w_pb07", "w_bb01"]] < 0).any().any():
            raise ValueError("Dynamic weights contain short positions")

        merged = pd.DataFrame({"date": self.dates}).merge(w, on="date", how="left")
        # No backfill: performance begins only when genuine OOS weights exist.
        if merged["w_pb07"].isna().any():
            raise ValueError("Dynamic weights do not cover every performance date")
        returns = merged["w_pb07"].to_numpy() * self.pb07_returns + merged["w_bb01"].to_numpy() * self.bb01_returns
        return {
            "returns": returns,
            "equity_curve": np.cumprod(1.0 + returns),
            "dates": self.dates,
            "weights_df": merged,
            "metrics": self._metrics(returns),
        }

    def get_turnover(self, weights_df):
        w = weights_df.sort_values("date")
        changes = np.abs(w[["w_pb07", "w_bb01"]].diff()).sum(axis=1)
        return float(changes.fillna(0.0).sum())

    def get_yearly_returns(self, returns):
        df = pd.DataFrame({"date": self.dates, "return": returns})
        return df.groupby(df["date"].dt.year)["return"].apply(lambda x: np.prod(1.0 + x.to_numpy()) - 1.0).to_dict()
