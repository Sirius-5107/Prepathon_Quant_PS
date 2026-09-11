"""
BB01 Temporal Stability Analysis @ 20-day forward return.

Investigates whether BB01 breakout signal exhibits stable predictive power
across years 2018-2021.

Follows existing research methodology:
- Forward returns: Close[t+h] / Open[t+1] - 1
- Welch t-test (unequal variances) for binary signal
- Spearman rank correlation for monotonicity
- No threshold optimization, no parameter sweeps
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats


class BB01TemporalAnalyzer:
    """Analyze BB01 temporal stability at 20-day horizon."""
    
    def __init__(self, signals_path, price_path):
        """
        Initialize analyzer.
        
        Parameters:
        -----------
        signals_path : str
            Path to signals_cleaned.csv
        price_path : str
            Path to price_cleaned.csv
        """
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        # Ensure chronological order
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        # Merge on date
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        
        # Extract year
        self.data['year'] = self.data['date'].dt.year
        
        self.results = []
    
    def compute_forward_returns(self, horizon):
        """
        Compute forward returns: Close[t+h] / Open[t+h] - 1
        Uses open[t+1] per timing convention.
        """
        close_future = self.data['close'].shift(-horizon).values
        open_future = self.data['open'].shift(-horizon).values
        
        forward_ret = (close_future - open_future) / open_future
        
        return pd.Series(forward_ret, index=self.data.index)
    
    def analyze_year(self, year, fwd_ret, bb01):
        """
        Analyze BB01 effect for a single year.
        
        Returns dict with all metrics for that year.
        """
        year_mask = self.data['year'] == year
        
        ret_year = fwd_ret[year_mask]
        bb01_year = bb01[year_mask].astype(int)
        
        # Remove NaNs
        valid_mask = ret_year.notna() & bb01_year.notna()
        ret_valid = ret_year[valid_mask]
        bb01_valid = bb01_year[valid_mask]
        
        n_total = len(ret_valid)
        n_bb01_1 = (bb01_valid == 1).sum()
        n_bb01_0 = (bb01_valid == 0).sum()
        
        if n_total < 5:  # Insufficient data
            return {
                'year': year,
                'n_total': n_total,
                'n_bb01_1': n_bb01_1,
                'n_bb01_0': n_bb01_0,
                'mean_bb01_1': np.nan,
                'mean_bb01_0': np.nan,
                'spread': np.nan,
                'welch_tstat': np.nan,
                'welch_pval': np.nan,
                'spearman_ic': np.nan,
                'note': 'insufficient_data'
            }
        
        # Mean returns by signal state
        ret_bb01_1 = ret_valid[bb01_valid == 1]
        ret_bb01_0 = ret_valid[bb01_valid == 0]
        
        mean_bb01_1 = ret_bb01_1.mean() if len(ret_bb01_1) > 0 else np.nan
        mean_bb01_0 = ret_bb01_0.mean() if len(ret_bb01_0) > 0 else np.nan
        
        spread = mean_bb01_1 - mean_bb01_0
        
        # Welch t-test
        if len(ret_bb01_1) >= 2 and len(ret_bb01_0) >= 2:
            t_stat, p_val = stats.ttest_ind(ret_bb01_1, ret_bb01_0, equal_var=False)
        else:
            t_stat, p_val = np.nan, np.nan
        
        # Spearman correlation
        if len(ret_valid) >= 3:
            spearman_ic, _ = stats.spearmanr(bb01_valid.rank(), ret_valid.rank())
        else:
            spearman_ic = np.nan
        
        return {
            'year': year,
            'n_total': n_total,
            'n_bb01_1': n_bb01_1,
            'n_bb01_0': n_bb01_0,
            'mean_bb01_1': mean_bb01_1,
            'mean_bb01_0': mean_bb01_0,
            'spread': spread,
            'welch_tstat': t_stat,
            'welch_pval': p_val,
            'spearman_ic': spearman_ic,
            'note': ''
        }
    
    def run_temporal_analysis(self, horizon=20):
        """
        Run temporal stability analysis for BB01 @ specified horizon.
        """
        print(f"Running BB01 temporal stability analysis @ {horizon}d horizon...")
        
        # Compute forward returns
        fwd_ret = self.compute_forward_returns(horizon)
        bb01 = self.data['BB01'].astype(float)
        
        # Analyze each year
        years = sorted(self.data['year'].unique())
        for year in years:
            year_result = self.analyze_year(year, fwd_ret, bb01)
            self.results.append(year_result)
        
        results_df = pd.DataFrame(self.results)
        
        # Add pooled statistics
        print("\nComputing pooled statistics...")
        
        # Pooled analysis
        valid_mask = fwd_ret.notna() & bb01.notna()
        ret_pooled = fwd_ret[valid_mask]
        bb01_pooled = bb01[valid_mask].astype(int)
        
        ret_bb01_1_pool = ret_pooled[bb01_pooled == 1]
        ret_bb01_0_pool = ret_pooled[bb01_pooled == 0]
        
        mean_bb01_1_pool = ret_bb01_1_pool.mean()
        mean_bb01_0_pool = ret_bb01_0_pool.mean()
        spread_pool = mean_bb01_1_pool - mean_bb01_0_pool
        
        t_stat_pool, p_val_pool = stats.ttest_ind(ret_bb01_1_pool, ret_bb01_0_pool, equal_var=False)
        spearman_ic_pool, _ = stats.spearmanr(bb01_pooled.rank(), ret_pooled.rank())
        
        # Summary statistics on yearly spreads
        yearly_spreads = results_df['spread'].dropna()
        n_positive = (yearly_spreads > 0).sum()
        n_negative = (yearly_spreads < 0).sum()
        mean_spread = yearly_spreads.mean()
        median_spread = yearly_spreads.median()
        
        print("\n" + "="*80)
        print("TEMPORAL STABILITY SUMMARY")
        print("="*80)
        print(f"\nYearly Spread Direction:")
        print(f"  Positive: {n_positive} years")
        print(f"  Negative: {n_negative} years")
        print(f"  Mean yearly spread: {mean_spread:.4f} ({mean_spread*100:.2f}%)")
        print(f"  Median yearly spread: {median_spread:.4f} ({median_spread*100:.2f}%)")
        
        print(f"\nPooled Analysis (all years combined):")
        print(f"  N: {len(ret_pooled)}")
        print(f"  BB01=1: {(bb01_pooled==1).sum()}")
        print(f"  BB01=0: {(bb01_pooled==0).sum()}")
        print(f"  Mean return (BB01=1): {mean_bb01_1_pool:.4f} ({mean_bb01_1_pool*100:.2f}%)")
        print(f"  Mean return (BB01=0): {mean_bb01_0_pool:.4f} ({mean_bb01_0_pool*100:.2f}%)")
        print(f"  Spread: {spread_pool:.4f} ({spread_pool*100:.2f}%)")
        print(f"  Welch t-stat: {t_stat_pool:.4f}")
        print(f"  Welch p-value: {p_val_pool:.4f}")
        print(f"  Spearman IC: {spearman_ic_pool:.4f}")
        
        print("\n" + "="*80)
        print("YEAR-BY-YEAR BREAKDOWN")
        print("="*80 + "\n")
        
        for idx, row in results_df.iterrows():
            year = int(row['year'])
            print(f"Year {year}:")
            print(f"  Usable N: {int(row['n_total'])}")
            print(f"  BB01=1 observations: {int(row['n_bb01_1'])}")
            print(f"  BB01=0 observations: {int(row['n_bb01_0'])}")
            print(f"  Mean return (BB01=1): {row['mean_bb01_1']:.4f} ({row['mean_bb01_1']*100:.2f}%)")
            print(f"  Mean return (BB01=0): {row['mean_bb01_0']:.4f} ({row['mean_bb01_0']*100:.2f}%)")
            print(f"  Spread: {row['spread']:.4f} ({row['spread']*100:.2f}%)")
            print(f"  Welch t-stat: {row['welch_tstat']:.4f}")
            print(f"  Welch p-value: {row['welch_pval']:.4f}")
            print(f"  Spearman IC: {row['spearman_ic']:.4f}")
            if row['note']:
                print(f"  Note: {row['note']}")
            print()
        
        # Add pooled row for reference
        pooled_row = pd.DataFrame([{
            'year': 'POOLED',
            'n_total': len(ret_pooled),
            'n_bb01_1': (bb01_pooled==1).sum(),
            'n_bb01_0': (bb01_pooled==0).sum(),
            'mean_bb01_1': mean_bb01_1_pool,
            'mean_bb01_0': mean_bb01_0_pool,
            'spread': spread_pool,
            'welch_tstat': t_stat_pool,
            'welch_pval': p_val_pool,
            'spearman_ic': spearman_ic_pool,
            'note': 'all_years'
        }])
        
        results_df = pd.concat([results_df, pooled_row], ignore_index=True)
        
        # Stability classification
        print("\n" + "="*80)
        print("STABILITY CLASSIFICATION")
        print("="*80 + "\n")
        
        if n_positive == len(yearly_spreads) and all(results_df['welch_pval'].dropna() < 0.05):
            classification = "STABLE: Positive and significant across all years"
        elif n_positive >= len(yearly_spreads) * 0.75 and median_spread > 0:
            classification = "DIRECTIONALLY CONSISTENT: Positive in majority of years, but statistically weak"
        elif n_positive == 1:
            classification = "UNSTABLE: Positive effect driven by single year only"
        elif n_negative == len(yearly_spreads):
            classification = "REJECT: Consistently negative, opposite to hypothesis"
        elif n_positive >= 2 and median_spread > 0:
            classification = "MIXED: Positive in some years, negative in others"
        else:
            classification = "MARGINAL: Weak evidence, requires further scrutiny"
        
        print(f"Classification: {classification}\n")
        
        print("="*80 + "\n")
        
        return results_df
    
    def save_results(self, results_df, output_dir='research_output'):
        """Save temporal stability results."""
        Path(output_dir).mkdir(exist_ok=True)
        
        filepath = Path(output_dir) / 'bb01_temporal_stability.csv'
        results_df.to_csv(filepath, index=False)
        
        print(f"Results saved to: {filepath}")
        
        return filepath


def main():
    """Run BB01 temporal stability analysis."""
    
    # Paths
    signals_path = 'signals_cleaned.csv'
    price_path = 'price_cleaned.csv'
    
    # Initialize analyzer
    analyzer = BB01TemporalAnalyzer(signals_path, price_path)
    
    # Run temporal analysis @ 20d horizon
    results_df = analyzer.run_temporal_analysis(horizon=20)
    
    # Save results
    analyzer.save_results(results_df)
    
    print("BB01 temporal stability analysis complete.")


if __name__ == '__main__':
    main()
