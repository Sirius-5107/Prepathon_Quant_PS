"""
Statistical Testing Module

Provides StatisticalTester class for hypothesis testing on strategy returns.
"""

import pandas as pd
import numpy as np
from scipy import stats


class StatisticalTester:
    """Test statistical significance of strategy returns."""
    
    def __init__(self, return_series, signal_series, horizon=20, rf_rate=0.0):
        """
        Initialize statistical tester.
        
        Args:
            return_series: Forward returns for each observation
            signal_series: Binary signal (0 or 1)
            horizon: Forward return horizon (days)
            rf_rate: Risk-free rate for Sharpe calculation
        """
        self.return_series = return_series
        self.signal_series = signal_series
        self.horizon = horizon
        self.rf_rate = rf_rate
    
    def welch_ttest(self, use_hac=True):
        """
        Welch t-test comparing signal-on vs signal-off returns.
        
        Args:
            use_hac: Apply HAC standard error adjustment
            
        Returns:
            dict with t-statistic, p-value, and effect size
        """
        signal_on_returns = self.return_series[self.signal_series == 1]
        signal_off_returns = self.return_series[self.signal_series == 0]
        
        # Welch's t-test (unequal variance)
        t_stat, p_value = stats.ttest_ind(signal_on_returns, signal_off_returns, equal_var=False)
        
        mean_diff = signal_on_returns.mean() - signal_off_returns.mean()
        
        return {
            'statistic': t_stat,
            'p_value': p_value,
            'mean_diff': mean_diff,
            'n_signal_on': len(signal_on_returns),
            'n_signal_off': len(signal_off_returns),
            'mean_signal_on': signal_on_returns.mean(),
            'mean_signal_off': signal_off_returns.mean()
        }
    
    def bootstrap_ci(self, n_bootstraps=1000, ci=95):
        """
        Compute bootstrap confidence interval for mean return.
        
        Args:
            n_bootstraps: Number of bootstrap resamples
            ci: Confidence level (default 95%)
            
        Returns:
            dict with CI bounds and mean
        """
        signal_on_returns = self.return_series[self.signal_series == 1]
        
        bootstrap_means = []
        for _ in range(n_bootstraps):
            resample = np.random.choice(signal_on_returns, size=len(signal_on_returns), replace=True)
            bootstrap_means.append(resample.mean())
        
        bootstrap_means = np.array(bootstrap_means)
        
        alpha = (100 - ci) / 2
        lower = np.percentile(bootstrap_means, alpha)
        upper = np.percentile(bootstrap_means, 100 - alpha)
        
        return {
            'mean': signal_on_returns.mean(),
            'lower_ci': lower,
            'upper_ci': upper,
            'ci_level': ci
        }
    
    def sharpe_ratio(self, daily_returns):
        """
        Compute Sharpe ratio from daily returns.
        
        Args:
            daily_returns: Series of daily returns
            
        Returns:
            Annualized Sharpe ratio
        """
        # Annualize daily statistics
        annual_return = (1 + daily_returns.mean()) ** 252 - 1
        annual_vol = daily_returns.std() * np.sqrt(252)
        
        sharpe = (annual_return - self.rf_rate) / annual_vol if annual_vol > 0 else 0
        
        return sharpe
    
    def fdr_correction(self, p_values, alpha=0.05):
        """
        Apply False Discovery Rate correction (Benjamini-Hochberg).
        
        Args:
            p_values: Array of p-values from multiple tests
            alpha: Target FDR level
            
        Returns:
            Boolean array indicating which tests pass FDR correction
        """
        p_values = np.array(p_values)
        n = len(p_values)
        
        # Sort p-values and get indices
        sorted_idx = np.argsort(p_values)
        sorted_p = p_values[sorted_idx]
        
        # BH critical value
        threshold_idx = -1
        for i in range(n - 1, -1, -1):
            if sorted_p[i] <= (i + 1) / n * alpha:
                threshold_idx = i
                break
        
        # Mark tests that pass
        pass_fdr = np.zeros(n, dtype=bool)
        if threshold_idx >= 0:
            pass_fdr[sorted_idx[:threshold_idx + 1]] = True
        
        return pass_fdr
