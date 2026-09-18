"""
Portfolio Engine

Loads Task 2 strategy returns, constructs weighted portfolios,
calculates equity curves, drawdowns, and comprehensive metrics.

Financial methodology:
- Daily returns: mark-to-market (MTM)
- Sparse structure: zero = no position, non-zero = realized P&L
- Portfolio return: w_pb07 * r_pb07 + w_bb01 * r_bb01
- Long-only, no leverage, transaction costs already included in strategy returns

Date range: 2018-01-02 to 2021-11-01 (867 observations)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json


class PortfolioEngine:
    """
    Loads canonical Task 2 returns and constructs portfolios.
    
    Attributes:
        bb01_returns: Series of BB01 daily MTM returns
        pb07_returns: Series of PB07 daily MTM returns
        dates: Aligned dates for both strategies
        n_obs: Number of observations
    """
    
    def __init__(self, data_dir="research_output"):
        """
        Load strategy returns from Task 2 output files.
        
        Args:
            data_dir: Path to research_output directory
        """
        self.data_dir = Path(data_dir)
        self._load_returns()
        self._validate()
    
    def _load_returns(self):
        """Load BB01 and PB07 daily MTM returns."""
        # Load BB01 returns
        bb01_path = self.data_dir / "strategy_bb01_daily_mtm.csv"
        bb01_df = pd.read_csv(bb01_path)
        bb01_df["date"] = pd.to_datetime(bb01_df["date"])
        bb01_df = bb01_df.set_index("date")
        
        # Load PB07 returns
        pb07_path = self.data_dir / "strategy_pb07_daily_mtm.csv"
        pb07_df = pd.read_csv(pb07_path)
        pb07_df["date"] = pd.to_datetime(pb07_df["date"])
        pb07_df = pb07_df.set_index("date")
        
        # Align on dates
        common_dates = bb01_df.index.intersection(pb07_df.index)
        self.bb01_returns = bb01_df.loc[common_dates, "bb01_daily_return"].values / 100.0
        self.pb07_returns = pb07_df.loc[common_dates, "pb07_daily_return"].values / 100.0
        self.dates = common_dates
        self.n_obs = len(self.dates)
    
    def _validate(self):
        """Validate loaded returns."""
        # Check alignment
        assert len(self.bb01_returns) == len(self.pb07_returns), "Returns not aligned"
        assert len(self.dates) == self.n_obs, "Date mismatch"
        
        # Check NaNs
        assert not np.isnan(self.bb01_returns).any(), "BB01 has NaNs"
        assert not np.isnan(self.pb07_returns).any(), "PB07 has NaNs"
        
        # Check magnitude sanity
        assert self.bb01_returns.min() > -0.20, "BB01 daily return < -20%, implausible"
        assert self.pb07_returns.min() > -0.20, "PB07 daily return < -20%, implausible"
    
    def construct_portfolio(self, w_pb07, w_bb01):
        """
        Construct portfolio with fixed weights.
        
        Args:
            w_pb07: Weight allocated to PB07
            w_bb01: Weight allocated to BB01
        
        Returns:
            dict with returns, equity curve, metrics
        """
        assert abs(w_pb07 + w_bb01 - 1.0) < 1e-10, "Weights must sum to 1"
        assert w_pb07 >= 0 and w_bb01 >= 0, "No short positions allowed"
        
        # Daily portfolio return
        portfolio_returns = w_pb07 * self.pb07_returns + w_bb01 * self.bb01_returns
        
        # Equity curve (assuming $1 initial capital)
        equity_curve = np.cumprod(1.0 + portfolio_returns)
        
        # Calculate metrics
        metrics = self._calculate_metrics(portfolio_returns, equity_curve, "static")
        
        return {
            "returns": portfolio_returns,
            "equity_curve": equity_curve,
            "dates": self.dates,
            "weights": {"pb07": w_pb07, "bb01": w_bb01},
            "metrics": metrics
        }
    
    def construct_dynamic_portfolio(self, weights_df):
        """
        Construct portfolio with time-varying weights.
        
        Args:
            weights_df: DataFrame with columns [date, w_pb07, w_bb01]
                        Weights apply to the date specified
        
        Returns:
            dict with returns, equity curve, metrics
        """
        weights_df = weights_df.copy()
        weights_df["date"] = pd.to_datetime(weights_df["date"])
        
        # Map weights to dates
        portfolio_returns = []
        for i, date in enumerate(self.dates):
            # Find weight for this date
            weight_row = weights_df[weights_df["date"] <= date]
            if len(weight_row) == 0:
                raise ValueError(f"No weight available for date {date}")
            
            w_pb07 = weight_row.iloc[-1]["w_pb07"]
            w_bb01 = weight_row.iloc[-1]["w_bb01"]
            
            assert abs(w_pb07 + w_bb01 - 1.0) < 1e-10, f"Weights don't sum to 1 at {date}"
            
            daily_ret = w_pb07 * self.pb07_returns[i] + w_bb01 * self.bb01_returns[i]
            portfolio_returns.append(daily_ret)
        
        portfolio_returns = np.array(portfolio_returns)
        equity_curve = np.cumprod(1.0 + portfolio_returns)
        
        metrics = self._calculate_metrics(portfolio_returns, equity_curve, "dynamic")
        
        return {
            "returns": portfolio_returns,
            "equity_curve": equity_curve,
            "dates": self.dates,
            "weights_df": weights_df,
            "metrics": metrics
        }
    
    def _calculate_metrics(self, returns, equity_curve, portfolio_type):
        """Calculate comprehensive portfolio metrics."""
        n_obs = len(returns)
        
        # Annual observations (252 trading days)
        annual_factor = 252
        
        # Returns
        total_return = equity_curve[-1] - 1.0
        cagr = (equity_curve[-1] ** (annual_factor / n_obs)) - 1.0
        
        # Volatility
        annual_vol = np.std(returns) * np.sqrt(annual_factor)
        
        # Sharpe (RF = 0%)
        excess_returns = returns
        sharpe = np.mean(excess_returns) / (np.std(excess_returns) + 1e-10) * np.sqrt(annual_factor)
        
        # Sortino (RF = 0%, downside > 0)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_vol = np.std(downside_returns) * np.sqrt(annual_factor)
            sortino = np.mean(excess_returns) / (downside_vol + 1e-10) * np.sqrt(annual_factor)
        else:
            sortino = np.nan
        
        # Maximum drawdown
        cumulative = np.cumprod(1.0 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = np.min(drawdown)
        
        # Calmar
        calmar = cagr / (abs(max_dd) + 1e-10)
        
        return {
            "total_return": total_return,
            "cagr": cagr,
            "annual_vol": annual_vol,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "calmar": calmar,
            "n_obs": n_obs,
            "portfolio_type": portfolio_type
        }
    
    def calculate_risk_parity(self, train_returns_bb01, train_returns_pb07):
        """
        Calculate risk-parity weights from training data.
        
        Equal risk contribution: w_i * sigma_i = constant for all i
        
        Args:
            train_returns_bb01: Training BB01 returns
            train_returns_pb07: Training PB07 returns
        
        Returns:
            (w_pb07, w_bb01)
        """
        sigma_bb01 = np.std(train_returns_bb01)
        sigma_pb07 = np.std(train_returns_pb07)
        
        # w = (1/sigma) / sum(1/sigma)
        inv_vol = np.array([1.0 / sigma_pb07, 1.0 / sigma_bb01])
        weights = inv_vol / inv_vol.sum()
        
        return weights[0], weights[1]  # w_pb07, w_bb01
    
    def get_yearly_returns(self, returns):
        """Calculate returns by year."""
        df = pd.DataFrame({
            "date": self.dates,
            "return": returns
        })
        df["year"] = df["date"].dt.year
        
        yearly = df.groupby("year")["return"].apply(
            lambda x: np.prod(1.0 + x.values) - 1.0
        )
        
        return yearly.to_dict()
    
    def get_turnover(self, weights_df):
        """Calculate average turnover from weight changes."""
        weights_df = weights_df.copy()
        weights_df = weights_df.sort_values("date")
        
        weight_changes = np.abs(weights_df[["w_pb07", "w_bb01"]].diff()).sum(axis=1)
        avg_turnover = weight_changes.mean()
        
        return avg_turnover
