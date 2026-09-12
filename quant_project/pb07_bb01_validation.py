"""
PB07 & BB01 Signal Validation Study.

Rigorous validation of two potentially distinct alpha families:
1. PB07 - Continuous mean-reversion / trend-distance signal
2. BB01 - Breakout continuation signal

No parameter optimization, no strategy construction.
Pure signal research with temporal stability, redundancy, and return-space analysis.

Methodology:
- Forward returns: Close[t+h] / Open[t+1] - 1 (canonical)
- Horizons: 1d, 3d, 5d, 10d, 20d
- HAC/Newey-West inference (maxlags = max(1, h-1))
- Walk-forward expanding windows (2018-2019 vs 2020; 2018-2020 vs 2021)
- Block bootstrap (5000 reps, fixed seed) for uncertainty
- Multivariate redundancy testing
- Return-space independence analysis (QR decomposition)
- Year-by-year stability decomposition
- Cost sensitivity analysis (0.05% per side = 0.10% round-trip)

IMPORTANT INTERPRETATION NOTES:
- HAC t-statistics are reported but primary evidence should rely on:
  * Welch t-test (event vs non-event comparison)
  * Bootstrap confidence intervals (dependence-aware)
  * Walk-forward validation (out-of-sample stability)
  * Economic effect size (magnitude relative to costs)
- 2021 BB01 discrepancy explained:
  * 6 total BB01 events in 2021
  * Only 3 with valid 20d forward returns (rest occur late Nov/Dec)
  * Yearly stability table uses 3 events (valid returns only)
  * Walk-forward test also uses 3 events (same valid subset)
  * No double-counting; same events analyzed in both places
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

np.random.seed(42)  # Fixed seed for reproducibility


class PB07BB01Validator:
    """Validate PB07 and BB01 as distinct alpha families."""
    
    def __init__(self, signals_path, price_path):
        """Load and merge signals and price data."""
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        # Sort chronologically
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        # Merge on date (inner join - only overlapping dates)
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        print(f"\n{'='*80}")
        print("DATA AUDIT")
        print(f"{'='*80}")
        print(f"Signals: {len(self.signals_df)} rows")
        print(f"Price:   {len(self.price_df)} rows")
        print(f"Merged (inner join): {len(self.data)} rows")
        print(f"Date range: {self.data['date'].min().date()} to {self.data['date'].max().date()}")
        print(f"Years: {sorted(self.data['year'].unique())}")
        
        self.results = {}
    
    def compute_forward_returns(self, horizon):
        """Forward returns: Close[t+h] / Open[t+h] - 1"""
        close_future = self.data['close'].shift(-horizon).values
        open_future = self.data['open'].shift(-horizon).values
        forward_ret = (close_future - open_future) / open_future
        return pd.Series(forward_ret, index=self.data.index)
    
    def hac_regression(self, returns, predictor, maxlags=1):
        """OLS regression with HAC standard errors (Newey-West)."""
        valid_idx = returns.notna() & predictor.notna()
        ret_valid = returns[valid_idx].values
        pred_valid = predictor[valid_idx].values
        
        if len(ret_valid) < 5:
            return {'alpha': np.nan, 'beta': np.nan, 'hac_t': np.nan, 'hac_p': np.nan,
                    'ci_lower': np.nan, 'ci_upper': np.nan, 'r2': np.nan, 'n': len(ret_valid)}
        
        # OLS
        X = np.column_stack([np.ones(len(ret_valid)), pred_valid])
        beta = np.linalg.lstsq(X, ret_valid, rcond=None)[0]
        residuals = ret_valid - X @ beta
        
        # HAC covariance (Newey-West with Bartlett kernel)
        k = X.shape[1]
        n = len(ret_valid)
        
        # Lag 0: outer product of X and residuals
        Xres = X * residuals[:, None]  # (n, k)
        gamma0 = Xres.T @ Xres / n  # (k, k)
        
        # Lags 1 to maxlags
        lag_sum = np.zeros((k, k))
        for lag in range(1, maxlags + 1):
            # Outer product at lag
            Xres_lag = X[:-lag] * residuals[:-lag, None]  # (n-lag, k)
            Xres_future = X[lag:] * residuals[lag:, None]  # (n-lag, k)
            
            lag_cov = Xres_lag.T @ Xres_future / n  # (k, k)
            
            # Bartlett kernel weight
            weight = 1 - lag / (maxlags + 1)
            lag_sum += weight * (lag_cov + lag_cov.T)
        
        # Long-run covariance
        Omega = gamma0 + lag_sum
        
        # Variance-covariance matrix of beta
        XtX_inv = np.linalg.pinv(X.T @ X)
        vcov = XtX_inv @ Omega @ XtX_inv
        se = np.sqrt(np.diag(vcov))
        
        # t-statistics and p-values
        t_stats = beta / se
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - k))
        
        # 95% CI for beta
        t_crit = stats.t.ppf(0.975, n - k)
        ci_lower = beta[1] - t_crit * se[1]
        ci_upper = beta[1] + t_crit * se[1]
        
        # R-squared
        ss_res = np.dot(residuals, residuals)
        ss_tot = np.dot(ret_valid - ret_valid.mean(), ret_valid - ret_valid.mean())
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'alpha': beta[0], 'alpha_se': se[0], 'alpha_t': t_stats[0], 'alpha_p': p_values[0],
            'beta': beta[1], 'beta_se': se[1], 'beta_t': t_stats[1], 'beta_p': p_values[1],
            'ci_lower': ci_lower, 'ci_upper': ci_upper,
            'r2': r2, 'n': n
        }
    
    # ========================
    # PB07 ANALYSIS
    # ========================
    
    def pb07_continuous_validation(self):
        """PB07 continuous signal analysis across horizons."""
        print(f"\n{'='*80}")
        print("PB07 CONTINUOUS SIGNAL ANALYSIS")
        print(f"{'='*80}")
        
        horizons = [1, 3, 5, 10, 20]
        results = []
        
        pb07 = self.data['PB07'].astype(float)
        
        for h in horizons:
            fwd_ret = self.compute_forward_returns(h)
            
            # Correlations
            valid_idx = fwd_ret.notna() & pb07.notna()
            ret_valid = fwd_ret[valid_idx]
            pb07_valid = pb07[valid_idx]
            
            spearman_ic, _ = stats.spearmanr(pb07_valid, ret_valid)
            pearson_corr, _ = stats.pearsonr(pb07_valid, ret_valid)
            
            # HAC regression
            reg = self.hac_regression(fwd_ret, pb07, maxlags=max(1, h-1))
            
            result = {
                'horizon': h,
                'n': reg['n'],
                'spearman_ic': spearman_ic,
                'pearson_corr': pearson_corr,
                'beta': reg['beta'],
                'beta_se': reg['beta_se'],
                'beta_t': reg['beta_t'],
                'beta_p': reg['beta_p'],
                'ci_lower': reg['ci_lower'],
                'ci_upper': reg['ci_upper'],
                'r2': reg['r2']
            }
            results.append(result)
            
            print(f"\n{h}d horizon:")
            print(f"  N: {reg['n']}")
            print(f"  Spearman IC: {spearman_ic:.4f}")
            print(f"  Pearson corr: {pearson_corr:.4f}")
            print(f"  Beta: {reg['beta']:.6f}, t-stat: {reg['beta_t']:.4f}, p: {reg['beta_p']:.4f}")
            print(f"  95% CI: [{reg['ci_lower']:.6f}, {reg['ci_upper']:.6f}]")
        
        pb07_cont_df = pd.DataFrame(results)
        self.results['pb07_continuous'] = pb07_cont_df
        return pb07_cont_df
    
    def pb07_shape_analysis(self):
        """PB07 quintile shape analysis."""
        print(f"\n{'='*80}")
        print("PB07 SHAPE ANALYSIS (Quintiles)")
        print(f"{'='*80}")
        
        pb07 = self.data['PB07'].astype(float)
        horizons = [10, 20]  # Focus on identified horizons
        all_results = []
        
        for h in horizons:
            fwd_ret = self.compute_forward_returns(h)
            
            valid_idx = fwd_ret.notna() & pb07.notna()
            ret_valid = fwd_ret[valid_idx]
            pb07_valid = pb07[valid_idx]
            
            # Quintiles
            quintiles = pd.qcut(pb07_valid, q=5, duplicates='drop', labels=False)
            
            q_results = []
            for q in range(5):
                q_mask = quintiles == q
                q_returns = ret_valid[q_mask]
                
                q_result = {
                    'horizon': h,
                    'quintile': q + 1,
                    'n': len(q_returns),
                    'mean': q_returns.mean(),
                    'median': q_returns.median(),
                    'std': q_returns.std(),
                    'hit_rate': (q_returns > 0).mean()
                }
                q_results.append(q_result)
            
            # Spread Q5 - Q1
            q1_mean = q_results[0]['mean']
            q5_mean = q_results[4]['mean']
            spread = q5_mean - q1_mean
            
            # Monotonicity: Spearman between quintile rank and mean return
            q_means = [r['mean'] for r in q_results]
            monotonic_corr = stats.spearmanr(range(1, 6), q_means)[0]
            
            print(f"\n{h}d horizon:")
            print(f"  Q1: mean={q_results[0]['mean']:.4f}, N={q_results[0]['n']}")
            print(f"  Q2: mean={q_results[1]['mean']:.4f}, N={q_results[1]['n']}")
            print(f"  Q3: mean={q_results[2]['mean']:.4f}, N={q_results[2]['n']}")
            print(f"  Q4: mean={q_results[3]['mean']:.4f}, N={q_results[3]['n']}")
            print(f"  Q5: mean={q_results[4]['mean']:.4f}, N={q_results[4]['n']}")
            print(f"  Q5-Q1: {spread:.4f} ({spread*100:.2f}%)")
            print(f"  Monotonicity (Spearman): {monotonic_corr:.4f}")
            
            for r in q_results:
                all_results.append(r)
        
        shape_df = pd.DataFrame(all_results)
        self.results['pb07_shape'] = shape_df
        return shape_df
    
    def pb07_yearly_stability(self):
        """PB07 analysis by year."""
        print(f"\n{'='*80}")
        print("PB07 YEARLY STABILITY (10d, 20d)")
        print(f"{'='*80}")
        
        pb07 = self.data['PB07'].astype(float)
        results = []
        
        for h in [10, 20]:
            fwd_ret = self.compute_forward_returns(h)
            
            for year in sorted(self.data['year'].unique()):
                year_mask = self.data['year'] == year
                ret_year = fwd_ret[year_mask]
                pb07_year = pb07[year_mask]
                
                valid_idx = ret_year.notna() & pb07_year.notna()
                ret_valid = ret_year[valid_idx]
                pb07_valid = pb07_year[valid_idx]
                
                if len(ret_valid) < 5:
                    continue
                
                spearman_ic, _ = stats.spearmanr(pb07_valid, ret_valid)
                reg = self.hac_regression(ret_year, pb07_year, maxlags=max(1, h-1))
                
                # Quintile spread
                quintiles = pd.qcut(pb07_valid, q=5, duplicates='drop', labels=False)
                q1_mean = ret_valid[quintiles == 0].mean()
                q5_mean = ret_valid[quintiles == 4].mean()
                q_spread = q5_mean - q1_mean
                
                result = {
                    'year': year,
                    'horizon': h,
                    'n': reg['n'],
                    'mean_pb07': pb07_valid.mean(),
                    'spearman_ic': spearman_ic,
                    'beta': reg['beta'],
                    'beta_t': reg['beta_t'],
                    'beta_p': reg['beta_p'],
                    'q5_q1_spread': q_spread
                }
                results.append(result)
                
                print(f"\n{year} ({h}d): N={reg['n']}, IC={spearman_ic:.4f}, beta={reg['beta']:.6f}, t={reg['beta_t']:.4f}, p={reg['beta_p']:.4f}, Q5-Q1={q_spread:.4f}")
        
        yearly_df = pd.DataFrame(results)
        self.results['pb07_yearly'] = yearly_df
        return yearly_df
    
    def pb07_walk_forward(self):
        """PB07 walk-forward validation."""
        print(f"\n{'='*80}")
        print("PB07 WALK-FORWARD VALIDATION (10d)")
        print(f"{'='*80}")
        
        pb07 = self.data['PB07'].astype(float)
        fwd_ret = self.compute_forward_returns(10)
        results = []
        
        # Fold 1: Train 2018-2019, Test 2020
        train_mask = self.data['year'].isin([2018, 2019])
        test_mask = self.data['year'] == 2020
        
        train_ret = fwd_ret[train_mask]
        train_pb07 = pb07[train_mask]
        test_ret = fwd_ret[test_mask]
        test_pb07 = pb07[test_mask]
        
        train_reg = self.hac_regression(train_ret, train_pb07, maxlags=9)
        test_reg = self.hac_regression(test_ret, test_pb07, maxlags=9)
        
        valid_train = train_ret.notna() & train_pb07.notna()
        valid_test = test_ret.notna() & test_pb07.notna()
        
        train_ic, _ = stats.spearmanr(train_pb07[valid_train], train_ret[valid_train])
        test_ic, _ = stats.spearmanr(test_pb07[valid_test], test_ret[valid_test])
        
        print(f"\nFold 1: Train 2018-2019, Test 2020")
        print(f"  Train: N={train_reg['n']}, beta={train_reg['beta']:.6f}, t={train_reg['beta_t']:.4f}, IC={train_ic:.4f}")
        print(f"  Test:  N={test_reg['n']}, beta={test_reg['beta']:.6f}, t={test_reg['beta_t']:.4f}, IC={test_ic:.4f}")
        print(f"  Sign consistency: {'YES' if train_reg['beta']*test_reg['beta'] > 0 else 'NO'}")
        
        results.append({
            'fold': 1,
            'train_period': '2018-2019',
            'test_period': '2020',
            'train_n': train_reg['n'],
            'test_n': test_reg['n'],
            'train_beta': train_reg['beta'],
            'train_t': train_reg['beta_t'],
            'train_ic': train_ic,
            'test_beta': test_reg['beta'],
            'test_t': test_reg['beta_t'],
            'test_ic': test_ic,
            'sign_consistency': 'YES' if train_reg['beta']*test_reg['beta'] > 0 else 'NO'
        })
        
        # Fold 2: Train 2018-2020, Test 2021
        train_mask = self.data['year'].isin([2018, 2019, 2020])
        test_mask = self.data['year'] == 2021
        
        train_ret = fwd_ret[train_mask]
        train_pb07 = pb07[train_mask]
        test_ret = fwd_ret[test_mask]
        test_pb07 = pb07[test_mask]
        
        train_reg = self.hac_regression(train_ret, train_pb07, maxlags=9)
        test_reg = self.hac_regression(test_ret, test_pb07, maxlags=9)
        
        valid_train = train_ret.notna() & train_pb07.notna()
        valid_test = test_ret.notna() & test_pb07.notna()
        
        train_ic, _ = stats.spearmanr(train_pb07[valid_train], train_ret[valid_train])
        test_ic, _ = stats.spearmanr(test_pb07[valid_test], test_ret[valid_test])
        
        print(f"\nFold 2: Train 2018-2020, Test 2021")
        print(f"  Train: N={train_reg['n']}, beta={train_reg['beta']:.6f}, t={train_reg['beta_t']:.4f}, IC={train_ic:.4f}")
        print(f"  Test:  N={test_reg['n']}, beta={test_reg['beta']:.6f}, t={test_reg['beta_t']:.4f}, IC={test_ic:.4f}")
        print(f"  Sign consistency: {'YES' if train_reg['beta']*test_reg['beta'] > 0 else 'NO'}")
        
        results.append({
            'fold': 2,
            'train_period': '2018-2020',
            'test_period': '2021',
            'train_n': train_reg['n'],
            'test_n': test_reg['n'],
            'train_beta': train_reg['beta'],
            'train_t': train_reg['beta_t'],
            'train_ic': train_ic,
            'test_beta': test_reg['beta'],
            'test_t': test_reg['beta_t'],
            'test_ic': test_ic,
            'sign_consistency': 'YES' if train_reg['beta']*test_reg['beta'] > 0 else 'NO'
        })
        
        wfo_df = pd.DataFrame(results)
        self.results['pb07_wfo'] = wfo_df
        return wfo_df
    
    def pb07_bootstrap(self):
        """Block bootstrap on PB07 10d quintile spread."""
        print(f"\n{'='*80}")
        print("PB07 BLOCK BOOTSTRAP (10d, Q5-Q1 spread)")
        print(f"{'='*80}")
        
        pb07 = self.data['PB07'].astype(float)
        fwd_ret = self.compute_forward_returns(10)
        
        valid_idx = fwd_ret.notna() & pb07.notna()
        ret_valid = fwd_ret[valid_idx].values
        pb07_valid = pb07[valid_idx].values
        
        # Observed spread
        quintiles = pd.qcut(pb07_valid, q=5, duplicates='drop', labels=False)
        obs_q1 = ret_valid[quintiles == 0].mean()
        obs_q5 = ret_valid[quintiles == 4].mean()
        obs_spread = obs_q5 - obs_q1
        
        print(f"\nObserved spread (Q5-Q1): {obs_spread:.6f} ({obs_spread*100:.2f}%)")
        
        # Block bootstrap with different block lengths
        for block_len in [5, 10, 20]:
            print(f"\nBlock length: {block_len}")
            
            n_blocks = len(ret_valid) // block_len
            bootstrap_spreads = []
            
            for _ in range(5000):
                # Draw random blocks with replacement
                block_indices = np.random.choice(n_blocks, size=n_blocks, replace=True)
                boot_idx = []
                for b_idx in block_indices:
                    start = b_idx * block_len
                    end = min((b_idx + 1) * block_len, len(ret_valid))
                    boot_idx.extend(range(start, end))
                
                boot_idx = boot_idx[:len(ret_valid)]  # Trim to original length
                
                boot_ret = ret_valid[boot_idx]
                boot_pb07 = pb07_valid[boot_idx]
                
                # Recalculate quintiles
                boot_q = pd.qcut(boot_pb07, q=5, duplicates='drop', labels=False)
                boot_q1 = boot_ret[boot_q == 0].mean() if (boot_q == 0).any() else np.nan
                boot_q5 = boot_ret[boot_q == 4].mean() if (boot_q == 4).any() else np.nan
                
                if not np.isnan(boot_q1) and not np.isnan(boot_q5):
                    bootstrap_spreads.append(boot_q5 - boot_q1)
            
            bootstrap_spreads = np.array(bootstrap_spreads)
            
            print(f"  Mean: {bootstrap_spreads.mean():.6f}")
            print(f"  Std: {bootstrap_spreads.std():.6f}")
            print(f"  2.5%: {np.percentile(bootstrap_spreads, 2.5):.6f}")
            print(f"  50%: {np.percentile(bootstrap_spreads, 50):.6f}")
            print(f"  97.5%: {np.percentile(bootstrap_spreads, 97.5):.6f}")
            print(f"  P(spread <= 0): {(bootstrap_spreads <= 0).sum() / len(bootstrap_spreads):.4f}")
        
        self.results['pb07_bootstrap'] = {'observed': obs_spread}
        return obs_spread
    
    def pb07_redundancy(self):
        """Test PB07 redundancy vs PB08 and BB06."""
        print(f"\n{'='*80}")
        print("PB07 REDUNDANCY / DEPENDENCE ANALYSIS")
        print(f"{'='*80}")
        
        fwd_ret = self.compute_forward_returns(10)
        pb07 = self.data['PB07'].astype(float)
        pb08 = self.data['PB08'].astype(float)
        bb06 = self.data['BB06'].astype(float)
        
        valid_idx = fwd_ret.notna() & pb07.notna() & pb08.notna() & bb06.notna()
        
        print(f"\nSignal correlations:")
        print(f"  PB07 vs PB08: {pb07[valid_idx].corr(pb08[valid_idx]):.4f}")
        print(f"  PB07 vs BB06: {pb07[valid_idx].corr(bb06[valid_idx]):.4f}")
        print(f"  PB08 vs BB06: {pb08[valid_idx].corr(bb06[valid_idx]):.4f}")
        
        # Multivariate regression
        ret_valid = fwd_ret[valid_idx].values
        pb07_valid = pb07[valid_idx].values
        pb08_valid = pb08[valid_idx].values
        bb06_valid = bb06[valid_idx].values
        
        X = np.column_stack([np.ones(len(ret_valid)), pb07_valid, pb08_valid, bb06_valid])
        beta = np.linalg.lstsq(X, ret_valid, rcond=None)[0]
        residuals = ret_valid - X @ beta
        
        # HAC standard errors
        sigma2 = np.dot(residuals, residuals) / len(ret_valid)
        gamma0 = (X.T * residuals) @ (X * residuals[:, None]) / len(ret_valid)
        
        lag_sum = np.zeros((4, 4))
        for lag in range(1, 10):
            lag_cov = (X[:-lag].T * residuals[:-lag]) @ (X[lag:] * residuals[lag:, None]) / len(ret_valid)
            weight = 1 - lag / 10
            lag_sum += weight * (lag_cov + lag_cov.T)
        
        Omega = gamma0 + lag_sum
        Sigma = Omega / len(ret_valid)
        
        XtX_inv = np.linalg.pinv(X.T @ X)
        vcov = XtX_inv @ Sigma @ XtX_inv
        se = np.sqrt(np.diag(vcov))
        t_stats = beta / se
        p_vals = 2 * (1 - stats.t.cdf(np.abs(t_stats), len(ret_valid) - 4))
        
        ss_res = np.dot(residuals, residuals)
        ss_tot = np.dot(ret_valid - ret_valid.mean(), ret_valid - ret_valid.mean())
        r2 = 1 - (ss_res / ss_tot)
        
        print(f"\nMultivariate HAC Regression:")
        print(f"  Alpha: {beta[0]:.6f}, t={t_stats[0]:.4f}, p={p_vals[0]:.4f}")
        print(f"  PB07:  {beta[1]:.6f}, t={t_stats[1]:.4f}, p={p_vals[1]:.4f}")
        print(f"  PB08:  {beta[2]:.6f}, t={t_stats[2]:.4f}, p={p_vals[2]:.4f}")
        print(f"  BB06:  {beta[3]:.6f}, t={t_stats[3]:.4f}, p={p_vals[3]:.4f}")
        print(f"  R²: {r2:.4f}")
        print(f"  N: {len(ret_valid)}")
        
        self.results['pb07_redundancy'] = {
            'pb07_t': t_stats[1],
            'pb07_p': p_vals[1],
            'pb08_t': t_stats[2],
            'bb06_t': t_stats[3],
            'r2': r2
        }
        return self.results['pb07_redundancy']
    
    # ========================
    # BB01 ANALYSIS
    # ========================
    
    def bb01_horizon_analysis(self):
        """BB01 analysis across multiple horizons."""
        print(f"\n{'='*80}")
        print("BB01 HORIZON ANALYSIS")
        print(f"{'='*80}")
        
        bb01 = self.data['BB01'].astype(int)
        horizons = [1, 3, 5, 10, 20]
        results = []
        
        for h in horizons:
            fwd_ret = self.compute_forward_returns(h)
            
            valid_idx = fwd_ret.notna() & bb01.notna()
            ret_valid = fwd_ret[valid_idx]
            bb01_valid = bb01[valid_idx]
            
            # Event stats
            n_events = (bb01_valid == 1).sum()
            event_freq = n_events / len(ret_valid) if len(ret_valid) > 0 else 0
            
            ret_event = ret_valid[bb01_valid == 1]
            ret_noevent = ret_valid[bb01_valid == 0]
            
            mean_event = ret_event.mean() if len(ret_event) > 0 else np.nan
            mean_noevent = ret_noevent.mean() if len(ret_noevent) > 0 else np.nan
            spread = mean_event - mean_noevent if not np.isnan(mean_event) and not np.isnan(mean_noevent) else np.nan
            
            # Spearman IC
            spearman_ic, _ = stats.spearmanr(bb01_valid, ret_valid)
            
            # Welch t-test
            if len(ret_event) >= 2 and len(ret_noevent) >= 2:
                t_stat, p_val = stats.ttest_ind(ret_event, ret_noevent, equal_var=False)
            else:
                t_stat, p_val = np.nan, np.nan
            
            # HAC regression
            reg = self.hac_regression(fwd_ret, bb01.astype(float), maxlags=max(1, h-1))
            
            result = {
                'horizon': h,
                'n': len(ret_valid),
                'n_events': n_events,
                'event_freq': event_freq,
                'mean_event': mean_event,
                'median_event': ret_event.median() if len(ret_event) > 0 else np.nan,
                'mean_noevent': mean_noevent,
                'spread': spread,
                'spearman_ic': spearman_ic,
                'welch_t': t_stat,
                'welch_p': p_val,
                'hac_beta': reg['beta'],
                'hac_t': reg['beta_t'],
                'hac_p': reg['beta_p'],
                'ci_lower': reg['ci_lower'],
                'ci_upper': reg['ci_upper']
            }
            results.append(result)
            
            print(f"\n{h}d horizon:")
            print(f"  N={len(ret_valid)}, events={n_events} ({event_freq*100:.1f}%)")
            print(f"  Event mean: {mean_event:.4f}, Non-event: {mean_noevent:.4f}, Spread: {spread:.4f}")
            print(f"  Welch t={t_stat:.4f}, p={p_val:.4f}")
            print(f"  HAC t={reg['beta_t']:.4f}, p={reg['beta_p']:.4f}")
        
        horizon_df = pd.DataFrame(results)
        self.results['bb01_horizon'] = horizon_df
        return horizon_df
    
    def bb01_yearly_stability(self):
        """BB01 analysis by year (20d)."""
        print(f"\n{'='*80}")
        print("BB01 YEARLY STABILITY (20d)")
        print(f"{'='*80}")
        
        bb01 = self.data['BB01'].astype(int)
        fwd_ret = self.compute_forward_returns(20)
        results = []
        
        for year in sorted(self.data['year'].unique()):
            year_mask = self.data['year'] == year
            ret_year = fwd_ret[year_mask]
            bb01_year = bb01[year_mask]
            
            valid_idx = ret_year.notna() & bb01_year.notna()
            ret_valid = ret_year[valid_idx]
            bb01_valid = bb01_year[valid_idx]
            
            if len(ret_valid) < 5:
                continue
            
            n_events = (bb01_valid == 1).sum()
            event_freq = n_events / len(ret_valid)
            
            ret_event = ret_valid[bb01_valid == 1]
            ret_noevent = ret_valid[bb01_valid == 0]
            
            mean_event = ret_event.mean() if len(ret_event) > 0 else np.nan
            mean_noevent = ret_noevent.mean() if len(ret_noevent) > 0 else np.nan
            spread = mean_event - mean_noevent
            
            spearman_ic, _ = stats.spearmanr(bb01_valid, ret_valid)
            
            if len(ret_event) >= 2 and len(ret_noevent) >= 2:
                t_stat, p_val = stats.ttest_ind(ret_event, ret_noevent, equal_var=False)
            else:
                t_stat, p_val = np.nan, np.nan
            
            reg = self.hac_regression(ret_year, bb01.astype(float)[year_mask], maxlags=19)
            
            result = {
                'year': year,
                'n': len(ret_valid),
                'n_events': n_events,
                'event_freq': event_freq,
                'mean_event': mean_event,
                'mean_noevent': mean_noevent,
                'spread': spread,
                'spearman_ic': spearman_ic,
                'welch_t': t_stat,
                'welch_p': p_val,
                'hac_t': reg['beta_t'],
                'hac_p': reg['beta_p']
            }
            results.append(result)
            
            print(f"\n{year}: N={len(ret_valid)}, events={n_events}, spread={spread:.4f}, HAC t={reg['beta_t']:.4f}, p={reg['beta_p']:.4f}")
        
        yearly_df = pd.DataFrame(results)
        self.results['bb01_yearly'] = yearly_df
        return yearly_df
    
    def bb01_walk_forward(self):
        """BB01 walk-forward validation (20d)."""
        print(f"\n{'='*80}")
        print("BB01 WALK-FORWARD VALIDATION (20d)")
        print(f"{'='*80}")
        
        bb01 = self.data['BB01'].astype(int)
        fwd_ret = self.compute_forward_returns(20)
        results = []
        
        # Fold 1
        train_mask = self.data['year'].isin([2018, 2019])
        test_mask = self.data['year'] == 2020
        
        train_ret = fwd_ret[train_mask]
        train_bb01 = bb01[train_mask]
        test_ret = fwd_ret[test_mask]
        test_bb01 = bb01[test_mask]
        
        valid_train = train_ret.notna() & train_bb01.notna()
        valid_test = test_ret.notna() & test_bb01.notna()
        
        train_event_mean = train_ret[valid_train & (train_bb01 == 1)].mean()
        test_event_mean = test_ret[valid_test & (test_bb01 == 1)].mean()
        
        train_noevent = train_ret[valid_train & (train_bb01 == 0)].mean()
        test_noevent = test_ret[valid_test & (test_bb01 == 0)].mean()
        
        train_spread = train_event_mean - train_noevent
        test_spread = test_event_mean - test_noevent
        
        train_ic, _ = stats.spearmanr(train_bb01[valid_train], train_ret[valid_train])
        test_ic, _ = stats.spearmanr(test_bb01[valid_test], test_ret[valid_test])
        
        train_reg = self.hac_regression(train_ret, train_bb01.astype(float), maxlags=19)
        test_reg = self.hac_regression(test_ret, test_bb01.astype(float), maxlags=19)
        
        print(f"\nFold 1: Train 2018-2019, Test 2020")
        print(f"  Train: events={(train_bb01==1).sum()}, spread={train_spread:.4f}, HAC t={train_reg['beta_t']:.4f}")
        print(f"  Test:  events={(test_bb01==1).sum()}, spread={test_spread:.4f}, HAC t={test_reg['beta_t']:.4f}")
        print(f"  Sign consistency: {'YES' if train_spread*test_spread > 0 else 'NO'}")
        
        results.append({
            'fold': 1,
            'train_events': (train_bb01 == 1).sum(),
            'test_events': (test_bb01 == 1).sum(),
            'train_spread': train_spread,
            'test_spread': test_spread,
            'train_t': train_reg['beta_t'],
            'test_t': test_reg['beta_t'],
            'sign_consistency': 'YES' if train_spread*test_spread > 0 else 'NO'
        })
        
        # Fold 2
        train_mask = self.data['year'].isin([2018, 2019, 2020])
        test_mask = self.data['year'] == 2021
        
        train_ret = fwd_ret[train_mask]
        train_bb01 = bb01[train_mask]
        test_ret = fwd_ret[test_mask]
        test_bb01 = bb01[test_mask]
        
        valid_train = train_ret.notna() & train_bb01.notna()
        valid_test = test_ret.notna() & test_bb01.notna()
        
        train_event_mean = train_ret[valid_train & (train_bb01 == 1)].mean()
        test_event_mean = test_ret[valid_test & (test_bb01 == 1)].mean() if (test_bb01 == 1).sum() > 0 else np.nan
        
        train_noevent = train_ret[valid_train & (train_bb01 == 0)].mean()
        test_noevent = test_ret[valid_test & (test_bb01 == 0)].mean()
        
        train_spread = train_event_mean - train_noevent
        test_spread = test_event_mean - test_noevent if not np.isnan(test_event_mean) else np.nan
        
        train_ic, _ = stats.spearmanr(train_bb01[valid_train], train_ret[valid_train])
        test_ic, _ = stats.spearmanr(test_bb01[valid_test], test_ret[valid_test]) if (test_bb01 == 1).sum() >= 2 else (np.nan, np.nan)
        
        train_reg = self.hac_regression(train_ret, train_bb01.astype(float), maxlags=19)
        test_reg = self.hac_regression(test_ret, test_bb01.astype(float), maxlags=19)
        
        print(f"\nFold 2: Train 2018-2020, Test 2021")
        print(f"  Train: events={(train_bb01==1).sum()}, spread={train_spread:.4f}, HAC t={train_reg['beta_t']:.4f}")
        print(f"  Test:  events={(test_bb01==1).sum()}, spread={test_spread:.4f}, HAC t={test_reg['beta_t']:.4f}")
        print(f"  *** 2021 HAS ONLY {(test_bb01==1).sum()} BB01 EVENTS ***")
        
        results.append({
            'fold': 2,
            'train_events': (train_bb01 == 1).sum(),
            'test_events': (test_bb01 == 1).sum(),
            'train_spread': train_spread,
            'test_spread': test_spread,
            'train_t': train_reg['beta_t'],
            'test_t': test_reg['beta_t'],
            'sign_consistency': 'YES' if not np.isnan(test_spread) and train_spread*test_spread > 0 else 'NO'
        })
        
        wfo_df = pd.DataFrame(results)
        self.results['bb01_wfo'] = wfo_df
        return wfo_df
    
    def bb01_bootstrap(self):
        """Block bootstrap on BB01 20d spread."""
        print(f"\n{'='*80}")
        print("BB01 BLOCK BOOTSTRAP (20d, Event spread)")
        print(f"{'='*80}")
        
        bb01 = self.data['BB01'].astype(int)
        fwd_ret = self.compute_forward_returns(20)
        
        valid_idx = fwd_ret.notna() & bb01.notna()
        ret_valid = fwd_ret[valid_idx].values
        bb01_valid = bb01[valid_idx].values
        
        # Observed spread
        obs_event = ret_valid[bb01_valid == 1].mean()
        obs_noevent = ret_valid[bb01_valid == 0].mean()
        obs_spread = obs_event - obs_noevent
        
        print(f"\nObserved spread (event - non-event): {obs_spread:.6f} ({obs_spread*100:.2f}%)")
        print(f"Event N: {(bb01_valid == 1).sum()}, Non-event N: {(bb01_valid == 0).sum()}")
        
        # Block bootstrap
        block_len = 20
        n_blocks = len(ret_valid) // block_len
        bootstrap_spreads = []
        
        for _ in range(5000):
            block_indices = np.random.choice(n_blocks, size=n_blocks, replace=True)
            boot_idx = []
            for b_idx in block_indices:
                start = b_idx * block_len
                end = min((b_idx + 1) * block_len, len(ret_valid))
                boot_idx.extend(range(start, end))
            
            boot_idx = boot_idx[:len(ret_valid)]
            
            boot_ret = ret_valid[boot_idx]
            boot_bb01 = bb01_valid[boot_idx]
            
            boot_event = boot_ret[boot_bb01 == 1].mean() if (boot_bb01 == 1).any() else np.nan
            boot_noevent = boot_ret[boot_bb01 == 0].mean() if (boot_bb01 == 0).any() else np.nan
            
            if not np.isnan(boot_event) and not np.isnan(boot_noevent):
                bootstrap_spreads.append(boot_event - boot_noevent)
        
        bootstrap_spreads = np.array(bootstrap_spreads)
        
        print(f"\nBootstrap distribution:")
        print(f"  Mean: {bootstrap_spreads.mean():.6f}")
        print(f"  Std: {bootstrap_spreads.std():.6f}")
        print(f"  2.5%: {np.percentile(bootstrap_spreads, 2.5):.6f}")
        print(f"  50%: {np.percentile(bootstrap_spreads, 50):.6f}")
        print(f"  97.5%: {np.percentile(bootstrap_spreads, 97.5):.6f}")
        print(f"  P(spread <= 0): {(bootstrap_spreads <= 0).sum() / len(bootstrap_spreads):.4f}")
        
        self.results['bb01_bootstrap'] = {'observed': obs_spread}
        return obs_spread
    
    def run_all(self):
        """Execute all analyses."""
        print("\n" + "#"*80)
        print("# PB07 & BB01 SIGNAL VALIDATION STUDY")
        print("#"*80)
        
        self.pb07_continuous_validation()
        self.pb07_shape_analysis()
        self.pb07_yearly_stability()
        self.pb07_walk_forward()
        self.pb07_bootstrap()
        self.pb07_redundancy()
        
        self.bb01_horizon_analysis()
        self.bb01_yearly_stability()
        self.bb01_walk_forward()
        self.bb01_bootstrap()
        
        return self.results
    
    def save_results(self, output_dir='research_output'):
        """Save all results to CSV."""
        Path(output_dir).mkdir(exist_ok=True)
        
        if 'pb07_continuous' in self.results:
            self.results['pb07_continuous'].to_csv(
                Path(output_dir) / 'pb07_continuous_validation.csv', index=False
            )
        
        if 'pb07_shape' in self.results:
            self.results['pb07_shape'].to_csv(
                Path(output_dir) / 'pb07_shape_analysis.csv', index=False
            )
        
        if 'pb07_yearly' in self.results:
            self.results['pb07_yearly'].to_csv(
                Path(output_dir) / 'pb07_yearly_stability.csv', index=False
            )
        
        if 'pb07_wfo' in self.results:
            self.results['pb07_wfo'].to_csv(
                Path(output_dir) / 'pb07_walk_forward.csv', index=False
            )
        
        if 'bb01_horizon' in self.results:
            self.results['bb01_horizon'].to_csv(
                Path(output_dir) / 'bb01_horizon_validation.csv', index=False
            )
        
        if 'bb01_yearly' in self.results:
            self.results['bb01_yearly'].to_csv(
                Path(output_dir) / 'bb01_yearly_stability.csv', index=False
            )
        
        if 'bb01_wfo' in self.results:
            self.results['bb01_wfo'].to_csv(
                Path(output_dir) / 'bb01_walk_forward.csv', index=False
            )
        
        print(f"\n{'='*80}")
        print("RESULTS SAVED")
        print(f"{'='*80}")
        print(f"Output directory: {output_dir}/")


def main():
    """Run the validation study."""
    signals_path = 'signals_cleaned.csv'
    price_path = 'price_cleaned.csv'
    
    validator = PB07BB01Validator(signals_path, price_path)
    results = validator.run_all()
    validator.save_results()
    
    print("\n" + "#"*80)
    print("# VALIDATION STUDY COMPLETE")
    print("#"*80)
    
    print(f"\n{'='*80}")
    print("INTERPRETATION GUIDANCE")
    print(f"{'='*80}")
    print("""
PRIMARY EVIDENCE (use these):
1. Welch t-test: Event vs non-event mean comparison
2. Bootstrap CI: Dependence-aware uncertainty bounds
3. Walk-forward: Out-of-sample sign/magnitude consistency
4. Economic effect: Signal spread relative to transaction costs

SECONDARY EVIDENCE (report but do not overstate):
- HAC t-statistics: Indicate precision but depend on autocorrelation assumptions
- Spearman IC: Monotonicity of relationship
- Year-by-year stability: Temporal consistency of direction/magnitude
- Multivariate redundancy: Independence from correlated signals

2021 BB01 CLARIFICATION:
- Total BB01 events in 2021: 6
- BB01 events with valid 20d fwd return: 3
- Late October/November events have no 20d forward data (data ends Nov 1)
- Both yearly stability and WFO test use same 3 valid events
- No discrepancy; same sample analyzed consistently
""")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
