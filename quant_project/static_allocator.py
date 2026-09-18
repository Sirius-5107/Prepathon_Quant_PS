"""
Static Portfolio Allocators

Implements fixed-weight portfolio construction:
- Equal-weight (50/50)
- Task 2 baseline (70/30)
- Grid search (10/90 to 90/10)
- Risk-parity (equal volatility contribution)
- Mean-variance optimization (maximize Sharpe)
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


class StaticAllocator:
    """Static portfolio allocators."""
    
    @staticmethod
    def equal_weight():
        """Equal-weight allocation: 50/50."""
        return {"pb07": 0.50, "bb01": 0.50}
    
    @staticmethod
    def baseline():
        """Task 2 baseline allocation: 70/30."""
        return {"pb07": 0.70, "bb01": 0.30}
    
    @staticmethod
    def risk_parity(bb01_returns, pb07_returns):
        """
        Risk-parity allocation: equal marginal risk contribution.
        
        Args:
            bb01_returns: Full sample BB01 returns
            pb07_returns: Full sample PB07 returns
        
        Returns:
            dict with weights
        """
        sigma_bb01 = np.std(bb01_returns)
        sigma_pb07 = np.std(pb07_returns)
        
        # w = (1/sigma) / sum(1/sigma)
        inv_vol = np.array([1.0 / sigma_pb07, 1.0 / sigma_bb01])
        weights = inv_vol / inv_vol.sum()
        
        return {"pb07": weights[0], "bb01": weights[1]}
    
    @staticmethod
    def optimize_sharpe(bb01_returns, pb07_returns):
        """
        Maximize Sharpe ratio via constrained optimization.
        
        Args:
            bb01_returns: Full sample BB01 returns
            pb07_returns: Full sample PB07 returns
        
        Returns:
            dict with optimized weights
        """
        # Expected return and volatility
        mu_bb01 = np.mean(bb01_returns)
        mu_pb07 = np.mean(pb07_returns)
        sigma_bb01 = np.std(bb01_returns)
        sigma_pb07 = np.std(pb07_returns)
        
        # Correlation matrix
        cov_matrix = np.cov(bb01_returns, pb07_returns)
        
        # Objective: minimize negative Sharpe (i.e., maximize Sharpe)
        def negative_sharpe(w):
            # w = [w_pb07, w_bb01]
            portfolio_return = w[0] * mu_pb07 + w[1] * mu_bb01
            portfolio_var = (
                w[0]**2 * cov_matrix[1, 1] +
                w[1]**2 * cov_matrix[0, 0] +
                2 * w[0] * w[1] * cov_matrix[0, 1]
            )
            portfolio_vol = np.sqrt(portfolio_var)
            
            sharpe = portfolio_return / (portfolio_vol + 1e-10)
            return -sharpe
        
        # Constraints: sum to 1, non-negative
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
        bounds = [(0, 1), (0, 1)]
        
        # Initial guess
        x0 = np.array([0.5, 0.5])
        
        # Optimize
        result = minimize(
            negative_sharpe,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints
        )
        
        w_opt = result.x
        return {"pb07": w_opt[0], "bb01": w_opt[1]}
    
    @staticmethod
    def grid_search(bb01_returns, pb07_returns, step=0.1):
        """
        Grid search: evaluate all allocations in 10% increments.
        
        Args:
            bb01_returns: Full sample BB01 returns
            pb07_returns: Full sample PB07 returns
            step: Allocation step (default 0.1 for 10% increments)
        
        Returns:
            list of dicts with (weights, metrics)
        """
        results = []
        
        allocations = np.arange(0, 1 + step, step)
        
        for w_pb07 in allocations:
            w_bb01 = 1.0 - w_pb07
            
            # Portfolio return and metrics
            portfolio_returns = w_pb07 * pb07_returns + w_bb01 * bb01_returns
            total_return = np.prod(1.0 + portfolio_returns) - 1.0
            annual_vol = np.std(portfolio_returns) * np.sqrt(252)
            annual_return = np.mean(portfolio_returns) * 252
            sharpe = annual_return / (annual_vol + 1e-10)
            
            # Max drawdown
            equity = np.cumprod(1.0 + portfolio_returns)
            running_max = np.maximum.accumulate(equity)
            max_dd = np.min((equity - running_max) / running_max)
            
            results.append({
                "w_pb07": w_pb07,
                "w_bb01": w_bb01,
                "total_return": total_return,
                "annual_vol": annual_vol,
                "sharpe": sharpe,
                "max_drawdown": max_dd
            })
        
        return results


def run_static_allocation_study(portfolio_engine):
    """
    Run comprehensive static allocation study.
    
    Args:
        portfolio_engine: PortfolioEngine instance
    
    Returns:
        dict with results from all allocators
    """
    allocator = StaticAllocator()
    
    # Get full-sample returns
    bb01_returns = portfolio_engine.bb01_returns
    pb07_returns = portfolio_engine.pb07_returns
    
    results = {}
    
    # 1. Equal-weight
    w_eq = allocator.equal_weight()
    portfolio_eq = portfolio_engine.construct_portfolio(w_eq["pb07"], w_eq["bb01"])
    results["equal_weight"] = {
        "weights": w_eq,
        "portfolio": portfolio_eq
    }
    
    # 2. Baseline (Task 2)
    w_base = allocator.baseline()
    portfolio_base = portfolio_engine.construct_portfolio(w_base["pb07"], w_base["bb01"])
    results["baseline"] = {
        "weights": w_base,
        "portfolio": portfolio_base
    }
    
    # 3. Risk-parity
    w_rp = allocator.risk_parity(bb01_returns, pb07_returns)
    portfolio_rp = portfolio_engine.construct_portfolio(w_rp["pb07"], w_rp["bb01"])
    results["risk_parity"] = {
        "weights": w_rp,
        "portfolio": portfolio_rp
    }
    
    # 4. Optimize Sharpe
    w_opt = allocator.optimize_sharpe(bb01_returns, pb07_returns)
    portfolio_opt = portfolio_engine.construct_portfolio(w_opt["pb07"], w_opt["bb01"])
    results["optimize_sharpe"] = {
        "weights": w_opt,
        "portfolio": portfolio_opt
    }
    
    # 5. Grid search
    grid_results = allocator.grid_search(bb01_returns, pb07_returns, step=0.10)
    results["grid_search"] = grid_results
    
    return results
