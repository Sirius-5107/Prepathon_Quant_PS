"""
Alpha Research Module

Provides AlphaResearch class for discovering and evaluating alpha signals.
"""

import pandas as pd
import numpy as np
from scipy import stats


class AlphaResearch:
    """Discover and evaluate alpha signals from raw data."""
    
    def __init__(self, signal_data, price_data, forward_returns):
        """
        Initialize alpha researcher.
        
        Args:
            signal_data: Dict of signal names -> signal Series
            price_data: OHLC price data
            forward_returns: Forward returns for evaluation
        """
        self.signal_data = signal_data
        self.price_data = price_data
        self.forward_returns = forward_returns
        self.candidates = {}
    
    def evaluate_signal(self, signal_name, signal, horizon=20):
        """
        Evaluate a single signal for alpha.
        
        Args:
            signal_name: Name of the signal
            signal: Binary signal Series
            horizon: Forward return horizon
            
        Returns:
            dict with evaluation metrics
        """
        # Get forward returns for active days
        active_returns = self.forward_returns[signal == 1]
        inactive_returns = self.forward_returns[signal == 0]
        
        # Statistics
        active_mean = active_returns.mean()
        inactive_mean = inactive_returns.mean()
        
        # Welch t-test
        if len(active_returns) > 1 and len(inactive_returns) > 1:
            t_stat, p_value = stats.ttest_ind(active_returns, inactive_returns, equal_var=False)
        else:
            t_stat, p_value = np.nan, 1.0
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((active_returns.std() ** 2 + inactive_returns.std() ** 2) / 2)
        cohens_d = (active_mean - inactive_mean) / pooled_std if pooled_std > 0 else 0
        
        evaluation = {
            'signal_name': signal_name,
            'active_count': len(active_returns),
            'inactive_count': len(inactive_returns),
            'active_mean_return': active_mean * 100,
            'inactive_mean_return': inactive_mean * 100,
            'mean_spread': (active_mean - inactive_mean) * 100,
            't_statistic': t_stat,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'win_rate_active': (active_returns > 0).sum() / len(active_returns) * 100 if len(active_returns) > 0 else 0,
            'median_return_active': active_returns.median() * 100 if len(active_returns) > 0 else 0
        }
        
        self.candidates[signal_name] = evaluation
        
        return evaluation
    
    def rank_candidates(self, metric='p_value'):
        """
        Rank candidate signals by performance metric.
        
        Args:
            metric: Metric to rank by (default 'p_value')
            
        Returns:
            DataFrame of ranked candidates
        """
        df = pd.DataFrame(self.candidates.values())
        
        if metric == 'p_value':
            df = df.sort_values('p_value')
        elif metric == 'mean_spread':
            df = df.sort_values('mean_spread', ascending=False)
        elif metric == 'cohens_d':
            df = df.sort_values('cohens_d', ascending=False)
        
        return df
    
    def candidates_passing_threshold(self, p_threshold=0.05, min_trades=10):
        """
        Get candidates passing statistical threshold.
        
        Args:
            p_threshold: Maximum p-value threshold
            min_trades: Minimum number of active trades
            
        Returns:
            List of passing candidate names
        """
        passing = []
        
        for name, metrics in self.candidates.items():
            if (metrics['p_value'] < p_threshold and 
                metrics['active_count'] >= min_trades):
                passing.append(name)
        
        return passing
    
    def signal_correlation_matrix(self, signal_names=None):
        """
        Compute correlation matrix of signals.
        
        Args:
            signal_names: List of signal names to include (default all)
            
        Returns:
            DataFrame correlation matrix
        """
        if signal_names is None:
            signal_names = list(self.signal_data.keys())
        
        signals_subset = {name: self.signal_data[name] for name in signal_names 
                         if name in self.signal_data}
        
        df = pd.DataFrame(signals_subset)
        return df.corr()
    
    def forward_return_analysis(self, signal_name, horizons=[5, 10, 20, 40]):
        """
        Analyze signal returns across different horizons.
        
        Args:
            signal_name: Name of signal
            horizons: List of horizon lengths to test
            
        Returns:
            DataFrame with returns at each horizon
        """
        if signal_name not in self.signal_data:
            return None
        
        signal = self.signal_data[signal_name]
        active_returns = self.forward_returns[signal == 1]
        
        results = []
        for horizon in horizons:
            mean_ret = active_returns.mean() * 100
            median_ret = active_returns.median() * 100
            win_rate = (active_returns > 0).sum() / len(active_returns) * 100
            
            results.append({
                'horizon': horizon,
                'mean_return': mean_ret,
                'median_return': median_ret,
                'win_rate': win_rate,
                'count': len(active_returns)
            })
        
        return pd.DataFrame(results)
    
    def research_summary(self):
        """
        Generate research summary across all candidates.
        
        Returns:
            dict with summary statistics
        """
        if not self.candidates:
            return {}
        
        df = pd.DataFrame(self.candidates.values())
        
        return {
            'total_signals_tested': len(self.candidates),
            'signals_with_positive_mean': (df['mean_spread'] > 0).sum(),
            'signals_with_p_value_lt_0_05': (df['p_value'] < 0.05).sum(),
            'signals_with_p_value_lt_0_10': (df['p_value'] < 0.10).sum(),
            'best_signal_by_mean': df.loc[df['mean_spread'].idxmax(), 'signal_name'],
            'best_signal_by_pvalue': df.loc[df['p_value'].idxmin(), 'signal_name'],
            'average_p_value': df['p_value'].mean(),
            'median_mean_spread': df['mean_spread'].median(),
            'max_mean_spread': df['mean_spread'].max(),
            'min_mean_spread': df['mean_spread'].min()
        }
