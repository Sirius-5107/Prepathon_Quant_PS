"""
Dynamic Portfolio Allocator

Walk-forward allocation with rolling risk-parity:
- Training: 2 years (504 trading days)
- Testing: 1 year (252 trading days)  
- Rebalance: Quarterly (every 63 days)
- Method: Risk-parity estimated from training window only
"""

import numpy as np
import pandas as pd
from datetime import datetime


class DynamicAllocator:
    """Walk-forward dynamic allocation."""
    
    def __init__(self, bb01_returns, pb07_returns, dates):
        """
        Initialize with strategy returns.
        
        Args:
            bb01_returns: Array of BB01 daily returns
            pb07_returns: Array of PB07 daily returns
            dates: Array of dates
        """
        self.bb01_returns = bb01_returns
        self.pb07_returns = pb07_returns
        self.dates = pd.to_datetime(dates)
        self.n_obs = len(self.dates)
    
    def run_walk_forward(self, train_years=2, test_years=1, rebalance_freq='quarterly'):
        """
        Execute walk-forward allocation.
        
        Args:
            train_years: Training window in years (default 2)
            test_years: Testing window in years (default 1)
            rebalance_freq: 'quarterly', 'monthly', or 'annual'
        
        Returns:
            DataFrame with weights and rebalance dates
        """
        trading_days_per_year = 252
        train_window = train_years * trading_days_per_year
        test_window = test_years * trading_days_per_year
        
        # Rebalance frequency (days)
        if rebalance_freq == 'quarterly':
            rebalance_days = 63
        elif rebalance_freq == 'monthly':
            rebalance_days = 21
        elif rebalance_freq == 'annual':
            rebalance_days = 252
        else:
            raise ValueError("rebalance_freq must be 'quarterly', 'monthly', or 'annual'")
        
        weights_list = []
        
        # Walk-forward windows
        windows = []
        for train_end_idx in range(train_window, self.n_obs - test_window + 1, test_window):
            train_start_idx = max(0, train_end_idx - train_window)
            test_end_idx = min(self.n_obs, train_end_idx + test_window)
            
            windows.append({
                'train_start': train_start_idx,
                'train_end': train_end_idx,
                'test_start': train_end_idx,
                'test_end': test_end_idx
            })
        
        # Process each window
        for window in windows:
            train_start = window['train_start']
            train_end = window['train_end']
            test_start = window['test_start']
            test_end = window['test_end']
            
            # Estimate weights from training data
            train_bb01 = self.bb01_returns[train_start:train_end]
            train_pb07 = self.pb07_returns[train_start:train_end]
            
            w_pb07, w_bb01 = self._calculate_risk_parity(train_bb01, train_pb07)
            
            # Apply weights throughout test period with rebalancing
            test_dates = self.dates[test_start:test_end]
            test_indices = np.arange(test_start, test_end)
            
            for rebal_idx in range(0, len(test_indices), rebalance_days):
                rebal_start = rebal_idx
                rebal_end = min(rebal_idx + rebalance_days, len(test_indices))
                
                for idx in range(rebal_start, rebal_end):
                    if idx < len(test_indices):
                        actual_idx = test_indices[idx]
                        weights_list.append({
                            'date': self.dates[actual_idx],
                            'w_pb07': w_pb07,
                            'w_bb01': w_bb01,
                            'window': len(weights_list) // len(test_indices) + 1,
                            'method': 'risk_parity_wfo'
                        })
        
        # Ensure coverage of full period
        weights_df = pd.DataFrame(weights_list)
        
        # Fill any gaps with forward-fill
        all_dates = pd.DataFrame({'date': self.dates})
        weights_df = all_dates.merge(
            weights_df,
            on='date',
            how='left'
        )
        weights_df['w_pb07'] = weights_df['w_pb07'].ffill().bfill()
        weights_df['w_bb01'] = weights_df['w_bb01'].ffill().bfill()
        
        return weights_df
    
    def _calculate_risk_parity(self, bb01_train, pb07_train):
        """
        Calculate risk-parity weights from training data.
        
        Args:
            bb01_train: Training window BB01 returns
            pb07_train: Training window PB07 returns
        
        Returns:
            (w_pb07, w_bb01)
        """
        sigma_bb01 = np.std(bb01_train)
        sigma_pb07 = np.std(pb07_train)
        
        # Avoid division by zero
        if sigma_bb01 == 0 or sigma_pb07 == 0:
            return 0.5, 0.5  # Fallback to equal-weight
        
        # w = (1/sigma) / sum(1/sigma)
        inv_vol = np.array([1.0 / sigma_pb07, 1.0 / sigma_bb01])
        weights = inv_vol / inv_vol.sum()
        
        return weights[0], weights[1]


def run_dynamic_allocation_study(portfolio_engine):
    """
    Run walk-forward dynamic allocation study.
    
    Args:
        portfolio_engine: PortfolioEngine instance
    
    Returns:
        dict with dynamic allocation results
    """
    allocator = DynamicAllocator(
        portfolio_engine.bb01_returns,
        portfolio_engine.pb07_returns,
        portfolio_engine.dates
    )
    
    # Run walk-forward
    weights_wfo = allocator.run_walk_forward(
        train_years=2,
        test_years=1,
        rebalance_freq='quarterly'
    )
    
    # Construct dynamic portfolio
    portfolio_dynamic = portfolio_engine.construct_dynamic_portfolio(weights_wfo)
    
    return {
        "weights": weights_wfo,
        "portfolio": portfolio_dynamic,
        "turnover": portfolio_engine.get_turnover(weights_wfo)
    }
