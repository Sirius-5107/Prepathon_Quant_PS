"""
Combined BB01 + PB07 Portfolio Construction.

Builds aligned daily return streams from two fixed, non-overlapping strategies
(BB01 Breakout Continuation, PB07 Q1 Mean Reversion) and analyzes portfolio
combinations using PRE-SPECIFIED weights.

Critical: This is NOT parameter optimization.
All weights are fixed in advance (50/50, 30/70, 70/30).
No look-ahead, no future information, no overlapping positions within each strategy.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import json
from datetime import timedelta

class PortfolioBuilder:
    """Build combined portfolio from two strategy daily return streams."""
    
    def __init__(self, signals_path, price_path):
        """Load data and prepare for portfolio construction."""
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        print(f"\n{'='*80}")
        print("PORTFOLIO CONSTRUCTION: BB01 + PB07")
        print(f"{'='*80}")
        print(f"Data loaded: {len(self.data)} rows")
        print(f"Date range: {self.data['date'].min().date()} to {self.data['date'].max().date()}")
        
        self.bb01_trades = []
        self.pb07_trades = []
        self.daily_returns = None
        self.portfolio_results = {}
    
    def extract_strategy_trades(self):
        """Extract trade data from existing strategy CSVs."""
        print(f"\n{'='*80}")
        print("EXTRACTING STRATEGY TRADES")
        print(f"{'='*80}")
        
        # Load existing trade CSVs
        try:
            bb01_trades_df = pd.read_csv('research_output/strategy_bb01_trades.csv', 
                                         parse_dates=['entry_date', 'exit_date'])
            pb07_trades_df = pd.read_csv('research_output/strategy_02_trades.csv',
                                         parse_dates=['entry_date', 'exit_date'])
            
            print(f"BB01 trades loaded: {len(bb01_trades_df)}")
            print(f"PB07 trades loaded: {len(pb07_trades_df)}")
            
            # Convert to internal format
            self.bb01_trades = bb01_trades_df.to_dict('records')
            self.pb07_trades = pb07_trades_df.to_dict('records')
            
            # Convert percentage returns to decimals
            for trade in self.bb01_trades:
                trade['net_return'] = trade['net_return'] / 100
                trade['gross_return'] = trade['gross_return'] / 100
                trade['entry_cost'] = trade['entry_cost'] / 100
                trade['exit_cost'] = trade['exit_cost'] / 100
            
            for trade in self.pb07_trades:
                trade['net_return'] = trade['net_return'] / 100
                trade['gross_return'] = trade['gross_return'] / 100
                trade['entry_cost'] = trade['entry_cost'] / 100
                trade['exit_cost'] = trade['exit_cost'] / 100
            
            return True
        except FileNotFoundError:
            print("ERROR: Could not load strategy trade CSVs")
            return False
    
    def build_daily_returns(self):
        """Build aligned daily return series for both strategies."""
        print(f"\n{'='*80}")
        print("BUILDING ALIGNED DAILY RETURNS")
        print(f"{'='*80}")
        
        # Initialize daily returns dataframe
        dates = self.data['date'].values
        daily_data = pd.DataFrame({
            'date': dates,
            'bb01_daily_return': np.zeros(len(dates)),
            'pb07_daily_return': np.zeros(len(dates)),
            'open': self.data['open'].values,
            'close': self.data['close'].values
        })
        
        # For BB01: mark-to-market daily during holding period, full return at exit
        print("\nProcessing BB01 trades...")
        for trade in self.bb01_trades:
            entry_date = pd.to_datetime(trade['entry_date'])
            exit_date = pd.to_datetime(trade['exit_date'])
            entry_price = trade['entry_price']
            exit_price = trade['exit_price']
            net_ret = trade['net_return']
            
            # Find indices
            entry_idx = None
            exit_idx = None
            
            for i, d in enumerate(dates):
                d_pd = pd.to_datetime(d)
                if d_pd == entry_date:
                    entry_idx = i
                if d_pd == exit_date:
                    exit_idx = i
            
            if entry_idx is not None and exit_idx is not None:
                # Mark full return at exit (simpler, matches strategy definition)
                daily_data.loc[exit_idx, 'bb01_daily_return'] += net_ret
        
        print(f"BB01 trades marked: {len(self.bb01_trades)}")
        
        # For PB07: same logic
        print("\nProcessing PB07 trades...")
        for trade in self.pb07_trades:
            entry_date = pd.to_datetime(trade['entry_date'])
            exit_date = pd.to_datetime(trade['exit_date'])
            net_ret = trade['net_return']
            
            entry_idx = None
            exit_idx = None
            
            for i, d in enumerate(dates):
                d_pd = pd.to_datetime(d)
                if d_pd == entry_date:
                    entry_idx = i
                if d_pd == exit_date:
                    exit_idx = i
            
            if entry_idx is not None and exit_idx is not None:
                # Mark full return at exit
                daily_data.loc[exit_idx, 'pb07_daily_return'] += net_ret
        
        print(f"PB07 trades marked: {len(self.pb07_trades)}")
        
        self.daily_returns = daily_data[['date', 'bb01_daily_return', 'pb07_daily_return']]
        return self.daily_returns
    
    def reconcile_with_standalone(self):
        """Verify daily returns reproduce standalone strategy results."""
        print(f"\n{'='*80}")
        print("RECONCILIATION CHECK")
        print(f"{'='*80}")
        
        # Use geometric compounding, not arithmetic sum
        # Equity curves in standalone used daily marking, so simple cumulative return
        # But the trade CSVs store individual trade returns
        
        # BB01: arithmetic sum of trade returns (as reported in standalone)
        bb01_arithmetic = sum(t['net_return'] for t in self.bb01_trades) * 100
        bb01_compounded = ((1 + np.array([t['net_return'] for t in self.bb01_trades])).prod() - 1) * 100
        
        print(f"\nBB01:")
        print(f"  Arithmetic sum of trades: {bb01_arithmetic:.2f}%")
        print(f"  Compounded equity: {bb01_compounded:.2f}%")
        print(f"  Standalone reported: 23.03% (arithmetic sum)")
        print(f"  Match: {abs(bb01_arithmetic - 23.03) < 0.1}")
        
        # PB07: same logic
        pb07_arithmetic = sum(t['net_return'] for t in self.pb07_trades) * 100
        pb07_compounded = ((1 + np.array([t['net_return'] for t in self.pb07_trades])).prod() - 1) * 100
        
        print(f"\nPB07:")
        print(f"  Arithmetic sum of trades: {pb07_arithmetic:.2f}%")
        print(f"  Compounded equity: {pb07_compounded:.2f}%")
        print(f"  Standalone reported: 22.64% (arithmetic sum)")
        print(f"  Match: {abs(pb07_arithmetic - 22.64) < 0.1}")
        
        # For portfolio construction, we use the daily return stream
        # The compounded return from daily returns should match compounded equity
        bb01_ret = (1 + self.daily_returns['bb01_daily_return']).prod() - 1
        pb07_ret = (1 + self.daily_returns['pb07_daily_return']).prod() - 1
        
        print(f"\nDaily return stream reconciliation:")
        print(f"  BB01 compounded from daily returns: {bb01_ret*100:.2f}%")
        print(f"  Expected compounded: {bb01_compounded:.2f}%")
        print(f"  PB07 compounded from daily returns: {pb07_ret*100:.2f}%")
        print(f"  Expected compounded: {pb07_compounded:.2f}%")
        
        # Check if they match (tolerance: 0.2% due to rounding)
        if abs((bb01_ret*100) - bb01_compounded) > 0.2 or abs((pb07_ret*100) - pb07_compounded) > 0.2:
            print("\nWARNING: Daily return reconciliation difference exceeds 0.2%")
            return False
        
        print("\n✓ Reconciliation PASSED (compounded returns match)")
        return True
    
    def build_portfolio_weights(self, weight_bb01, weight_pb07):
        """Build portfolio with specified weights."""
        portfolio_ret = (self.daily_returns['bb01_daily_return'] * weight_bb01 + 
                        self.daily_returns['pb07_daily_return'] * weight_pb07)
        return portfolio_ret
    
    def calculate_metrics(self, daily_returns, name=""):
        """Calculate portfolio metrics from daily return series."""
        rets = daily_returns.values
        
        # Remove zero days for correlation/vol calculations
        active_days = rets[rets != 0]
        
        total_ret = (1 + rets).prod() - 1
        n_active_days = len(active_days)
        n_total_days = len(rets)
        
        if len(active_days) > 0:
            daily_vol = np.std(active_days)
            ann_vol = daily_vol * np.sqrt(252)
            
            # Annualized return
            years = n_total_days / 252
            ann_ret = ((1 + total_ret) ** (1 / years)) - 1 if years > 0 else 0
            
            sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
            
            # Drawdown
            equity = np.cumprod(1 + rets)
            running_max = np.maximum.accumulate(equity)
            dd = (equity - running_max) / running_max
            max_dd = np.min(dd) if len(dd) > 0 else 0
            
            calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0
            
            # Win rate
            win_rate = (rets > 0).sum() / len(rets[rets != 0]) if len(rets[rets != 0]) > 0 else 0
        else:
            ann_vol = 0
            ann_ret = 0
            sharpe = 0
            max_dd = 0
            calmar = 0
            win_rate = 0
        
        metrics = {
            'total_return_pct': total_ret * 100,
            'annualized_return_pct': ann_ret * 100,
            'annualized_volatility_pct': ann_vol * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_dd * 100,
            'calmar_ratio': calmar,
            'win_rate_pct': win_rate * 100,
            'n_active_days': int(n_active_days),
            'n_total_days': int(n_total_days)
        }
        
        return metrics
    
    def calculate_correlation(self):
        """Calculate correlation metrics between strategies."""
        bb01_rets = self.daily_returns['bb01_daily_return'].values
        pb07_rets = self.daily_returns['pb07_daily_return'].values
        
        # All days
        pearson_all = np.corrcoef(bb01_rets, pb07_rets)[0, 1]
        spearman_all, _ = stats.spearmanr(bb01_rets, pb07_rets)
        
        # Joint active days (at least one position open)
        active_mask = (bb01_rets != 0) | (pb07_rets != 0)
        if active_mask.sum() > 1:
            pearson_active = np.corrcoef(bb01_rets[active_mask], pb07_rets[active_mask])[0, 1]
            spearman_active, _ = stats.spearmanr(bb01_rets[active_mask], pb07_rets[active_mask])
        else:
            pearson_active = np.nan
            spearman_active = np.nan
        
        # Covariance
        cov_matrix = np.cov(bb01_rets, pb07_rets)
        covariance = cov_matrix[0, 1]
        
        metrics = {
            'pearson_correlation_all': float(pearson_all),
            'spearman_correlation_all': float(spearman_all),
            'pearson_correlation_active': float(pearson_active),
            'spearman_correlation_active': float(spearman_active),
            'covariance': float(covariance),
            'n_active_days': int(active_mask.sum()),
            'n_total_days': len(bb01_rets)
        }
        
        return metrics
    
    def analyze_worst_drawdowns(self):
        """Find worst drawdown periods and analyze strategy behavior."""
        rets = self.daily_returns.copy()
        
        # Calculate equity curves
        bb01_eq = np.cumprod(1 + rets['bb01_daily_return'])
        pb07_eq = np.cumprod(1 + rets['pb07_daily_return'])
        portfolio_eq = np.cumprod(1 + (0.5 * rets['bb01_daily_return'] + 0.5 * rets['pb07_daily_return']))
        
        # Drawdowns
        bb01_dd = (bb01_eq - np.maximum.accumulate(bb01_eq)) / np.maximum.accumulate(bb01_eq)
        pb07_dd = (pb07_eq - np.maximum.accumulate(pb07_eq)) / np.maximum.accumulate(pb07_eq)
        port_dd = (portfolio_eq - np.maximum.accumulate(portfolio_eq)) / np.maximum.accumulate(portfolio_eq)
        
        # Find worst 10 portfolio drawdowns
        worst_dd_indices = np.argsort(port_dd)[:10]
        
        results = []
        for idx in worst_dd_indices:
            results.append({
                'date': rets['date'].iloc[idx],
                'portfolio_dd_pct': port_dd[idx] * 100,
                'bb01_dd_pct': bb01_dd[idx] * 100,
                'pb07_dd_pct': pb07_dd[idx] * 100,
                'bb01_return_pct': rets['bb01_daily_return'].iloc[idx] * 100,
                'pb07_return_pct': rets['pb07_daily_return'].iloc[idx] * 100
            })
        
        return results
    
    def run_complete_analysis(self):
        """Run complete portfolio analysis."""
        print("\n" + "#"*80)
        print("# PORTFOLIO CONSTRUCTION & ANALYSIS")
        print("#"*80)
        
        # Extract trades
        if not self.extract_strategy_trades():
            print("FATAL: Could not extract strategy trades")
            return False
        
        # Build daily returns
        self.build_daily_returns()
        
        # Reconcile
        if not self.reconcile_with_standalone():
            print("FATAL: Reconciliation failed - daily returns do not match standalone")
            return False
        
        # Calculate correlation
        corr_metrics = self.calculate_correlation()
        self.portfolio_results['correlation'] = corr_metrics
        
        print(f"\n{'='*80}")
        print("CORRELATION ANALYSIS")
        print(f"{'='*80}")
        print(f"Pearson correlation (all days): {corr_metrics['pearson_correlation_all']:.4f}")
        print(f"Pearson correlation (active days): {corr_metrics['pearson_correlation_active']:.4f}")
        print(f"Spearman correlation (all days): {corr_metrics['spearman_correlation_all']:.4f}")
        print(f"Covariance: {corr_metrics['covariance']:.6f}")
        
        # Test fixed weights
        weights_to_test = [
            (1.0, 0.0, "BB01 alone"),
            (0.0, 1.0, "PB07 alone"),
            (0.5, 0.5, "50/50"),
            (0.3, 0.7, "30/70"),
            (0.7, 0.3, "70/30")
        ]
        
        print(f"\n{'='*80}")
        print("PORTFOLIO METRICS COMPARISON")
        print(f"{'='*80}")
        
        for w_bb01, w_pb07, label in weights_to_test:
            port_ret = self.build_portfolio_weights(w_bb01, w_pb07)
            metrics = self.calculate_metrics(port_ret, label)
            self.portfolio_results[label] = metrics
            
            print(f"\n{label}:")
            print(f"  Total return: {metrics['total_return_pct']:.2f}%")
            print(f"  Ann. return: {metrics['annualized_return_pct']:.2f}%")
            print(f"  Ann. vol: {metrics['annualized_volatility_pct']:.2f}%")
            print(f"  Sharpe: {metrics['sharpe_ratio']:.4f}")
            print(f"  Max DD: {metrics['max_drawdown_pct']:.2f}%")
            print(f"  Calmar: {metrics['calmar_ratio']:.4f}")
            print(f"  Win rate: {metrics['win_rate_pct']:.1f}%")
        
        # Yearly breakdown
        print(f"\n{'='*80}")
        print("YEARLY BREAKDOWN")
        print(f"{'='*80}")
        self.calculate_yearly_performance()
        
        # WFO
        print(f"\n{'='*80}")
        print("WALK-FORWARD VALIDATION")
        print(f"{'='*80}")
        self.calculate_wfo_performance()
        
        # Worst drawdowns
        print(f"\n{'='*80}")
        print("WORST DRAWDOWN PERIODS")
        print(f"{'='*80}")
        worst_dd = self.analyze_worst_drawdowns()
        self.portfolio_results['worst_drawdowns'] = worst_dd
        for dd_event in worst_dd[:5]:
            print(f"{dd_event['date'].date()}: Portfolio {dd_event['portfolio_dd_pct']:.2f}%, "
                  f"BB01 {dd_event['bb01_dd_pct']:.2f}%, PB07 {dd_event['pb07_dd_pct']:.2f}%")
        
        return True
    
    def calculate_yearly_performance(self):
        """Calculate yearly portfolio performance."""
        rets = self.daily_returns.copy()
        rets['year'] = pd.to_datetime(rets['date']).dt.year
        
        yearly_results = []
        for year in sorted(rets['year'].unique()):
            year_mask = rets['year'] == year
            year_data = rets[year_mask]
            
            bb01_yr = year_data['bb01_daily_return'].sum() * 100
            pb07_yr = year_data['pb07_daily_return'].sum() * 100
            port_50_50 = (year_data['bb01_daily_return'] * 0.5 + year_data['pb07_daily_return'] * 0.5).sum() * 100
            
            yearly_results.append({
                'year': int(year),
                'bb01_return_pct': bb01_yr,
                'pb07_return_pct': pb07_yr,
                'portfolio_50_50_pct': port_50_50
            })
            
            print(f"{year}: BB01 {bb01_yr:7.2f}%, PB07 {pb07_yr:7.2f}%, 50/50 {port_50_50:7.2f}%")
        
        self.portfolio_results['yearly'] = yearly_results
    
    def calculate_wfo_performance(self):
        """Walk-forward portfolio validation."""
        rets = self.daily_returns.copy()
        rets['date_pd'] = pd.to_datetime(rets['date'])
        rets['year'] = rets['date_pd'].dt.year
        
        # Fold 1: 2018-2019 train, 2020 test
        fold1_train = rets[rets['year'].isin([2018, 2019])]
        fold1_test = rets[rets['year'] == 2020]
        
        bb01_fold1_test = fold1_test['bb01_daily_return'].sum() * 100
        pb07_fold1_test = fold1_test['pb07_daily_return'].sum() * 100
        port_fold1_test = (fold1_test['bb01_daily_return'] * 0.5 + fold1_test['pb07_daily_return'] * 0.5).sum() * 100
        
        print(f"Fold 1 (2018-2019 → 2020):")
        print(f"  BB01: {bb01_fold1_test:.2f}%")
        print(f"  PB07: {pb07_fold1_test:.2f}%")
        print(f"  50/50: {port_fold1_test:.2f}%")
        
        # Fold 2: 2018-2020 train, 2021 test
        fold2_train = rets[rets['year'].isin([2018, 2019, 2020])]
        fold2_test = rets[rets['year'] == 2021]
        
        bb01_fold2_test = fold2_test['bb01_daily_return'].sum() * 100
        pb07_fold2_test = fold2_test['pb07_daily_return'].sum() * 100
        port_fold2_test = (fold2_test['bb01_daily_return'] * 0.5 + fold2_test['pb07_daily_return'] * 0.5).sum() * 100
        
        print(f"Fold 2 (2018-2020 → 2021):")
        print(f"  BB01: {bb01_fold2_test:.2f}%")
        print(f"  PB07: {pb07_fold2_test:.2f}%")
        print(f"  50/50: {port_fold2_test:.2f}%")
        
        self.portfolio_results['wfo'] = {
            'fold1_test_bb01': bb01_fold1_test,
            'fold1_test_pb07': pb07_fold1_test,
            'fold1_test_portfolio': port_fold1_test,
            'fold2_test_bb01': bb01_fold2_test,
            'fold2_test_pb07': pb07_fold2_test,
            'fold2_test_portfolio': port_fold2_test
        }
    
    def save_results(self, output_dir='research_output'):
        """Save all portfolio results."""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Daily returns CSV
        self.daily_returns.to_csv(Path(output_dir) / 'portfolio_daily_returns.csv', index=False)
        
        # Correlation CSV
        corr_data = self.portfolio_results['correlation']
        corr_df = pd.DataFrame([corr_data])
        corr_df.to_csv(Path(output_dir) / 'portfolio_correlation.csv', index=False)
        
        # Yearly CSV
        yearly_df = pd.DataFrame(self.portfolio_results['yearly'])
        yearly_df.to_csv(Path(output_dir) / 'portfolio_yearly.csv', index=False)
        
        # WFO CSV
        wfo_data = self.portfolio_results['wfo']
        wfo_df = pd.DataFrame([{
            'fold': [1, 2],
            'test_bb01_pct': [wfo_data['fold1_test_bb01'], wfo_data['fold2_test_bb01']],
            'test_pb07_pct': [wfo_data['fold1_test_pb07'], wfo_data['fold2_test_pb07']],
            'test_portfolio_50_50_pct': [wfo_data['fold1_test_portfolio'], wfo_data['fold2_test_portfolio']]
        }])
        
        # Metrics JSON
        metrics_json = {
            'standalone_bb01': self.portfolio_results['BB01 alone'],
            'standalone_pb07': self.portfolio_results['PB07 alone'],
            'portfolio_50_50': self.portfolio_results['50/50'],
            'portfolio_30_70': self.portfolio_results['30/70'],
            'portfolio_70_30': self.portfolio_results['70/30'],
            'correlation': self.portfolio_results['correlation'],
            'wfo': self.portfolio_results['wfo']
        }
        
        with open(Path(output_dir) / 'portfolio_metrics.json', 'w') as f:
            json.dump(metrics_json, f, indent=2, default=str)
        
        # WFO CSV (simplified)
        wfo_simple = pd.DataFrame({
            'fold': [1, 2],
            'test_bb01_pct': [wfo_data['fold1_test_bb01'], wfo_data['fold2_test_bb01']],
            'test_pb07_pct': [wfo_data['fold1_test_pb07'], wfo_data['fold2_test_pb07']],
            'test_portfolio_50_50_pct': [wfo_data['fold1_test_portfolio'], wfo_data['fold2_test_portfolio']]
        })
        wfo_simple.to_csv(Path(output_dir) / 'portfolio_wfo.csv', index=False)
        
        print(f"\nResults saved to {output_dir}/")


def main():
    """Run portfolio construction and analysis."""
    signals_path = 'signals_cleaned.csv'
    price_path = 'price_cleaned.csv'
    
    builder = PortfolioBuilder(signals_path, price_path)
    success = builder.run_complete_analysis()
    
    if success:
        builder.save_results()
        print("\n" + "#"*80)
        print("# PORTFOLIO ANALYSIS COMPLETE")
        print("#"*80)
    else:
        print("\nPORTFOLIO ANALYSIS FAILED - DO NOT REPORT RESULTS")


if __name__ == '__main__':
    main()
