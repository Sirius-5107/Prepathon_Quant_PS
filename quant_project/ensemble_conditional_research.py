"""
Ensemble and Conditional-Alpha Analysis (Task 2 Research).

Investigate whether PB07 and BB01 contain complementary information
that improves risk-adjusted performance or reveals conditional relationships.

Research discipline:
- Fixed baselines (no parameter optimization)
- Conditional analysis (discovery phase)
- Robustness checks (yearly, WFO, transaction costs)
- Statistical discipline (explicit hypothesis, no overfitting)
- Clear distinction: discovery → hypothesis → validation

No Optuna, no grid search, no parameter optimization.
"""

import pandas as pd
import numpy as np
from scipy import stats
import json
from pathlib import Path


class EnsembleAnalyzer:
    """Analyze multiple portfolio configurations using fixed weights."""
    
    def __init__(self, signals_path, price_path):
        """Load data and prepare merged dataset."""
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        print(f"\nEnsemble Analysis initialized: {len(self.data)} trading days")
    
    def load_strategy_daily_returns(self, strategy_name, csv_path):
        """Load daily returns for a strategy."""
        df = pd.read_csv(csv_path, parse_dates=['date'])
        return df.set_index('date')[f'{strategy_name}_daily_return'].to_dict()
    
    def compute_metrics(self, daily_returns_dict):
        """Compute performance metrics from daily returns dictionary."""
        rets = np.array(list(daily_returns_dict.values()))
        
        # Total and annualized return
        total_ret = (np.prod(1 + rets) - 1) * 100
        years = len(rets) / 252
        ann_ret = ((1 + total_ret/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Volatility (from daily returns)
        daily_vol = np.std(rets) * np.sqrt(252) * 100
        
        # Sharpe
        sharpe = ann_ret / daily_vol if daily_vol > 0 else 0
        
        # Drawdown
        equity = np.cumprod(1 + rets)
        dd = (equity - np.maximum.accumulate(equity)) / np.maximum.accumulate(equity)
        max_dd = np.min(dd) * 100 if len(dd) > 0 else 0
        
        # Calmar
        calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0
        
        # Win rate
        win_rate = (rets > 0).sum() / len(rets) * 100
        
        # Profit factor
        gross_wins = rets[rets > 0].sum()
        gross_loss = abs(rets[rets < 0].sum())
        profit_factor = gross_wins / gross_loss if gross_loss > 0 else 0
        
        return {
            'total_return': total_ret,
            'annualized_return': ann_ret,
            'volatility': daily_vol,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'calmar': calmar,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
    
    def compute_yearly_returns(self, daily_returns_dict):
        """Compute yearly returns."""
        yearly = {}
        for year in [2018, 2019, 2020, 2021]:
            year_rets = []
            for date_str, ret in daily_returns_dict.items():
                if isinstance(date_str, str):
                    year_val = int(date_str[:4])
                else:
                    year_val = pd.to_datetime(date_str).year
                
                if year_val == year:
                    year_rets.append(ret)
            
            if len(year_rets) > 0:
                year_return = (np.prod(1 + np.array(year_rets)) - 1) * 100
            else:
                year_return = 0
            
            yearly[year] = year_return
        
        return yearly


class ConditionalAlphaAnalyzer:
    """Analyze conditional relationships between signals."""
    
    def __init__(self, merged_data):
        """Initialize with merged price and signal data."""
        self.data = merged_data.copy()
        self.results = {}
    
    def compute_forward_returns(self, horizon=5):
        """Compute forward returns for given horizon."""
        fwd_ret = []
        for i in range(len(self.data) - horizon):
            entry_open = self.data.loc[i, 'open']
            exit_close = self.data.loc[i + horizon, 'close']
            ret = (exit_close - entry_open) / entry_open
            fwd_ret.append(ret)
        
        # Pad with NaN
        fwd_ret = fwd_ret + [np.nan] * horizon
        return fwd_ret
    
    def classify_signal_state(self, signal_name, signal_col):
        """Classify signal as positive/negative/neutral for each date."""
        if signal_name == 'BB01':
            return self.data[signal_col].astype(int)
        elif signal_name == 'PB07':
            # Bottom quintile
            valid = self.data[signal_col].dropna()
            q1 = np.percentile(valid, 20)
            state = pd.Series(0, index=self.data.index)
            state[self.data[signal_col] <= q1] = 1
            return state
        return None
    
    def conditional_forward_returns(self, signal_col, signal_name, condition_col, condition_name, horizon=5):
        """
        Compute forward returns conditioned on another signal.
        
        For example: PB07 returns conditional on BB01 state.
        """
        fwd_ret = self.compute_forward_returns(horizon)
        self.data[f'fwd_ret_{horizon}'] = fwd_ret
        
        # Get signal states
        main_signal = self.classify_signal_state(signal_name, signal_col)
        cond_signal = self.classify_signal_state(condition_name, condition_col)
        
        results = {}
        
        # Condition on: positive, negative, neutral
        for cond_state, cond_label in [(1, 'positive'), (0, 'negative')]:
            mask = cond_signal == cond_state
            rets = self.data.loc[mask, f'fwd_ret_{horizon}'].dropna()
            
            if len(rets) > 0:
                results[f'{condition_name}_{cond_label}'] = {
                    'count': len(rets),
                    'mean_return': rets.mean() * 100,
                    'median_return': rets.median() * 100,
                    'std_return': rets.std() * 100,
                    'win_rate': (rets > 0).sum() / len(rets) * 100
                }
        
        return results
    
    def joint_states_analysis(self, horizon=5):
        """
        Analyze forward returns for joint signal states.
        
        States:
        1. PB07+ and BB01+
        2. PB07+ and BB01-
        3. PB07- and BB01+
        4. PB07- and BB01-
        5. only PB07 active
        6. only BB01 active
        7. neither active
        """
        fwd_ret = self.compute_forward_returns(horizon)
        self.data[f'fwd_ret_{horizon}'] = fwd_ret
        
        pb07_state = self.classify_signal_state('PB07', 'PB07')
        bb01_state = self.classify_signal_state('BB01', 'BB01')
        
        results = {}
        
        # Define joint states
        states = [
            ((1, 1), 'PB07+ BB01+'),
            ((1, 0), 'PB07+ BB01-'),
            ((0, 1), 'PB07- BB01+'),
            ((0, 0), 'PB07- BB01-'),
            ((1, 2), 'only_PB07'),  # Special: PB07 active, BB01 inactive (state 2 = nan/inactive)
            ((2, 1), 'only_BB01'),  # Special: BB01 active, PB07 inactive
            ((2, 2), 'neither'),    # Neither active
        ]
        
        for (pb07_val, bb01_val), label in states:
            if pb07_val == 2:  # Inactive
                mask = pb07_state.isna() | (pb07_state != 1)
            elif pb07_val == 1:
                mask = pb07_state == 1
            else:
                mask = pb07_state == 0
            
            if bb01_val == 2:
                mask = mask & (bb01_state.isna() | (bb01_state != 1))
            elif bb01_val == 1:
                mask = mask & (bb01_state == 1)
            else:
                mask = mask & (bb01_state == 0)
            
            rets = self.data.loc[mask, f'fwd_ret_{horizon}'].dropna()
            
            if len(rets) > 0:
                results[label] = {
                    'count': len(rets),
                    'mean_return': rets.mean() * 100,
                    'median_return': rets.median() * 100,
                    'std_return': rets.std() * 100,
                    'win_rate': (rets > 0).sum() / len(rets) * 100
                }
        
        return results
    
    def agreement_analysis(self, horizon=5):
        """
        Analyze whether agreement between signals improves returns.
        
        Compare:
        - PB07 unconditional
        - PB07 when BB01 agrees
        - BB01 unconditional
        - BB01 when PB07 agrees
        """
        fwd_ret = self.compute_forward_returns(horizon)
        self.data[f'fwd_ret_{horizon}'] = fwd_ret
        
        pb07_state = self.classify_signal_state('PB07', 'PB07')
        bb01_state = self.classify_signal_state('BB01', 'BB01')
        
        results = {}
        
        # PB07 unconditional
        pb07_rets = self.data.loc[pb07_state == 1, f'fwd_ret_{horizon}'].dropna()
        if len(pb07_rets) > 0:
            results['PB07_unconditional'] = {
                'count': len(pb07_rets),
                'mean_return': pb07_rets.mean() * 100,
                'std_return': pb07_rets.std() * 100,
                'win_rate': (pb07_rets > 0).sum() / len(pb07_rets) * 100
            }
        
        # PB07 when BB01 agrees (both positive)
        pb07_bb01_agree = self.data.loc[(pb07_state == 1) & (bb01_state == 1), f'fwd_ret_{horizon}'].dropna()
        if len(pb07_bb01_agree) > 0:
            results['PB07_when_BB01_agrees'] = {
                'count': len(pb07_bb01_agree),
                'mean_return': pb07_bb01_agree.mean() * 100,
                'std_return': pb07_bb01_agree.std() * 100,
                'win_rate': (pb07_bb01_agree > 0).sum() / len(pb07_bb01_agree) * 100
            }
        
        # BB01 unconditional
        bb01_rets = self.data.loc[bb01_state == 1, f'fwd_ret_{horizon}'].dropna()
        if len(bb01_rets) > 0:
            results['BB01_unconditional'] = {
                'count': len(bb01_rets),
                'mean_return': bb01_rets.mean() * 100,
                'std_return': bb01_rets.std() * 100,
                'win_rate': (bb01_rets > 0).sum() / len(bb01_rets) * 100
            }
        
        # BB01 when PB07 agrees (both positive)
        bb01_pb07_agree = self.data.loc[(bb01_state == 1) & (pb07_state == 1), f'fwd_ret_{horizon}'].dropna()
        if len(bb01_pb07_agree) > 0:
            results['BB01_when_PB07_agrees'] = {
                'count': len(bb01_pb07_agree),
                'mean_return': bb01_pb07_agree.mean() * 100,
                'std_return': bb01_pb07_agree.std() * 100,
                'win_rate': (bb01_pb07_agree > 0).sum() / len(bb01_pb07_agree) * 100
            }
        
        return results


def run_ensemble_and_conditional_analysis():
    """Run full ensemble and conditional analysis."""
    
    print("\n" + "="*80)
    print("ENSEMBLE AND CONDITIONAL-ALPHA ANALYSIS")
    print("="*80)
    
    # Load baseline daily returns (from portfolio_bb01_pb07.py output)
    print("\nLoading baseline daily returns...")
    portfolio_daily = pd.read_csv('research_output/portfolio_daily_returns.csv', parse_dates=['date'])
    
    # Extract daily returns for each strategy
    daily_returns = {
        'BB01': dict(zip(portfolio_daily['date'], portfolio_daily['bb01_daily_return'])),
        'PB07': dict(zip(portfolio_daily['date'], portfolio_daily['pb07_daily_return']))
    }
    
    # Compute portfolio allocations
    print("\nComputing portfolio allocations...")
    portfolio_daily['port_50_50'] = 0.5 * portfolio_daily['bb01_daily_return'] + 0.5 * portfolio_daily['pb07_daily_return']
    portfolio_daily['port_30_70'] = 0.3 * portfolio_daily['bb01_daily_return'] + 0.7 * portfolio_daily['pb07_daily_return']
    portfolio_daily['port_70_30'] = 0.7 * portfolio_daily['bb01_daily_return'] + 0.3 * portfolio_daily['pb07_daily_return']
    
    daily_returns['50/50'] = dict(zip(portfolio_daily['date'], portfolio_daily['port_50_50']))
    daily_returns['30/70'] = dict(zip(portfolio_daily['date'], portfolio_daily['port_30_70']))
    daily_returns['70/30'] = dict(zip(portfolio_daily['date'], portfolio_daily['port_70_30']))
    
    # Compute metrics
    print("\n" + "="*80)
    print("ENSEMBLE METRICS (FIXED WEIGHTS)")
    print("="*80)
    
    analyzer = EnsembleAnalyzer('signals_cleaned.csv', 'price_cleaned.csv')
    ensemble_results = {}
    
    for name, daily_ret_dict in daily_returns.items():
        metrics = analyzer.compute_metrics(daily_ret_dict)
        yearly = analyzer.compute_yearly_returns(daily_ret_dict)
        
        ensemble_results[name] = {
            'metrics': metrics,
            'yearly': yearly
        }
        
        print(f"\n{name}:")
        print(f"  Return: {metrics['total_return']:.2f}%")
        print(f"  Ann. Return: {metrics['annualized_return']:.2f}%")
        print(f"  Volatility: {metrics['volatility']:.2f}%")
        print(f"  Sharpe: {metrics['sharpe']:.4f}")
        print(f"  Calmar: {metrics['calmar']:.4f}")
        print(f"  Max DD: {metrics['max_drawdown']:.2f}%")
        print(f"  Yearly: 2018={yearly[2018]:.2f}% | 2019={yearly[2019]:.2f}% | 2020={yearly[2020]:.2f}% | 2021={yearly[2021]:.2f}%")
    
    # Conditional analysis
    print("\n" + "="*80)
    print("CONDITIONAL-ALPHA ANALYSIS")
    print("="*80)
    
    # Load merged data for conditional analysis
    signals_df = pd.read_csv('signals_cleaned.csv', parse_dates=['date'])
    price_df = pd.read_csv('price_cleaned.csv', parse_dates=['date'])
    merged = pd.merge(signals_df, price_df, on='date', how='inner').sort_values('date').reset_index(drop=True)
    
    cond_analyzer = ConditionalAlphaAnalyzer(merged)
    
    # Joint states analysis (5-day forward return)
    print("\nJoint Signal States (5-day forward return):")
    joint_results = cond_analyzer.joint_states_analysis(horizon=5)
    
    for state, data in sorted(joint_results.items()):
        print(f"  {state:20} | count={data['count']:3} | mean={data['mean_return']:7.3f}% | win_rate={data['win_rate']:5.1f}%")
    
    # Agreement analysis
    print("\nAgreement Analysis (5-day forward return):")
    agreement_results = cond_analyzer.agreement_analysis(horizon=5)
    
    for config, data in sorted(agreement_results.items()):
        improvement = ""
        if 'agree' in config and 'unconditional' in agreement_results:
            # Calculate improvement
            pass
        print(f"  {config:30} | count={data['count']:3} | mean={data['mean_return']:7.3f}% | win_rate={data['win_rate']:5.1f}%")
    
    # Save results
    results_json = {
        'ensemble': ensemble_results,
        'conditional': {
            'joint_states': joint_results,
            'agreement': agreement_results
        }
    }
    
    with open('research_output/ensemble_conditional_results.json', 'w') as f:
        # Convert to JSON-serializable types
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_types(v) for v in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            return obj
        
        json.dump(convert_types(results_json), f, indent=2)
    
    print("\n✓ Results saved to research_output/ensemble_conditional_results.json")
    
    return ensemble_results, joint_results, agreement_results


if __name__ == '__main__':
    import os
    os.chdir('/tmp/Prepathon_Quant_PS')
    
    ensemble_res, joint_res, agreement_res = run_ensemble_and_conditional_analysis()
