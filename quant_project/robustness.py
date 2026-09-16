"""
Robustness Testing Module

Provides RobustnessTester class for stress-testing strategy performance.
"""

import pandas as pd
import numpy as np


class RobustnessTester:
    """Test robustness of strategy across time periods, subsets, and perturbations."""
    
    def __init__(self, daily_returns, dates):
        """
        Initialize robustness tester.
        
        Args:
            daily_returns: Series of daily returns
            dates: Index of dates corresponding to returns
        """
        self.daily_returns = daily_returns
        self.dates = dates
    
    def yearly_breakdown(self):
        """
        Compute returns by year.
        
        Returns:
            dict with yearly returns
        """
        df = pd.DataFrame({'returns': self.daily_returns, 'date': self.dates})
        df['year'] = df['date'].dt.year
        
        yearly = {}
        for year in sorted(df['year'].unique()):
            year_rets = df[df['year'] == year]['returns'].values
            if len(year_rets) > 0:
                yearly[year] = (np.prod(1 + year_rets) - 1) * 100
        
        return yearly
    
    def rolling_window_returns(self, window=63):
        """
        Compute rolling window returns (e.g., quarterly).
        
        Args:
            window: Window size in days
            
        Returns:
            Series of rolling returns
        """
        returns_arr = self.daily_returns.values
        
        rolling_rets = []
        for i in range(len(returns_arr) - window + 1):
            window_return = (np.prod(1 + returns_arr[i:i + window]) - 1) * 100
            rolling_rets.append(window_return)
        
        return pd.Series(rolling_rets)
    
    def walk_forward_analysis(self, train_years=2, test_years=1):
        """
        Evaluate performance across train/test splits (expanding window).
        
        Args:
            train_years: Years for training
            test_years: Years for testing
            
        Returns:
            dict with train/test returns
        """
        df = pd.DataFrame({'returns': self.daily_returns, 'date': self.dates})
        df['year'] = df['date'].dt.year
        
        years = sorted(df['year'].unique())
        results = []
        
        for i in range(len(years) - (train_years + test_years) + 1):
            train_end_year = years[i + train_years - 1]
            test_start_year = years[i + train_years]
            test_end_year = years[i + train_years + test_years - 1]
            
            train_data = df[df['year'] <= train_end_year]['returns'].values
            test_data = df[(df['year'] >= test_start_year) & (df['year'] <= test_end_year)]['returns'].values
            
            train_ret = (np.prod(1 + train_data) - 1) * 100 if len(train_data) > 0 else 0
            test_ret = (np.prod(1 + test_data) - 1) * 100 if len(test_data) > 0 else 0
            
            results.append({
                'fold': len(results) + 1,
                'train_end_year': train_end_year,
                'test_period': f'{test_start_year}-{test_end_year}',
                'train_return': train_ret,
                'test_return': test_ret
            })
        
        return pd.DataFrame(results)
    
    def transaction_cost_sensitivity(self, base_costs, cost_multiples=[0.5, 1.0, 1.5, 2.0]):
        """
        Test sensitivity to transaction costs.
        
        Args:
            base_costs: Base transaction costs as % of capital
            cost_multiples: Multiples of base costs to test
            
        Returns:
            dict with returns under different cost scenarios
        """
        results = {}
        
        for multiple in cost_multiples:
            adjusted_costs = base_costs * multiple
            adjusted_return = ((1 + (self.daily_returns.sum() - adjusted_costs / 100)) ** 
                              (252 / len(self.daily_returns)) - 1) * 100
            results[f'{multiple}x'] = adjusted_return
        
        return results
    
    def subsample_analysis(self, subsample_pct=[50, 75, 90]):
        """
        Test robustness on random subsamples of the data.
        
        Args:
            subsample_pct: Percentages of data to sample
            
        Returns:
            dict with returns on different sample sizes
        """
        results = {}
        
        for pct in subsample_pct:
            sample_size = max(1, int(len(self.daily_returns) * pct / 100))
            
            # Take evenly-spaced subsample
            indices = np.linspace(0, len(self.daily_returns) - 1, sample_size, dtype=int)
            subsample_rets = self.daily_returns.iloc[indices].values
            
            subsample_return = (np.prod(1 + subsample_rets) - 1) * 100
            results[f'{pct}%'] = subsample_return
        
        return results
    
    def drawdown_analysis(self):
        """
        Compute maximum drawdown and drawdown duration statistics.
        
        Returns:
            dict with drawdown metrics
        """
        equity = np.cumprod(1 + self.daily_returns.values)
        running_max = np.maximum.accumulate(equity)
        drawdowns = (equity - running_max) / running_max
        
        max_dd = drawdowns.min()
        max_dd_duration = self._max_dd_duration(drawdowns)
        
        return {
            'max_drawdown': max_dd * 100,
            'max_dd_duration_days': max_dd_duration,
            'number_of_drawdowns': (drawdowns < 0).sum()
        }
    
    @staticmethod
    def _max_dd_duration(drawdowns):
        """Find duration of maximum drawdown."""
        dd_periods = drawdowns < 0
        changes = np.diff(np.concatenate(([False], dd_periods, [False])).astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        
        if len(starts) == 0:
            return 0
        
        durations = ends - starts
        return int(durations.max())
