"""
Orthogonality / Independence Analysis Module

Provides OrthogonalityAnalyzer class for testing independence of signals.
"""

import pandas as pd
import numpy as np
from scipy import stats


class OrthogonalityAnalyzer:
    """Analyze statistical independence and return-space orthogonality of signals."""
    
    def __init__(self, signal1, signal2, forward_returns):
        """
        Initialize orthogonality analyzer.
        
        Args:
            signal1: Binary signal 1 (Series)
            signal2: Binary signal 2 (Series)
            forward_returns: Forward returns (Series)
        """
        self.signal1 = signal1
        self.signal2 = signal2
        self.forward_returns = forward_returns
    
    def correlation_analysis(self):
        """
        Compute correlation between signals.
        
        Returns:
            dict with Pearson, Spearman, and Kendall correlations
        """
        pearson, pearson_p = stats.pearsonr(self.signal1, self.signal2)
        spearman, spearman_p = stats.spearmanr(self.signal1, self.signal2)
        kendall, kendall_p = stats.kendalltau(self.signal1, self.signal2)
        
        return {
            'pearson': pearson,
            'pearson_p': pearson_p,
            'spearman': spearman,
            'spearman_p': spearman_p,
            'kendall': kendall,
            'kendall_p': kendall_p
        }
    
    def joint_signal_returns(self):
        """
        Analyze forward returns for joint signal states.
        
        Returns:
            dict with statistics for each joint state
        """
        both_on = self.forward_returns[(self.signal1 == 1) & (self.signal2 == 1)]
        sig1_only = self.forward_returns[(self.signal1 == 1) & (self.signal2 == 0)]
        sig2_only = self.forward_returns[(self.signal1 == 0) & (self.signal2 == 1)]
        neither = self.forward_returns[(self.signal1 == 0) & (self.signal2 == 0)]
        
        def stats_for_group(group, label):
            if len(group) == 0:
                return None
            return {
                'label': label,
                'count': len(group),
                'mean_return': group.mean() * 100,
                'median_return': group.median() * 100,
                'std_return': group.std() * 100,
                'win_rate': (group > 0).sum() / len(group) * 100
            }
        
        results = {}
        if len(both_on) > 0:
            results['both_on'] = stats_for_group(both_on, 'Signal1+ & Signal2+')
        if len(sig1_only) > 0:
            results['sig1_only'] = stats_for_group(sig1_only, 'Signal1+ only')
        if len(sig2_only) > 0:
            results['sig2_only'] = stats_for_group(sig2_only, 'Signal2+ only')
        if len(neither) > 0:
            results['neither'] = stats_for_group(neither, 'Neither')
        
        return results
    
    def agreement_analysis(self):
        """
        Analyze whether signal agreement improves forward returns.
        
        Returns:
            dict comparing unconditional vs agreement-conditioned returns
        """
        sig1_unconditional = self.forward_returns[self.signal1 == 1]
        sig1_when_agree = self.forward_returns[(self.signal1 == 1) & (self.signal2 == 1)]
        
        sig2_unconditional = self.forward_returns[self.signal2 == 1]
        sig2_when_agree = self.forward_returns[(self.signal1 == 1) & (self.signal2 == 1)]
        
        results = {}
        
        if len(sig1_unconditional) > 0:
            results['sig1_unconditional'] = {
                'mean_return': sig1_unconditional.mean() * 100,
                'count': len(sig1_unconditional)
            }
        
        if len(sig1_when_agree) > 0:
            results['sig1_when_agree'] = {
                'mean_return': sig1_when_agree.mean() * 100,
                'count': len(sig1_when_agree)
            }
        
        if len(sig2_unconditional) > 0:
            results['sig2_unconditional'] = {
                'mean_return': sig2_unconditional.mean() * 100,
                'count': len(sig2_unconditional)
            }
        
        if len(sig2_when_agree) > 0:
            results['sig2_when_agree'] = {
                'mean_return': sig2_when_agree.mean() * 100,
                'count': len(sig2_when_agree)
            }
        
        return results
    
    def disagreement_analysis(self):
        """
        Analyze whether signal disagreement contains useful information.
        
        Returns:
            dict with disagreement statistics
        """
        sig1_pos_sig2_neg = self.forward_returns[(self.signal1 == 1) & (self.signal2 == 0)]
        sig1_neg_sig2_pos = self.forward_returns[(self.signal1 == 0) & (self.signal2 == 1)]
        
        results = {}
        
        if len(sig1_pos_sig2_neg) > 0:
            results['sig1_pos_sig2_neg'] = {
                'mean_return': sig1_pos_sig2_neg.mean() * 100,
                'win_rate': (sig1_pos_sig2_neg > 0).sum() / len(sig1_pos_sig2_neg) * 100,
                'count': len(sig1_pos_sig2_neg)
            }
        
        if len(sig1_neg_sig2_pos) > 0:
            results['sig1_neg_sig2_pos'] = {
                'mean_return': sig1_neg_sig2_pos.mean() * 100,
                'win_rate': (sig1_neg_sig2_pos > 0).sum() / len(sig1_neg_sig2_pos) * 100,
                'count': len(sig1_neg_sig2_pos)
            }
        
        return results
    
    def portfolio_analysis(self, weights):
        """
        Analyze portfolio combining the two signals with given weights.
        
        Args:
            weights: (w1, w2) weights for signal1 and signal2
            
        Returns:
            dict with portfolio statistics
        """
        w1, w2 = weights
        
        # For sparse event-based strategies, approximation:
        # Portfolio return is weighted average of individual returns
        signal1_ret = self.forward_returns[self.signal1 == 1].mean()
        signal2_ret = self.forward_returns[self.signal2 == 1].mean()
        
        portfolio_mean_return = w1 * signal1_ret + w2 * signal2_ret
        
        # Correlation-based volatility estimate
        r_corr = self.correlation_analysis()['pearson']
        signal1_vol = self.forward_returns[self.signal1 == 1].std()
        signal2_vol = self.forward_returns[self.signal2 == 1].std()
        
        portfolio_vol = np.sqrt((w1 * signal1_vol) ** 2 + 
                               (w2 * signal2_vol) ** 2 + 
                               2 * w1 * w2 * signal1_vol * signal2_vol * r_corr)
        
        return {
            'weights': weights,
            'mean_return': portfolio_mean_return * 100,
            'estimated_volatility': portfolio_vol * 100,
            'estimated_sharpe': (portfolio_mean_return / portfolio_vol * 100) if portfolio_vol > 0 else 0
        }
    
    def independence_summary(self):
        """
        Provide summary independence assessment.
        
        Returns:
            dict with independence judgement
        """
        corr = self.correlation_analysis()['pearson']
        joint = self.joint_signal_returns()
        both_active = len(joint.get('both_on', {}) or {}) if 'both_on' in joint else 0
        
        return {
            'pearson_correlation': corr,
            'interpretation': 'Nearly independent' if abs(corr) < 0.1 else 'Moderately correlated' if abs(corr) < 0.3 else 'Highly correlated',
            'joint_activation_pct': (both_active / len(self.signal1) * 100) if len(self.signal1) > 0 else 0,
            'signals_complement_each_other': both_active < len(self.signal1) * 0.05
        }
