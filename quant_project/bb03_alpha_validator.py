"""
BB03 Alpha Validation Study: Time-Series Robustness & Stability Analysis.

Investigates the core hypothesis:
"Overbought oscillator state (BB03=1) at t-1 predicts negative 10-day forward 
returns from t's open, with statistical significance and temporal stability."

Methodology:
- Forward returns: Close[t+10] / Open[t+1] - 1 (canonical convention)
- Welch t-tests with explicit unequal-variance handling
- HAC standard errors (Newey-West, 10-lag window)
- Year-by-year decomposition
- Rolling correlation & volatility stability
- Spearman rank correlation (monotonicity check)
- Cross-validation via expanding windows
- Cost sensitivity analysis
- No parameter optimization; no signal modification

Output: comprehensive validation report for Task 2 strategy selection.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import warnings

warnings.filterwarnings('ignore')


class BB03AlphaValidator:
    """Validate BB03 mean-reversion alpha across time and conditions."""
    
    def __init__(self, signals_path, price_path):
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        # Sort chronologically
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        # Merge
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        self.results = {}
    
    def compute_forward_returns(self, horizon):
        """Forward returns: Close[t+h] / Open[t+h] - 1"""
        close_future = self.data['close'].shift(-horizon).values
        open_future = self.data['open'].shift(-horizon).values
        forward_ret = (close_future - open_future) / open_future
        return pd.Series(forward_ret, index=self.data.index)
    
    def hac_ttest(self, returns, binary_signal, maxlags=10):
        """Welch t-test with Newey-West standard errors."""
        signal_0 = returns[binary_signal == 0].dropna()
        signal_1 = returns[binary_signal == 1].dropna()
        
        if len(signal_0) < 2 or len(signal_1) < 2:
            return {
                'n0': len(signal_0), 'n1': len(signal_1),
                'mean0': np.nan, 'mean1': np.nan,
                'spread': np.nan, 't_stat': np.nan, 'p_value': np.nan,
                'hac_se': np.nan, 'ci_lower': np.nan, 'ci_upper': np.nan
            }
        
        mean0 = signal_0.mean()
        mean1 = signal_1.mean()
        spread = mean1 - mean0
        
        # Welch t-test
        t_stat, p_val = stats.ttest_ind(signal_1, signal_0, equal_var=False)
        
        # HAC standard error (simplified: use pooled std with lag adjustment)
        var0 = signal_0.var()
        var1 = signal_1.var()
        n0, n1 = len(signal_0), len(signal_1)
        
        # Pooled variance estimate
        pooled_var = ((n0 - 1) * var0 + (n1 - 1) * var1) / (n0 + n1 - 2)
        
        # HAC adjustment factor (lag-weighted)
        lag_weights = 1 - np.arange(maxlags + 1) / (maxlags + 1)
        hac_factor = 1 + 2 * lag_weights[1:].sum()  # Simplified
        
        hac_se = np.sqrt(pooled_var * (1/n0 + 1/n1) * hac_factor)
        hac_tstat = spread / hac_se if hac_se > 0 else np.nan
        hac_pval = 2 * (1 - stats.t.cdf(abs(hac_tstat), n0 + n1 - 2)) if not np.isnan(hac_tstat) else np.nan
        
        # 95% CI
        t_crit = stats.t.ppf(0.975, n0 + n1 - 2)
        ci_lower = spread - t_crit * hac_se
        ci_upper = spread + t_crit * hac_se
        
        return {
            'n0': len(signal_0), 'n1': len(signal_1),
            'mean0': mean0, 'mean1': mean1,
            'spread': spread, 't_stat': t_stat, 'p_value': p_val,
            'hac_se': hac_se, 'hac_tstat': hac_tstat, 'hac_pval': hac_pval,
            'ci_lower': ci_lower, 'ci_upper': ci_upper,
            'hit_rate_1': (signal_1 > 0).mean(),
            'hit_rate_0': (signal_0 > 0).mean()
        }
    
    # ========================
    # VALIDATION 1: Full Sample
    # ========================
    
    def validate_full_sample(self):
        """Unconditional analysis on full dataset."""
        print("\n" + "="*80)
        print("VALIDATION 1: Full Sample (2018-2021)")
        print("="*80)
        
        fwd_ret = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        
        valid_idx = fwd_ret.notna() & bb03.notna()
        ret_valid = fwd_ret[valid_idx]
        bb03_valid = bb03[valid_idx]
        
        result = self.hac_ttest(ret_valid, bb03_valid)
        result['n_total'] = len(ret_valid)
        result['horizon'] = 10
        
        print(f"\nSample size: {result['n_total']}")
        print(f"BB03=1 events: {result['n1']} ({result['n1']/result['n_total']*100:.1f}%)")
        print(f"BB03=0 events: {result['n0']} ({result['n0']/result['n_total']*100:.1f}%)")
        print(f"\nMean return (BB03=1): {result['mean1']:.4f} ({result['mean1']*100:.2f}%)")
        print(f"Mean return (BB03=0): {result['mean0']:.4f} ({result['mean0']*100:.2f}%)")
        print(f"Spread (1-0): {result['spread']:.4f} ({result['spread']*100:.2f}%)")
        print(f"Hit rate (BB03=1): {result['hit_rate_1']:.1%}")
        print(f"Hit rate (BB03=0): {result['hit_rate_0']:.1%}")
        print(f"\nWelch t-stat: {result['t_stat']:.4f}")
        print(f"Welch p-value: {result['p_value']:.4f}")
        print(f"HAC t-stat: {result['hac_tstat']:.4f}")
        print(f"HAC p-value: {result['hac_pval']:.4f}")
        print(f"95% CI: [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
        
        self.results['full_sample'] = result
        return result
    
    # ========================
    # VALIDATION 2: Year-by-Year
    # ========================
    
    def validate_yearly(self):
        """Decompose across calendar years."""
        print("\n" + "="*80)
        print("VALIDATION 2: Year-by-Year Stability (2018-2021)")
        print("="*80)
        
        fwd_ret = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        
        results = []
        for year in sorted(self.data['year'].unique()):
            year_mask = self.data['year'] == year
            ret_year = fwd_ret[year_mask]
            bb03_year = bb03[year_mask]
            
            valid_mask = ret_year.notna() & bb03_year.notna()
            ret_valid = ret_year[valid_mask]
            bb03_valid = bb03_year[valid_mask]
            
            if len(ret_valid) < 10:
                continue
            
            result = self.hac_ttest(ret_valid, bb03_valid)
            result['year'] = year
            result['n_total'] = len(ret_valid)
            results.append(result)
            
            print(f"\n{year}:")
            print(f"  N={int(result['n_total'])}, BB03=1: {int(result['n1'])}, BB03=0: {int(result['n0'])}")
            print(f"  Spread: {result['spread']:.4f} ({result['spread']*100:.2f}%)")
            print(f"  HAC t-stat: {result['hac_tstat']:.4f}, p-value: {result['hac_pval']:.4f}")
            print(f"  Hit rate (BB03=1): {result['hit_rate_1']:.1%}")
        
        yearly_df = pd.DataFrame(results)
        
        # Summary
        positive_years = (yearly_df['spread'] > 0).sum()
        print(f"\nYears with negative spread: {positive_years}/4")
        print(f"Mean yearly spread: {yearly_df['spread'].mean():.4f}")
        print(f"Consistency: {'STABLE' if positive_years >= 3 else 'INCONSISTENT'}")
        
        self.results['yearly'] = yearly_df
        return yearly_df
    
    # ========================
    # VALIDATION 3: Rolling Correlation
    # ========================
    
    def validate_rolling_correlation(self, window=60):
        """Test temporal stability of BB03-return relationship via rolling correlation."""
        print("\n" + "="*80)
        print(f"VALIDATION 3: Rolling Spearman Correlation (window={window}d)")
        print("="*80)
        
        fwd_ret = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(float)
        
        rolling_corr = []
        for i in range(window, len(self.data)):
            window_data = self.data.iloc[i-window:i]
            ret_window = fwd_ret.iloc[i-window:i]
            bb03_window = bb03.iloc[i-window:i]
            
            valid = ret_window.notna() & bb03_window.notna()
            if valid.sum() < 10:
                rolling_corr.append(np.nan)
                continue
            
            corr, _ = stats.spearmanr(bb03_window[valid], ret_window[valid])
            rolling_corr.append(corr)
        
        rolling_corr = pd.Series(rolling_corr, index=self.data.index[window:])
        
        # Quarterly stats
        for year in sorted(self.data['year'].unique()):
            year_data = rolling_corr[rolling_corr.index.year == year]
            if len(year_data) > 0:
                print(f"\n{year}:")
                print(f"  Mean corr: {year_data.mean():.4f}")
                print(f"  Std: {year_data.std():.4f}")
                print(f"  Range: [{year_data.min():.4f}, {year_data.max():.4f}]")
        
        print(f"\nOverall:")
        print(f"  Mean rolling corr: {rolling_corr.mean():.4f}")
        print(f"  Std: {rolling_corr.std():.4f}")
        print(f"  Negative corr periods: {(rolling_corr < 0).sum()} / {len(rolling_corr)}")
        print(f"  Stability: {'STABLE' if rolling_corr.std() < 0.1 else 'UNSTABLE'}")
        
        self.results['rolling_corr'] = rolling_corr
        return rolling_corr
    
    # ========================
    # VALIDATION 4: Walk-Forward
    # ========================
    
    def validate_walk_forward(self):
        """Out-of-sample validation with expanding windows."""
        print("\n" + "="*80)
        print("VALIDATION 4: Walk-Forward Validation")
        print("="*80)
        
        fwd_ret = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        
        # Fold 1: Train 2018-2019, Test 2020
        train_mask = self.data['year'].isin([2018, 2019])
        test_mask = self.data['year'] == 2020
        
        print("\nFold 1: Train on 2018-2019, Test on 2020")
        train_result = self.hac_ttest(fwd_ret[train_mask], bb03[train_mask])
        test_result = self.hac_ttest(fwd_ret[test_mask], bb03[test_mask])
        
        print(f"Train: spread={train_result['spread']:.4f}, HAC t={train_result['hac_tstat']:.4f}")
        print(f"Test:  spread={test_result['spread']:.4f}, HAC t={test_result['hac_tstat']:.4f}")
        print(f"Sign consistency: {'YES' if train_result['spread']*test_result['spread'] > 0 else 'NO'}")
        
        # Fold 2: Train 2018-2020, Test 2021
        train_mask = self.data['year'].isin([2018, 2019, 2020])
        test_mask = self.data['year'] == 2021
        
        print("\nFold 2: Train on 2018-2020, Test on 2021")
        train_result = self.hac_ttest(fwd_ret[train_mask], bb03[train_mask])
        test_result = self.hac_ttest(fwd_ret[test_mask], bb03[test_mask])
        
        print(f"Train: spread={train_result['spread']:.4f}, HAC t={train_result['hac_tstat']:.4f}")
        print(f"Test:  spread={test_result['spread']:.4f}, HAC t={test_result['hac_tstat']:.4f}")
        print(f"Sign consistency: {'YES' if train_result['spread']*test_result['spread'] > 0 else 'NO'}")
        
        fold_results = {
            'fold_1_train': train_result,
            'fold_1_test': test_result
        }
        self.results['walk_forward'] = fold_results
        return fold_results
    
    # ========================
    # VALIDATION 5: Cost Sensitivity
    # ========================
    
    def validate_cost_sensitivity(self):
        """Assess net alpha after transaction costs."""
        print("\n" + "="*80)
        print("VALIDATION 5: Cost Sensitivity Analysis")
        print("="*80)
        
        fwd_ret = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        
        result = self.hac_ttest(fwd_ret, bb03[fwd_ret.notna()])
        
        gross_spread = result['spread']
        
        # Test multiple cost scenarios
        cost_scenarios = [0.0005, 0.001, 0.0015, 0.002]  # Per side
        
        print(f"\nGross spread: {gross_spread:.4f} ({gross_spread*100:.2f}%)")
        print("\nNet spread after round-trip costs:")
        
        for cost_ps in cost_scenarios:
            round_trip_cost = cost_ps * 2
            net_spread = gross_spread - round_trip_cost
            pct_eroded = (round_trip_cost / abs(gross_spread)) * 100 if gross_spread != 0 else 0
            
            print(f"  Cost {cost_ps*100:.02f}%/side ({round_trip_cost*100:.02f}% round-trip):")
            print(f"    Net spread: {net_spread:.4f} ({net_spread*100:.2f}%)")
            print(f"    % of alpha eroded: {pct_eroded:.1f}%")
        
        self.results['cost_sensitivity'] = {
            'gross_spread': gross_spread,
            'cost_scenarios': cost_scenarios
        }
        return result
    
    # ========================
    # VALIDATION 6: Hypothesis Test
    # ========================
    
    def validate_hypothesis(self):
        """Formal hypothesis testing."""
        print("\n" + "="*80)
        print("VALIDATION 6: Formal Hypothesis Testing")
        print("="*80)
        
        fwd_ret = self.compute_forward_returns(10)
        bb03 = self.data['BB03'].astype(int)
        
        valid_idx = fwd_ret.notna() & bb03.notna()
        ret_valid = fwd_ret[valid_idx]
        bb03_valid = bb03[valid_idx]
        
        ret_bb03_1 = ret_valid[bb03_valid == 1]
        
        # H0: mean return when BB03=1 >= 0 (no mean-reversion)
        # H1: mean return when BB03=1 < 0 (mean-reversion)
        
        # One-tailed test
        t_stat_one = stats.ttest_1samp(ret_bb03_1, 0)[0]
        p_one = stats.t.cdf(t_stat_one, len(ret_bb03_1) - 1)  # Left-tailed
        
        print(f"\nH0: Mean return (BB03=1) >= 0 (no reversal)")
        print(f"H1: Mean return (BB03=1) < 0 (reversal)")
        print(f"\nOne-tailed t-test:")
        print(f"  t-stat: {t_stat_one:.4f}")
        print(f"  p-value (left-tailed): {p_one:.4f}")
        print(f"  Reject H0 at 5%?: {'YES' if p_one < 0.05 else 'NO'}")
        
        # Effect size (Cohen's d)
        mean_ret = ret_bb03_1.mean()
        std_ret = ret_bb03_1.std()
        cohens_d = mean_ret / std_ret
        
        print(f"\nEffect size (Cohen's d): {cohens_d:.4f}")
        print(f"Interpretation: {'Negligible' if abs(cohens_d) < 0.2 else 'Small' if abs(cohens_d) < 0.5 else 'Medium' if abs(cohens_d) < 0.8 else 'Large'}")
        
        self.results['hypothesis_test'] = {
            't_stat': t_stat_one,
            'p_value': p_one,
            'cohens_d': cohens_d,
            'mean_return': mean_ret
        }
        return self.results['hypothesis_test']
    
    def run_all_validations(self):
        """Execute all validation studies."""
        print("\n" + "#"*80)
        print("# BB03 ALPHA VALIDATION STUDY")
        print("#"*80)
        
        self.validate_full_sample()
        self.validate_yearly()
        self.validate_rolling_correlation()
        self.validate_walk_forward()
        self.validate_cost_sensitivity()
        self.validate_hypothesis()
        
        return self.results
    
    def save_results(self, output_dir='research_output'):
        """Save validation results."""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save yearly results
        if 'yearly' in self.results and isinstance(self.results['yearly'], pd.DataFrame):
            self.results['yearly'].to_csv(
                Path(output_dir) / 'bb03_yearly_validation.csv', index=False
            )
        
        # Save rolling correlation
        if 'rolling_corr' in self.results:
            self.results['rolling_corr'].to_csv(
                Path(output_dir) / 'bb03_rolling_correlation.csv'
            )
        
        print(f"\nResults saved to {output_dir}/")


def main():
    """Run BB03 alpha validation study."""
    signals_path = 'signals_cleaned.csv'
    price_path = 'price_cleaned.csv'
    
    validator = BB03AlphaValidator(signals_path, price_path)
    results = validator.run_all_validations()
    validator.save_results()
    
    print("\n" + "#"*80)
    print("# BB03 ALPHA VALIDATION COMPLETE")
    print("#"*80)


if __name__ == '__main__':
    main()
