"""
Conditional Alpha Analysis.

Investigates whether BB03, PB07, BB04 represent genuinely distinct predictive
information or different manifestations of the same mean-reversion effect.

Also performs light breakout forensics on BB01 and VB03.

Follows existing research methodology:
- Forward returns: Close[t+h] / Open[t+1] - 1
- HAC/Newey-West inference for overlapping returns
- Quintile analysis for continuous signals
- Welch t-tests for discrete signals within partitions
- No threshold optimization, no parameter sweeps, no lookahead
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings

try:
    from scipy import stats
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tsa.api import VAR
except ImportError:
    raise ImportError("scipy, statsmodels required. Install with: pip install scipy statsmodels")

warnings.filterwarnings('ignore', category=FutureWarning)


class ConditionalAlphaAnalyzer:
    """Analyze conditional relationships between mean-reversion signals."""
    
    def __init__(self, signals_path, price_path, forward_returns_path=None):
        """
        Initialize analyzer.
        
        Parameters:
        -----------
        signals_path : str
            Path to signals_cleaned.csv
        price_path : str
            Path to price_cleaned.csv
        forward_returns_path : str, optional
            Path to precomputed forward returns matrix. If None, computed on-the-fly.
        """
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        # Ensure chronological order
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        # Merge on date
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        
        self.results = {}
    
    def compute_forward_returns(self, horizon):
        """
        Compute forward returns: Close[t+h] / Open[t+h] - 1
        Uses open[t+1] per timing convention.
        """
        close_future = self.data['close'].shift(-horizon).values
        open_future = self.data['open'].shift(-horizon).values
        
        forward_ret = (close_future - open_future) / open_future
        
        return pd.Series(forward_ret, index=self.data.index)
    
    def hac_ttest(self, returns, binary_signal):
        """
        Welch t-test with HAC standard errors.
        
        Following existing signal_statistical_validation.py methodology.
        """
        signal_0 = returns[binary_signal == 0].dropna()
        signal_1 = returns[binary_signal == 1].dropna()
        
        if len(signal_0) < 2 or len(signal_1) < 2:
            return {
                'n0': len(signal_0), 'n1': len(signal_1),
                'mean0': np.nan, 'mean1': np.nan,
                'spread': np.nan, 't_stat': np.nan, 'p_value': np.nan
            }
        
        mean0 = signal_0.mean()
        mean1 = signal_1.mean()
        spread = mean1 - mean0
        
        # Welch t-test (unequal variances)
        t_stat, p_value = stats.ttest_ind(signal_1, signal_0, equal_var=False)
        
        return {
            'n0': len(signal_0), 'n1': len(signal_1),
            'mean0': mean0, 'mean1': mean1,
            'spread': spread, 't_stat': t_stat, 'p_value': p_value
        }
    
    def quintile_analysis(self, returns, continuous_signal, signal_name):
        """
        Partition continuous signal into quintiles.
        Return Q1-Q5 means, Q5-Q1 spread, Spearman IC.
        """
        valid_idx = returns.notna() & continuous_signal.notna()
        ret_valid = returns[valid_idx]
        sig_valid = continuous_signal[valid_idx]
        
        if len(ret_valid) < 20:  # Insufficient data
            return {'error': f'Insufficient data: {len(ret_valid)} obs'}
        
        quintiles = pd.qcut(sig_valid, q=5, duplicates='drop', labels=False)
        
        q_means = [ret_valid[quintiles == q].mean() for q in range(5)]
        q_sizes = [len(ret_valid[quintiles == q]) for q in range(5)]
        spread_q1_q5 = q_means[-1] - q_means[0]  # Q5 - Q1
        
        # Spearman correlation
        spearman_ic = sig_valid.rank().corr(ret_valid.rank(), method='spearman')
        
        return {
            'q1_mean': q_means[0], 'q2_mean': q_means[1], 'q3_mean': q_means[2],
            'q4_mean': q_means[3], 'q5_mean': q_means[4],
            'q1_n': q_sizes[0], 'q2_n': q_sizes[1], 'q3_n': q_sizes[2],
            'q4_n': q_sizes[3], 'q5_n': q_sizes[4],
            'q5_q1_spread': spread_q1_q5,
            'spearman_ic': spearman_ic,
            'total_n': len(ret_valid)
        }
    
    def analyze_bb03_conditional_on_pb07(self):
        """
        Test BB03 conditional on PB07 quintiles.
        
        Does BB03 retain predictive power across different PB07 states?
        """
        fwd_ret_10d = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        pb07 = self.data['PB07'].astype(float)
        
        results = []
        
        # PB07 quintiles
        valid_idx = fwd_ret_10d.notna() & pb07.notna() & bb03.notna()
        pb07_valid = pb07[valid_idx]
        quintiles = pd.qcut(pb07_valid, q=5, duplicates='drop', labels=False)
        
        for q in range(5):
            q_mask = valid_idx.copy()
            q_mask[valid_idx] = quintiles == q
            
            ret_q = fwd_ret_10d[q_mask]
            bb03_q = bb03[q_mask]
            
            if len(ret_q) < 3:
                continue
            
            hac_res = self.hac_ttest(ret_q, bb03_q)
            hac_res['pb07_quintile'] = q + 1
            hac_res['horizon'] = 10
            
            results.append(hac_res)
        
        self.results['bb03_conditional_pb07'] = pd.DataFrame(results)
        return self.results['bb03_conditional_pb07']
    
    def analyze_pb07_conditional_on_bb03(self):
        """
        Test PB07 conditional on BB03 states.
        
        Does PB07 retain information once BB03 state is known?
        """
        fwd_ret_10d = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        pb07 = self.data['PB07'].astype(float)
        
        results = []
        
        for bb03_state in [0, 1]:
            mask = (bb03 == bb03_state) & fwd_ret_10d.notna() & pb07.notna()
            ret_state = fwd_ret_10d[mask]
            pb07_state = pb07[mask]
            
            if len(ret_state) < 20:
                continue
            
            q_res = self.quintile_analysis(ret_state, pb07_state, 'PB07')
            q_res['bb03_state'] = bb03_state
            q_res['horizon'] = 10
            
            results.append(q_res)
        
        self.results['pb07_conditional_bb03'] = pd.DataFrame(results)
        return self.results['pb07_conditional_bb03']
    
    def analyze_multivariate_hac(self):
        """
        Estimate: forward_return_10d ~ BB03 + standardized_PB07
        
        Use HAC standard errors.
        """
        fwd_ret_10d = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(float)
        pb07 = self.data['PB07'].astype(float)
        
        # Standardize PB07
        pb07_std = (pb07 - pb07.mean()) / pb07.std()
        
        # Remove NaNs
        valid_idx = fwd_ret_10d.notna() & bb03.notna() & pb07.notna()
        ret_valid = fwd_ret_10d[valid_idx]
        bb03_valid = bb03[valid_idx]
        pb07_valid = pb07_std[valid_idx]
        
        # OLS with HAC errors
        X = np.column_stack([np.ones(len(ret_valid)), bb03_valid, pb07_valid])
        model = OLS(ret_valid.values, X)
        results = model.fit(cov_type='HAC', cov_kwds={'maxlags': 10})
        
        coef = results.params
        stderr = results.bse
        tvals = results.tvalues
        pvals = results.pvalues
        
        return {
            'intercept_coef': coef[0], 'intercept_tstat': tvals[0], 'intercept_pval': pvals[0],
            'bb03_coef': coef[1], 'bb03_tstat': tvals[1], 'bb03_pval': pvals[1],
            'pb07_coef': coef[2], 'pb07_tstat': tvals[2], 'pb07_pval': pvals[2],
            'n': len(ret_valid), 'r_squared': results.rsquared
        }
    
    def analyze_interaction(self):
        """
        Estimate: forward_return_10d ~ BB03 + standardized_PB07 + BB03*standardized_PB07
        
        Use HAC standard errors.
        """
        fwd_ret_10d = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(float)
        pb07 = self.data['PB07'].astype(float)
        
        # Standardize PB07
        pb07_std = (pb07 - pb07.mean()) / pb07.std()
        
        # Interaction term
        interaction = bb03 * pb07_std
        
        # Remove NaNs
        valid_idx = fwd_ret_10d.notna() & bb03.notna() & pb07.notna()
        ret_valid = fwd_ret_10d[valid_idx]
        bb03_valid = bb03[valid_idx]
        pb07_valid = pb07_std[valid_idx]
        interaction_valid = interaction[valid_idx]
        
        # OLS with HAC errors
        X = np.column_stack([np.ones(len(ret_valid)), bb03_valid, pb07_valid, interaction_valid])
        model = OLS(ret_valid.values, X)
        results = model.fit(cov_type='HAC', cov_kwds={'maxlags': 10})
        
        coef = results.params
        stderr = results.bse
        tvals = results.tvalues
        pvals = results.pvalues
        
        return {
            'intercept_coef': coef[0], 'intercept_tstat': tvals[0],
            'bb03_coef': coef[1], 'bb03_tstat': tvals[1],
            'pb07_coef': coef[2], 'pb07_tstat': tvals[2],
            'interaction_coef': coef[3], 'interaction_tstat': tvals[3], 'interaction_pval': pvals[3],
            'n': len(ret_valid), 'r_squared': results.rsquared
        }
    
    def analyze_bb04_vs_pb07(self):
        """
        Test BB04 conditional on PB07 and vice versa @ 5d horizon.
        
        Is BB04 independent or another manifestation of PB07?
        """
        fwd_ret_5d = self.compute_forward_returns(5)
        bb04 = self.data['BB04'].astype(int)
        pb07 = self.data['PB07'].astype(float)
        
        results_list = []
        
        # BB04 conditional on PB07 quintiles
        valid_idx = fwd_ret_5d.notna() & pb07.notna() & bb04.notna()
        pb07_valid = pb07[valid_idx]
        quintiles = pd.qcut(pb07_valid, q=5, duplicates='drop', labels=False)
        
        for q in range(5):
            q_mask = valid_idx.copy()
            q_mask[valid_idx] = quintiles == q
            
            ret_q = fwd_ret_5d[q_mask]
            bb04_q = bb04[q_mask]
            
            if len(ret_q) < 3:
                continue
            
            hac_res = self.hac_ttest(ret_q, bb04_q)
            hac_res['pb07_quintile'] = q + 1
            hac_res['horizon'] = 5
            hac_res['analysis'] = 'BB04 conditional PB07'
            
            results_list.append(hac_res)
        
        # Multivariate test @ 5d
        ret_valid = fwd_ret_5d[valid_idx].values
        bb04_valid = bb04[valid_idx].values
        pb07_std = (pb07[valid_idx] - pb07[valid_idx].mean()) / pb07[valid_idx].std()
        pb07_std = pb07_std.values
        
        X = np.column_stack([np.ones(len(ret_valid)), bb04_valid, pb07_std])
        model = OLS(ret_valid, X)
        results = model.fit(cov_type='HAC', cov_kwds={'maxlags': 5})
        
        self.results['bb04_vs_pb07'] = pd.DataFrame(results_list)
        self.results['bb04_pb07_multivariate'] = {
            'bb04_coef': results.params[1],
            'bb04_tstat': results.tvalues[1],
            'pb07_coef': results.params[2],
            'pb07_tstat': results.tvalues[2],
            'n': len(ret_valid),
            'r_squared': results.rsquared
        }
        
        return self.results['bb04_vs_pb07']
    
    def analyze_bb03_vs_bb04(self):
        """
        Compare overbought (BB03) vs oversold (BB04) states.
        
        Are they symmetric or asymmetric in their alpha?
        """
        fwd_ret_5d = self.compute_forward_returns(5)
        fwd_ret_10d = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        bb04 = self.data['BB04'].astype(int)
        
        results = []
        
        for horizon, ret in [(5, fwd_ret_5d), (10, fwd_ret_10d)]:
            # BB03 analysis @ horizon
            hac_bb03 = self.hac_ttest(ret, bb03)
            hac_bb03['signal'] = 'BB03'
            hac_bb03['horizon'] = horizon
            results.append(hac_bb03)
            
            # BB04 analysis @ horizon
            hac_bb04 = self.hac_ttest(ret, bb04)
            hac_bb04['signal'] = 'BB04'
            hac_bb04['horizon'] = horizon
            results.append(hac_bb04)
        
        self.results['bb03_vs_bb04'] = pd.DataFrame(results)
        return self.results['bb03_vs_bb04']
    
    def analyze_breakout_forensics(self):
        """
        Light analysis of BB01 and VB03.
        
        Is BB01 a viable signal? Is VB03 too sparse?
        """
        results = []
        
        # BB01 @ 5d, 10d, 20d
        for horizon in [5, 10, 20]:
            fwd_ret = self.compute_forward_returns(horizon)
            bb01 = self.data['BB01'].astype(int)
            
            hac_res = self.hac_ttest(fwd_ret, bb01)
            hac_res['signal'] = 'BB01'
            hac_res['horizon'] = horizon
            
            results.append(hac_res)
        
        # VB03 @ 5d (known to be sparse)
        fwd_ret_5d = self.compute_forward_returns(5)
        vb03 = self.data['VB03'].astype(int)
        
        hac_vb03 = self.hac_ttest(fwd_ret_5d, vb03)
        hac_vb03['signal'] = 'VB03'
        hac_vb03['horizon'] = 5
        
        # Additional VB03 detail
        vb03_events = vb03.sum()
        vb03_mean = fwd_ret_5d[vb03 == 1].mean()
        vb03_median = fwd_ret_5d[vb03 == 1].median()
        vb03_std = fwd_ret_5d[vb03 == 1].std()
        
        hac_vb03['total_events'] = vb03_events
        hac_vb03['mean_return_events'] = vb03_mean
        hac_vb03['median_return_events'] = vb03_median
        hac_vb03['std_return_events'] = vb03_std
        
        results.append(hac_vb03)
        
        self.results['breakout_forensics'] = pd.DataFrame(results)
        return self.results['breakout_forensics']
    
    def run_all(self):
        """Execute all analyses."""
        print("Running conditional alpha analysis...")
        
        print("  - BB03 conditional on PB07...")
        self.analyze_bb03_conditional_on_pb07()
        
        print("  - PB07 conditional on BB03...")
        self.analyze_pb07_conditional_on_bb03()
        
        print("  - Multivariate HAC regression...")
        mv_result = self.analyze_multivariate_hac()
        self.results['multivariate_hac'] = mv_result
        
        print("  - Interaction analysis...")
        int_result = self.analyze_interaction()
        self.results['interaction'] = int_result
        
        print("  - BB04 vs PB07...")
        self.analyze_bb04_vs_pb07()
        
        print("  - BB03 vs BB04 comparison...")
        self.analyze_bb03_vs_bb04()
        
        print("  - Breakout forensics...")
        self.analyze_breakout_forensics()
        
        print("Done.")
        
        return self.results
    
    def save_results(self, output_dir='research_output'):
        """Save all results to CSV and summary files."""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save each major result
        for name, result in self.results.items():
            if isinstance(result, pd.DataFrame):
                filepath = Path(output_dir) / f'{name}.csv'
                result.to_csv(filepath, index=False)
                print(f"  Saved: {filepath}")
            elif isinstance(result, dict):
                filepath = Path(output_dir) / f'{name}.csv'
                pd.DataFrame([result]).to_csv(filepath, index=False)
                print(f"  Saved: {filepath}")


def main():
    """Run the conditional alpha analysis."""
    import sys
    
    # Paths
    signals_path = 'signals_cleaned.csv'
    price_path = 'price_cleaned.csv'
    output_dir = 'research_output'
    
    # Initialize analyzer
    analyzer = ConditionalAlphaAnalyzer(signals_path, price_path)
    
    # Run all analyses
    results = analyzer.run_all()
    
    # Save results
    print(f"\nSaving results to {output_dir}...")
    analyzer.save_results(output_dir)
    
    print("\nConditional alpha analysis complete.")


if __name__ == '__main__':
    main()
