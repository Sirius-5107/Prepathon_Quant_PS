"""
Strategy 2: Mean-Reversion Candidates Study & Implementation.

Rigorous comparison of mean-reversion candidates:
- Candidate A: BB03 short reversal (10d)
- Candidate B: BB04 long reversal (5d)
- Candidate C: PB07 extreme quintiles mean reversion
- Candidate D: Composite (only if incremental evidence)

NO parameter optimization.
NO threshold tuning.
Tests only pre-specified fixed hypotheses.

Primary evidence: effect size, Welch t, bootstrap, WFO, economic return.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import json
from datetime import timedelta

class MeanReversionCandidates:
    """Evaluate mean-reversion candidates using fixed hypotheses."""
    
    def __init__(self, signals_path, price_path):
        """Load and prepare data."""
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        print(f"\n{'='*80}")
        print("MEAN-REVERSION CANDIDATES STUDY")
        print(f"{'='*80}")
        print(f"Data loaded: {len(self.data)} rows")
        print(f"Date range: {self.data['date'].min().date()} to {self.data['date'].max().date()}")
        
        self.candidates = {}
        self.results = {}
    
    def compute_forward_returns(self, horizon):
        """Compute executable holding-period return: open[t] -> close[t+horizon]."""
        close_future = self.data['close'].shift(-horizon).values
        open_current = self.data['open'].values
        fwd_ret = (close_future - open_current) / open_current
        return pd.Series(fwd_ret, index=self.data.index)

    def causal_pb07_q1_signal(self, min_history=60):
        """Build Q1 using only observations strictly before each signal date."""
        pb07 = self.data['PB07']
        signal = pd.Series(0, index=self.data.index, dtype=int)
        threshold = pd.Series(np.nan, index=self.data.index, dtype=float)
        for i in range(len(pb07)):
            history = pb07.iloc[:i].dropna()
            if len(history) < min_history or pd.isna(pb07.iloc[i]):
                continue
            threshold.iloc[i] = history.quantile(0.20)
            signal.iloc[i] = int(pb07.iloc[i] <= threshold.iloc[i])
        return signal, threshold
    
    def welch_ttest(self, signal_series, returns_series, signal_value=1):
        """Welch t-test for signal vs non-signal returns."""
        valid_idx = signal_series.notna() & returns_series.notna()
        sig_valid = signal_series[valid_idx]
        ret_valid = returns_series[valid_idx]
        
        event_rets = ret_valid[sig_valid == signal_value]
        nonevent_rets = ret_valid[sig_valid != signal_value]
        
        if len(event_rets) < 3 or len(nonevent_rets) < 3:
            return {'t': np.nan, 'p': np.nan, 'spread': np.nan, 
                    'event_mean': np.nan, 'nonevent_mean': np.nan, 'n_events': len(event_rets)}
        
        t_stat, p_val = stats.ttest_ind(event_rets, nonevent_rets, equal_var=False)
        spread = event_rets.mean() - nonevent_rets.mean()
        
        return {
            't': t_stat,
            'p': p_val,
            'spread': spread,
            'event_mean': event_rets.mean(),
            'nonevent_mean': nonevent_rets.mean(),
            'n_events': len(event_rets),
            'n_nonevent': len(nonevent_rets)
        }
    
    def block_bootstrap_ci(self, signal_series, returns_series, signal_value=1, n_reps=5000, block_len=5):
        """Block bootstrap confidence interval for event spread."""
        valid_idx = signal_series.notna() & returns_series.notna()
        sig_valid = signal_series[valid_idx].values
        ret_valid = returns_series[valid_idx].values
        
        spreads = []
        n_blocks = len(ret_valid) // block_len
        np.random.seed(42)
        
        for _ in range(n_reps):
            block_idx = np.random.choice(n_blocks, size=n_blocks, replace=True)
            boot_idx = []
            for b in block_idx:
                start = b * block_len
                end = min((b+1) * block_len, len(ret_valid))
                boot_idx.extend(range(start, end))
            boot_idx = boot_idx[:len(ret_valid)]
            
            boot_sig = sig_valid[boot_idx]
            boot_ret = ret_valid[boot_idx]
            
            event_ret = boot_ret[boot_sig == signal_value].mean() if (boot_sig == signal_value).any() else np.nan
            nonevent_ret = boot_ret[boot_sig != signal_value].mean() if (boot_sig != signal_value).any() else np.nan
            
            if not np.isnan(event_ret) and not np.isnan(nonevent_ret):
                spreads.append(event_ret - nonevent_ret)
        
        spreads = np.array(spreads)
        return {
            'ci_lower': np.percentile(spreads, 2.5),
            'ci_upper': np.percentile(spreads, 97.5),
            'ci_includes_zero': np.percentile(spreads, 2.5) <= 0 <= np.percentile(spreads, 97.5),
            'mean': spreads.mean(),
            'std': spreads.std()
        }
    
    def candidate_a_bb03_short(self):
        """Candidate A: BB03 short reversal (10d horizon)."""
        print(f"\n{'='*80}")
        print("CANDIDATE A: BB03 Short Reversal (10d)")
        print(f"{'='*80}")
        print("Hypothesis: BB03=1 (overbought) → short signal → negative 10d return")
        
        horizon = 10
        fwd_ret = self.compute_forward_returns(horizon)
        
        # For short signal, we want NEGATIVE returns
        # So we reverse the sign: BB03=1 should correlate with negative returns
        bb03 = self.data['BB03'].astype(int)
        
        # Welch t-test
        welch_result = self.welch_ttest(bb03, fwd_ret, signal_value=1)
        
        # Bootstrap
        boot_result = self.block_bootstrap_ci(bb03, fwd_ret, signal_value=1, block_len=10)
        
        print(f"\nWelch t-test (BB03=1 vs non-BB03):")
        print(f"  Event mean: {welch_result['event_mean']*100:.4f}%")
        print(f"  Non-event mean: {welch_result['nonevent_mean']*100:.4f}%")
        print(f"  Spread: {welch_result['spread']*100:.4f}%")
        print(f"  t-stat: {welch_result['t']:.4f}, p-value: {welch_result['p']:.4f}")
        print(f"  N events: {welch_result['n_events']}")
        
        print(f"\nBlock bootstrap (5000 reps, block_len=10):")
        print(f"  95% CI: [{boot_result['ci_lower']*100:.4f}%, {boot_result['ci_upper']*100:.4f}%]")
        print(f"  Includes zero: {boot_result['ci_includes_zero']}")
        print(f"  Mean: {boot_result['mean']*100:.4f}%")
        
        # Yearly stability
        print(f"\nYear-by-year (10d):")
        yearly = []
        for year in sorted(self.data['year'].unique()):
            year_mask = self.data['year'] == year
            year_bb03 = bb03[year_mask]
            year_ret = fwd_ret[year_mask]
            
            year_welch = self.welch_ttest(year_bb03, year_ret, signal_value=1)
            yearly.append({
                'year': year,
                'n_events': year_welch['n_events'],
                'spread_pct': year_welch['spread'] * 100,
                'welch_t': year_welch['t'],
                'welch_p': year_welch['p']
            })
            print(f"  {year}: {year_welch['n_events']:2d} events, {year_welch['spread']*100:7.3f}%, t={year_welch['t']:7.3f}, p={year_welch['p']:.4f}")
        
        # WFO
        print(f"\nWalk-forward validation:")
        train_mask = self.data['year'].isin([2018, 2019])
        test_mask = self.data['year'] == 2020
        
        fold1_train_welch = self.welch_ttest(bb03[train_mask], fwd_ret[train_mask], signal_value=1)
        fold1_test_welch = self.welch_ttest(bb03[test_mask], fwd_ret[test_mask], signal_value=1)
        
        print(f"  Fold 1 (2018-2019 → 2020):")
        print(f"    Train: {fold1_train_welch['spread']*100:7.3f}%, n={fold1_train_welch['n_events']}")
        print(f"    Test:  {fold1_test_welch['spread']*100:7.3f}%, n={fold1_test_welch['n_events']}")
        print(f"    Sign consistency: {'YES' if fold1_train_welch['spread'] * fold1_test_welch['spread'] > 0 else 'NO'}")
        
        train_mask_2 = self.data['year'].isin([2018, 2019, 2020])
        test_mask_2 = self.data['year'] == 2021
        
        fold2_train_welch = self.welch_ttest(bb03[train_mask_2], fwd_ret[train_mask_2], signal_value=1)
        fold2_test_welch = self.welch_ttest(bb03[test_mask_2], fwd_ret[test_mask_2], signal_value=1)
        
        print(f"  Fold 2 (2018-2020 → 2021):")
        print(f"    Train: {fold2_train_welch['spread']*100:7.3f}%, n={fold2_train_welch['n_events']}")
        print(f"    Test:  {fold2_test_welch['spread']*100:7.3f}%, n={fold2_test_welch['n_events']}")
        print(f"    Sign consistency: {'YES' if fold2_train_welch['spread'] * fold2_test_welch['spread'] > 0 else 'NO'}")
        
        self.candidates['A_bb03_short_10d'] = {
            'name': 'BB03 Short Reversal (10d)',
            'horizon': horizon,
            'signal': 'BB03=1 → short',
            'welch': welch_result,
            'bootstrap': boot_result,
            'yearly': yearly,
            'wfo_fold1_train': fold1_train_welch['spread'],
            'wfo_fold1_test': fold1_test_welch['spread'],
            'wfo_fold2_train': fold2_train_welch['spread'],
            'wfo_fold2_test': fold2_test_welch['spread']
        }
        
        return welch_result, boot_result
    
    def candidate_b_bb04_long(self):
        """Candidate B: BB04 long reversal (5d horizon)."""
        print(f"\n{'='*80}")
        print("CANDIDATE B: BB04 Long Reversal (5d)")
        print(f"{'='*80}")
        print("Hypothesis: BB04=1 (oversold) → long signal → positive 5d return")
        
        horizon = 5
        fwd_ret = self.compute_forward_returns(horizon)
        bb04 = self.data['BB04'].astype(int)
        
        welch_result = self.welch_ttest(bb04, fwd_ret, signal_value=1)
        boot_result = self.block_bootstrap_ci(bb04, fwd_ret, signal_value=1, block_len=5)
        
        print(f"\nWelch t-test (BB04=1 vs non-BB04):")
        print(f"  Event mean: {welch_result['event_mean']*100:.4f}%")
        print(f"  Non-event mean: {welch_result['nonevent_mean']*100:.4f}%")
        print(f"  Spread: {welch_result['spread']*100:.4f}%")
        print(f"  t-stat: {welch_result['t']:.4f}, p-value: {welch_result['p']:.4f}")
        print(f"  N events: {welch_result['n_events']}")
        
        print(f"\nBlock bootstrap (5000 reps, block_len=5):")
        print(f"  95% CI: [{boot_result['ci_lower']*100:.4f}%, {boot_result['ci_upper']*100:.4f}%]")
        print(f"  Includes zero: {boot_result['ci_includes_zero']}")
        print(f"  Mean: {boot_result['mean']*100:.4f}%")
        
        print(f"\nYear-by-year (5d):")
        yearly = []
        for year in sorted(self.data['year'].unique()):
            year_mask = self.data['year'] == year
            year_bb04 = bb04[year_mask]
            year_ret = fwd_ret[year_mask]
            
            year_welch = self.welch_ttest(year_bb04, year_ret, signal_value=1)
            yearly.append({
                'year': year,
                'n_events': year_welch['n_events'],
                'spread_pct': year_welch['spread'] * 100,
                'welch_t': year_welch['t'],
                'welch_p': year_welch['p']
            })
            print(f"  {year}: {year_welch['n_events']:2d} events, {year_welch['spread']*100:7.3f}%, t={year_welch['t']:7.3f}, p={year_welch['p']:.4f}")
        
        print(f"\nWalk-forward validation:")
        train_mask = self.data['year'].isin([2018, 2019])
        test_mask = self.data['year'] == 2020
        
        fold1_train_welch = self.welch_ttest(bb04[train_mask], fwd_ret[train_mask], signal_value=1)
        fold1_test_welch = self.welch_ttest(bb04[test_mask], fwd_ret[test_mask], signal_value=1)
        
        print(f"  Fold 1 (2018-2019 → 2020):")
        print(f"    Train: {fold1_train_welch['spread']*100:7.3f}%, n={fold1_train_welch['n_events']}")
        print(f"    Test:  {fold1_test_welch['spread']*100:7.3f}%, n={fold1_test_welch['n_events']}")
        print(f"    Sign consistency: {'YES' if fold1_train_welch['spread'] * fold1_test_welch['spread'] > 0 else 'NO'}")
        
        train_mask_2 = self.data['year'].isin([2018, 2019, 2020])
        test_mask_2 = self.data['year'] == 2021
        
        fold2_train_welch = self.welch_ttest(bb04[train_mask_2], fwd_ret[train_mask_2], signal_value=1)
        fold2_test_welch = self.welch_ttest(bb04[test_mask_2], fwd_ret[test_mask_2], signal_value=1)
        
        print(f"  Fold 2 (2018-2020 → 2021):")
        print(f"    Train: {fold2_train_welch['spread']*100:7.3f}%, n={fold2_train_welch['n_events']}")
        print(f"    Test:  {fold2_test_welch['spread']*100:7.3f}%, n={fold2_test_welch['n_events']}")
        print(f"    Sign consistency: {'YES' if fold2_train_welch['spread'] * fold2_test_welch['spread'] > 0 else 'NO'}")
        
        self.candidates['B_bb04_long_5d'] = {
            'name': 'BB04 Long Reversal (5d)',
            'horizon': horizon,
            'signal': 'BB04=1 → long',
            'welch': welch_result,
            'bootstrap': boot_result,
            'yearly': yearly,
            'wfo_fold1_train': fold1_train_welch['spread'],
            'wfo_fold1_test': fold1_test_welch['spread'],
            'wfo_fold2_train': fold2_train_welch['spread'],
            'wfo_fold2_test': fold2_test_welch['spread']
        }
        
        return welch_result, boot_result
    
    def candidate_c_pb07_quintiles(self):
        """Candidate C: PB07 extreme quintile mean reversion (20d)."""
        print(f"\n{'='*80}")
        print("CANDIDATE C: PB07 Extreme Quintile Mean Reversion (20d)")
        print(f"{'='*80}")
        print("Hypothesis: PB07 historical Q1 (bottom quintile) → long (mean reversion)")
        
        horizon = 20
        fwd_ret = self.compute_forward_returns(horizon)
        pb07 = self.data['PB07']
        
        # Causal Q1: threshold at t uses only observations strictly before t.
        pb07_q1_signal, pb07_threshold = self.causal_pb07_q1_signal(min_history=60)
        
        welch_result = self.welch_ttest(pb07_q1_signal, fwd_ret, signal_value=1)
        boot_result = self.block_bootstrap_ci(pb07_q1_signal, fwd_ret, signal_value=1, block_len=20)
        
        print(f"\nWelch t-test (PB07 Q1 vs others):")
        print(f"  Event mean (Q1): {welch_result['event_mean']*100:.4f}%")
        print(f"  Non-event mean: {welch_result['nonevent_mean']*100:.4f}%")
        print(f"  Spread: {welch_result['spread']*100:.4f}%")
        print(f"  t-stat: {welch_result['t']:.4f}, p-value: {welch_result['p']:.4f}")
        print(f"  N events: {welch_result['n_events']}")
        
        print(f"\nBlock bootstrap (5000 reps, block_len=20):")
        print(f"  95% CI: [{boot_result['ci_lower']*100:.4f}%, {boot_result['ci_upper']*100:.4f}%]")
        print(f"  Includes zero: {boot_result['ci_includes_zero']}")
        print(f"  Mean: {boot_result['mean']*100:.4f}%")
        
        print(f"\nYear-by-year (20d, Q1):")
        yearly = []
        for year in sorted(self.data['year'].unique()):
            year_mask = self.data['year'] == year
            year_sig = pb07_q1_signal[year_mask]
            year_ret = fwd_ret[year_mask]
            
            year_welch = self.welch_ttest(year_sig, year_ret, signal_value=1)
            yearly.append({
                'year': year,
                'n_events': year_welch['n_events'],
                'spread_pct': year_welch['spread'] * 100,
                'welch_t': year_welch['t'],
                'welch_p': year_welch['p']
            })
            print(f"  {year}: {year_welch['n_events']:2d} events, {year_welch['spread']*100:7.3f}%, t={year_welch['t']:7.3f}, p={year_welch['p']:.4f}")
        
        print(f"\nWalk-forward validation:")
        train_mask = self.data['year'].isin([2018, 2019])
        test_mask = self.data['year'] == 2020
        
        fold1_train_welch = self.welch_ttest(pb07_q1_signal[train_mask], fwd_ret[train_mask], signal_value=1)
        fold1_test_welch = self.welch_ttest(pb07_q1_signal[test_mask], fwd_ret[test_mask], signal_value=1)
        
        print(f"  Fold 1 (2018-2019 → 2020):")
        print(f"    Train: {fold1_train_welch['spread']*100:7.3f}%, n={fold1_train_welch['n_events']}")
        print(f"    Test:  {fold1_test_welch['spread']*100:7.3f}%, n={fold1_test_welch['n_events']}")
        print(f"    Sign consistency: {'YES' if fold1_train_welch['spread'] * fold1_test_welch['spread'] > 0 else 'NO'}")
        
        train_mask_2 = self.data['year'].isin([2018, 2019, 2020])
        test_mask_2 = self.data['year'] == 2021
        
        fold2_train_welch = self.welch_ttest(pb07_q1_signal[train_mask_2], fwd_ret[train_mask_2], signal_value=1)
        fold2_test_welch = self.welch_ttest(pb07_q1_signal[test_mask_2], fwd_ret[test_mask_2], signal_value=1)
        
        print(f"  Fold 2 (2018-2020 → 2021):")
        print(f"    Train: {fold2_train_welch['spread']*100:7.3f}%, n={fold2_train_welch['n_events']}")
        print(f"    Test:  {fold2_test_welch['spread']*100:7.3f}%, n={fold2_test_welch['n_events']}")
        print(f"    Sign consistency: {'YES' if fold2_train_welch['spread'] * fold2_test_welch['spread'] > 0 else 'NO'}")
        
        self.candidates['C_pb07_q1_long_20d'] = {
            'name': 'PB07 Q1 Long Reversal (20d)',
            'horizon': horizon,
            'signal': 'Causal PB07 Q1 (historical bottom quintile) → long',
            'welch': welch_result,
            'bootstrap': boot_result,
            'yearly': yearly,
            'wfo_fold1_train': fold1_train_welch['spread'],
            'wfo_fold1_test': fold1_test_welch['spread'],
            'wfo_fold2_train': fold2_train_welch['spread'],
            'wfo_fold2_test': fold2_test_welch['spread']
        }
        
        return welch_result, boot_result
    
    def run_candidate_comparison(self):
        """Run all candidate evaluations."""
        print("\n" + "#"*80)
        print("# MEAN-REVERSION CANDIDATES EVALUATION")
        print("#"*80)
        
        self.candidate_a_bb03_short()
        self.candidate_b_bb04_long()
        self.candidate_c_pb07_quintiles()
        
        return self.candidates
    
    def save_candidate_comparison(self, output_dir='research_output'):
        """Save candidate comparison CSV."""
        Path(output_dir).mkdir(exist_ok=True)
        
        rows = []
        for key, cand in self.candidates.items():
            welch = cand['welch']
            boot = cand['bootstrap']
            
            rows.append({
                'Candidate': cand['name'],
                'Signal': cand['signal'],
                'Horizon': cand['horizon'],
                'N_Events': welch['n_events'],
                'Spread_pct': welch['spread'] * 100,
                'Welch_t': welch['t'],
                'Welch_p': welch['p'],
                'Bootstrap_CI_Lower_pct': boot['ci_lower'] * 100,
                'Bootstrap_CI_Upper_pct': boot['ci_upper'] * 100,
                'CI_Includes_Zero': boot['ci_includes_zero'],
                'WFO_Fold1_Train_pct': cand['wfo_fold1_train'] * 100,
                'WFO_Fold1_Test_pct': cand['wfo_fold1_test'] * 100,
                'WFO_Fold1_Sign_Match': 'YES' if cand['wfo_fold1_train'] * cand['wfo_fold1_test'] > 0 else 'NO',
                'WFO_Fold2_Train_pct': cand['wfo_fold2_train'] * 100,
                'WFO_Fold2_Test_pct': cand['wfo_fold2_test'] * 100,
                'WFO_Fold2_Sign_Match': 'YES' if cand['wfo_fold2_train'] * cand['wfo_fold2_test'] > 0 else 'NO'
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(Path(output_dir) / 'strategy_02_candidates.csv', index=False)
        
        print(f"\nCandidate comparison saved to {output_dir}/strategy_02_candidates.csv")
        print("\n" + "="*80)
        print("CANDIDATE SUMMARY")
        print("="*80)
        print(df.to_string(index=False))
        
        return df


def main():
    """Run candidate comparison."""
    signals_path = 'signals_cleaned.csv'
    price_path = 'price_cleaned.csv'
    
    study = MeanReversionCandidates(signals_path, price_path)
    candidates = study.run_candidate_comparison()
    study.save_candidate_comparison()
    
    print("\n" + "#"*80)
    print("# CANDIDATE COMPARISON COMPLETE")
    print("#"*80)
    
    # Build Strategy 2 from Candidate C
    print("\n" + "#"*80)
    print("# STRATEGY 2: PB07 Q1 MEAN REVERSION EXECUTABLE")
    print("#"*80)
    
    strategy = PB07MeanReversionStrategy(signals_path, price_path)
    strategy.find_entry_exits(horizon=20)
    strategy.compute_equity_curve()
    strategy.calculate_metrics()
    strategy.calculate_yearly_performance()
    strategy.calculate_wfo_performance()
    strategy.print_summary()
    strategy.save_results()


class PB07MeanReversionStrategy:
    """PB07 Q1 mean reversion strategy with no-overlap position enforcement."""
    
    def __init__(self, signals_path, price_path):
        """Load and prepare data."""
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        self.trades = []
        self.equity = []
        self.results = {}
        
        print(f"\n{'='*80}")
        print("PB07 Q1 MEAN REVERSION STRATEGY")
        print(f"{'='*80}")
        print(f"Data loaded: {len(self.data)} rows")
        print(f"Date range: {self.data['date'].min().date()} to {self.data['date'].max().date()}")
    
    def find_entry_exits(self, horizon=20):
        """
        Find all PB07 Q1 events and their corresponding forward returns.
        Enforces no-overlap rule.
        """
        print(f"\n{'='*80}")
        print(f"FINDING ENTRIES & EXITS (Holding period: {horizon}d)")
        print(f"{'='*80}")
        
        pb07 = self.data['PB07']
        
        # Causal Q1: each date's threshold uses only prior observations.
        pb07_signal, pb07_threshold = self.causal_pb07_q1_signal(min_history=60)
        self.data['pb07_q1_threshold'] = pb07_threshold
        self.data['pb07_q1_signal'] = pb07_signal
        
        # Find all Q1 events (using t-1 close convention)
        all_events = []
        for i in range(1, len(self.data)):
            if pb07_signal.iloc[i-1] == 1:
                all_events.append(i)
        
        print(f"\nTotal PB07 Q1 signal events: {len(all_events)}")
        
        # Enforce no-overlap rule
        open_positions = {}
        valid_entries = []
        skipped = 0
        
        for entry_idx in all_events:
            position_open = False
            for ex_idx in open_positions.values():
                if entry_idx < ex_idx:
                    position_open = True
                    skipped += 1
                    break
            
            if not position_open:
                exit_idx = min(entry_idx + horizon, len(self.data) - 1)
                open_positions[entry_idx] = exit_idx
                valid_entries.append(entry_idx)
        
        print(f"Events skipped (position overlap): {skipped}")
        print(f"Valid non-overlapping entries: {len(valid_entries)}")
        
        # Extract trades
        for entry_idx in valid_entries:
            exit_idx = open_positions[entry_idx]
            
            entry_date = self.data.iloc[entry_idx]['date']
            exit_date = self.data.iloc[exit_idx]['date']
            entry_price = self.data.iloc[entry_idx]['open']
            exit_price = self.data.iloc[exit_idx]['close']
            
            gross_return = (exit_price - entry_price) / entry_price
            entry_cost = 0.0005
            exit_cost = 0.0005
            total_cost = entry_cost + exit_cost
            net_return = gross_return - total_cost
            
            holding_days = (exit_date - entry_date).days
            
            trade = {
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'gross_return': gross_return,
                'entry_cost': entry_cost,
                'exit_cost': exit_cost,
                'total_cost': total_cost,
                'net_return': net_return,
                'holding_days': holding_days
            }
            self.trades.append(trade)
        
        self.results['all_events'] = len(all_events)
        self.results['skipped_events'] = skipped
        self.results['executable_trades'] = len(valid_entries)
        
        return valid_entries
    
    def compute_equity_curve(self):
        """Compute cumulative equity curve."""
        equity = [1.0]
        for trade in self.trades:
            equity.append(equity[-1] * (1 + trade['net_return']))
        self.equity = equity
        return equity
    
    def calculate_metrics(self):
        """Calculate strategy performance metrics."""
        if len(self.trades) == 0:
            print("\nNo trades executed.")
            return {}
        
        returns = np.array([t['net_return'] for t in self.trades])
        gross_returns = np.array([t['gross_return'] for t in self.trades])
        
        total_return = self.equity[-1] - 1.0
        n_trades = len(self.trades)
        
        total_days = (self.trades[-1]['exit_date'] - self.trades[0]['entry_date']).days
        years = total_days / 365.25
        annualized_return = (self.equity[-1] ** (1 / years)) - 1 if years > 0 else 0
        
        daily_rets = []
        for i in range(1, len(self.equity)):
            daily_ret = (self.equity[i] - self.equity[i-1]) / self.equity[i-1]
            daily_rets.append(daily_ret)
        
        daily_vol = np.std(daily_rets) if len(daily_rets) > 0 else 0
        annualized_vol = daily_vol * np.sqrt(252)
        
        sharpe = (annualized_return / annualized_vol) if annualized_vol > 0 else 0
        
        running_max = np.maximum.accumulate(self.equity)
        drawdown = (np.array(self.equity) - running_max) / running_max
        max_dd = np.min(drawdown)
        
        calmar = (annualized_return / abs(max_dd)) if max_dd != 0 else 0
        
        winners = (returns > 0).sum()
        losers = (returns < 0).sum()
        win_rate = winners / n_trades if n_trades > 0 else 0
        
        gross_wins = np.maximum(returns, 0).sum()
        gross_losses = np.abs(np.minimum(returns, 0)).sum()
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else np.inf
        
        avg_return = returns.mean()
        median_return = np.median(returns)
        
        best_trade = returns.max()
        worst_trade = returns.min()
        avg_winner = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loser = returns[returns < 0].mean() if (returns < 0).any() else 0
        
        avg_hold = np.mean([t['holding_days'] for t in self.trades])
        
        total_costs = np.sum([t['total_cost'] for t in self.trades])
        gross_pnl = np.sum(gross_returns)
        net_pnl = np.sum(returns)
        
        metrics = {
            'total_return_pct': total_return * 100,
            'annualized_return_pct': annualized_return * 100,
            'annualized_volatility_pct': annualized_vol * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd * 100,
            'calmar_ratio': calmar,
            'n_trades': n_trades,
            'win_rate_pct': win_rate * 100,
            'avg_trade_pct': avg_return * 100,
            'median_trade_pct': median_return * 100,
            'profit_factor': profit_factor,
            'best_trade_pct': best_trade * 100,
            'worst_trade_pct': worst_trade * 100,
            'avg_winner_pct': avg_winner * 100,
            'avg_loser_pct': avg_loser * 100,
            'avg_holding_days': avg_hold,
            'total_transaction_costs_pct': total_costs * 100,
            'gross_pnl_pct': gross_pnl * 100,
            'net_pnl_pct': net_pnl * 100,
            'period_start': self.trades[0]['entry_date'].strftime('%Y-%m-%d'),
            'period_end': self.trades[-1]['exit_date'].strftime('%Y-%m-%d'),
            'total_period_days': total_days,
            'winners': int(winners),
            'losers': int(losers)
        }
        
        self.results['metrics'] = metrics
        return metrics
    
    def calculate_yearly_performance(self):
        """Calculate performance by year."""
        yearly_results = []
        
        for year in sorted(self.data['year'].unique()):
            year_trades = [t for t in self.trades if t['entry_date'].year == year]
            
            if len(year_trades) == 0:
                continue
            
            returns = np.array([t['net_return'] for t in year_trades])
            gross_returns = np.array([t['gross_return'] for t in year_trades])
            
            result = {
                'year': year,
                'n_trades': len(year_trades),
                'total_return_pct': returns.sum() * 100,
                'avg_trade_pct': returns.mean() * 100,
                'win_rate_pct': (returns > 0).sum() / len(year_trades) * 100,
                'best_trade_pct': returns.max() * 100,
                'worst_trade_pct': returns.min() * 100,
                'gross_pnl_pct': gross_returns.sum() * 100
            }
            yearly_results.append(result)
        
        yearly_df = pd.DataFrame(yearly_results)
        self.results['yearly'] = yearly_df
        return yearly_df
    
    def calculate_wfo_performance(self):
        """Walk-forward validation."""
        wfo_results = []
        
        # Fold 1
        train_trades_1 = [t for t in self.trades if t['entry_date'].year in [2018, 2019]]
        test_trades_1 = [t for t in self.trades if t['entry_date'].year == 2020]
        
        train_ret_1 = np.array([t['net_return'] for t in train_trades_1])
        test_ret_1 = np.array([t['net_return'] for t in test_trades_1])
        
        result_1 = {
            'fold': 1,
            'train_period': '2018-2019',
            'test_period': '2020',
            'train_trades': len(train_trades_1),
            'test_trades': len(test_trades_1),
            'train_return_pct': train_ret_1.sum() * 100,
            'test_return_pct': test_ret_1.sum() * 100,
            'train_avg_pct': train_ret_1.mean() * 100,
            'test_avg_pct': test_ret_1.mean() * 100,
            'train_win_rate_pct': (train_ret_1 > 0).sum() / len(train_trades_1) * 100 if len(train_trades_1) > 0 else 0,
            'test_win_rate_pct': (test_ret_1 > 0).sum() / len(test_trades_1) * 100 if len(test_trades_1) > 0 else 0,
            'sign_consistency': 'YES' if train_ret_1.sum() * test_ret_1.sum() > 0 else 'NO'
        }
        wfo_results.append(result_1)
        
        # Fold 2
        train_trades_2 = [t for t in self.trades if t['entry_date'].year in [2018, 2019, 2020]]
        test_trades_2 = [t for t in self.trades if t['entry_date'].year == 2021]
        
        train_ret_2 = np.array([t['net_return'] for t in train_trades_2])
        test_ret_2 = np.array([t['net_return'] for t in test_trades_2])
        
        result_2 = {
            'fold': 2,
            'train_period': '2018-2020',
            'test_period': '2021',
            'train_trades': len(train_trades_2),
            'test_trades': len(test_trades_2),
            'train_return_pct': train_ret_2.sum() * 100,
            'test_return_pct': test_ret_2.sum() * 100,
            'train_avg_pct': train_ret_2.mean() * 100,
            'test_avg_pct': test_ret_2.mean() * 100,
            'train_win_rate_pct': (train_ret_2 > 0).sum() / len(train_trades_2) * 100 if len(train_trades_2) > 0 else 0,
            'test_win_rate_pct': (test_ret_2 > 0).sum() / len(test_trades_2) * 100 if len(test_trades_2) > 0 else 0,
            'sign_consistency': 'YES' if train_ret_2.sum() * test_ret_2.sum() > 0 else 'NO'
        }
        wfo_results.append(result_2)
        
        wfo_df = pd.DataFrame(wfo_results)
        self.results['wfo'] = wfo_df
        return wfo_df
    
    def print_summary(self):
        """Print detailed summary."""
        print(f"\n{'='*80}")
        print("EXECUTABLE STRATEGY SUMMARY (20d holding period)")
        print(f"{'='*80}")
        
        print(f"\nSignal-level validation (all events):")
        print(f"  Total PB07 Q1 events: {self.results['all_events']}")
        print(f"  Q1 threshold: expanding historical 20th percentile, prior observations only (min 60 observations)")
        
        print(f"\nExecutable strategy (no overlaps):")
        print(f"  Events skipped (position overlap): {self.results['skipped_events']}")
        print(f"  Executable trades: {self.results['executable_trades']}")
        
        if len(self.trades) > 0:
            m = self.results['metrics']
            print(f"\nPerformance metrics:")
            print(f"  Total return: {m['total_return_pct']:.2f}%")
            print(f"  Annualized return: {m['annualized_return_pct']:.2f}%")
            print(f"  Annualized volatility: {m['annualized_volatility_pct']:.2f}%")
            print(f"  Sharpe ratio: {m['sharpe_ratio']:.4f}")
            print(f"  Max drawdown: {m['max_drawdown_pct']:.2f}%")
            print(f"  Calmar ratio: {m['calmar_ratio']:.4f}")
            print(f"  Win rate: {m['win_rate_pct']:.1f}% ({m['winners']} wins, {m['losers']} losses)")
            print(f"  Profit factor: {m['profit_factor']:.4f}")
            print(f"  Avg trade: {m['avg_trade_pct']:.2f}%")
            print(f"  Best/worst: {m['best_trade_pct']:.2f}% / {m['worst_trade_pct']:.2f}%")
            print(f"  Avg holding: {m['avg_holding_days']:.1f} days")
            print(f"  Transaction costs: {m['total_transaction_costs_pct']:.2f}%")
            print(f"  Gross PnL: {m['gross_pnl_pct']:.2f}%")
            print(f"  Net PnL: {m['net_pnl_pct']:.2f}%")
            
            if 'yearly' in self.results and len(self.results['yearly']) > 0:
                print(f"\nYear-by-year:")
                for _, row in self.results['yearly'].iterrows():
                    print(f"  {int(row['year'])}: {int(row['n_trades'])} trades, {row['total_return_pct']:.2f}% return, {row['win_rate_pct']:.1f}% win rate")
            
            if 'wfo' in self.results and len(self.results['wfo']) > 0:
                print(f"\nWalk-forward validation:")
                for _, row in self.results['wfo'].iterrows():
                    print(f"  Fold {int(row['fold'])} ({row['train_period']} → {row['test_period']}):")
                    print(f"    Train: {int(row['train_trades'])} trades, {row['train_return_pct']:.2f}%")
                    print(f"    Test:  {int(row['test_trades'])} trades, {row['test_return_pct']:.2f}%")
                    print(f"    Sign consistency: {row['sign_consistency']}")
    
    def save_results(self, output_dir='research_output'):
        """Save all results to files."""
        Path(output_dir).mkdir(exist_ok=True)
        
        if len(self.trades) > 0:
            # Trade-level CSV
            trades_df = pd.DataFrame(self.trades)
            trades_df = trades_df[[
                'entry_date', 'exit_date', 'entry_price', 'exit_price',
                'gross_return', 'entry_cost', 'exit_cost', 'net_return', 'holding_days'
            ]]
            trades_df['gross_return'] *= 100
            trades_df['entry_cost'] *= 100
            trades_df['exit_cost'] *= 100
            trades_df['net_return'] *= 100
            trades_df.to_csv(Path(output_dir) / 'strategy_02_trades.csv', index=False)
            
            # Equity curve CSV
            equity_df = pd.DataFrame({
                'trade_n': range(len(self.equity)),
                'equity': self.equity,
                'return_pct': (np.array(self.equity) - 1) * 100
            })
            equity_df.to_csv(Path(output_dir) / 'strategy_02_equity.csv', index=False)
        
        # Metrics JSON
        metrics_json = {
            'signal_events': self.results['all_events'],
            'skipped_events': self.results['skipped_events'],
            'executable_trades': self.results['executable_trades'],
            'metrics': self.results['metrics']
        }
        with open(Path(output_dir) / 'strategy_02_metrics.json', 'w') as f:
            json.dump(metrics_json, f, indent=2, default=str)
        
        # Yearly results
        if 'yearly' in self.results and len(self.results['yearly']) > 0:
            self.results['yearly'].to_csv(
                Path(output_dir) / 'strategy_02_yearly.csv', index=False
            )
        
        # WFO results
        if 'wfo' in self.results and len(self.results['wfo']) > 0:
            self.results['wfo'].to_csv(
                Path(output_dir) / 'strategy_02_wfo.csv', index=False
            )
        
        print(f"\nResults saved to {output_dir}/")


if __name__ == '__main__':
    main()
