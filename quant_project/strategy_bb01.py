"""
Strategy 1: BB01 Breakout Continuation.

Converts validated BB01 @ 20d signal into a causally correct, 
non-overlapping long strategy under competition rules.

Rules:
1. Long only
2. Enter when BB01[t-1]=1 and no position open
3. Hold for 20 trading days
4. Exit at t+20 open
5. No overlapping positions
6. No stop loss, profit target, leverage, filters, regime conditions
7. Transaction cost: 0.05% per side = 0.10% round trip

Timing convention:
- Signal available through t-1 close
- Entry decision at t, execution at t open
- Return: close[t+20] / open[t] - 1
- Exit at open[t+20]

Critical distinction:
- Signal-level validation: all 40 events, +0.323% spread
- Executable strategy: trades after no-overlap enforcement, actual costs
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import json
from datetime import timedelta

class BB01Strategy:
    """BB01 breakout continuation strategy with no-overlap position enforcement."""
    
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
        print("BB01 BREAKOUT CONTINUATION STRATEGY")
        print(f"{'='*80}")
        print(f"Data loaded: {len(self.data)} rows")
        print(f"Date range: {self.data['date'].min().date()} to {self.data['date'].max().date()}")
    
    def find_entry_exits(self, horizon=20):
        """
        Find all BB01 events and their corresponding 20d forward returns.
        Enforces no-overlap rule: skip events that occur during existing positions.
        """
        print(f"\n{'='*80}")
        print(f"FINDING ENTRIES & EXITS (Holding period: {horizon}d)")
        print(f"{'='*80}")
        
        bb01 = self.data['BB01'].astype(int)
        
        # Find all BB01 events (signal available through t-1, entry at t)
        all_events = []
        for i in range(len(self.data)):
            if i > 0 and bb01.iloc[i-1] == 1:  # BB01 known at t-1
                all_events.append(i)
        
        print(f"\nTotal BB01 signal events: {len(all_events)}")
        
        # Enforce no-overlap rule
        open_positions = {}  # entry_idx -> exit_idx
        valid_entries = []
        skipped = 0
        
        for entry_idx in all_events:
            # Check if any position is still open at entry_idx
            position_open = False
            for ex_idx in open_positions.values():
                if entry_idx < ex_idx:
                    position_open = True
                    skipped += 1
                    break
            
            if not position_open:
                # Can enter
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
            
            # Calculate returns
            gross_return = (exit_price - entry_price) / entry_price
            
            # Transaction costs (0.05% per side)
            entry_cost = 0.0005
            exit_cost = 0.0005
            total_cost = entry_cost + exit_cost
            
            net_return = gross_return - total_cost
            
            # Holding period in days
            holding_days = (exit_date - entry_date).days
            
            trade = {
                'entry_idx': entry_idx,
                'exit_idx': exit_idx,
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
        """Compute cumulative equity curve starting at 1.0."""
        equity = [1.0]
        
        for trade in self.trades:
            # Equity after net return
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
        
        # Basic statistics
        total_return = self.equity[-1] - 1.0
        n_trades = len(self.trades)
        
        # Annualized (assuming 252 trading days per year)
        total_days = (self.trades[-1]['exit_date'] - self.trades[0]['entry_date']).days
        years = total_days / 365.25
        annualized_return = (self.equity[-1] ** (1 / years)) - 1 if years > 0 else 0
        
        # Volatility
        daily_rets = []
        for i in range(1, len(self.equity)):
            daily_ret = (self.equity[i] - self.equity[i-1]) / self.equity[i-1]
            daily_rets.append(daily_ret)
        
        daily_vol = np.std(daily_rets) if len(daily_rets) > 0 else 0
        annualized_vol = daily_vol * np.sqrt(252)
        
        # Sharpe ratio (rf=0)
        sharpe = (annualized_return / annualized_vol) if annualized_vol > 0 else 0
        
        # Drawdown
        running_max = np.maximum.accumulate(self.equity)
        drawdown = (np.array(self.equity) - running_max) / running_max
        max_dd = np.min(drawdown)
        
        # Calmar ratio
        calmar = (annualized_return / abs(max_dd)) if max_dd != 0 else 0
        
        # Win rate
        winners = (returns > 0).sum()
        losers = (returns < 0).sum()
        win_rate = winners / n_trades if n_trades > 0 else 0
        
        # Profit factor
        gross_wins = np.maximum(returns, 0).sum()
        gross_losses = np.abs(np.minimum(returns, 0)).sum()
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else np.inf
        
        # Average trade
        avg_return = returns.mean()
        median_return = np.median(returns)
        
        # Best/worst
        best_trade = returns.max()
        worst_trade = returns.min()
        avg_winner = returns[returns > 0].mean() if (returns > 0).any() else 0
        avg_loser = returns[returns < 0].mean() if (returns < 0).any() else 0
        
        # Holding period
        avg_hold = np.mean([t['holding_days'] for t in self.trades])
        
        # Transaction costs
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
            'total_period_days': (self.trades[-1]['exit_date'] - self.trades[0]['entry_date']).days,
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
                'gross_pnl_pct': gross_returns.sum() * 100,
                'max_dd_pct': 0  # Placeholder
            }
            yearly_results.append(result)
        
        yearly_df = pd.DataFrame(yearly_results)
        self.results['yearly'] = yearly_df
        return yearly_df
    
    def calculate_wfo_performance(self):
        """Walk-forward validation: Train 2018-2019 test 2020; Train 2018-2020 test 2021."""
        wfo_results = []
        
        # Fold 1: Train 2018-2019, Test 2020
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
        
        # Fold 2: Train 2018-2020, Test 2021
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
    
    def sensitivity_check_horizons(self):
        """Test 10d and 15d horizons as robustness checks."""
        print(f"\n{'='*80}")
        print("SENSITIVITY CHECK: Holding Periods")
        print(f"{'='*80}")
        
        sensitivity = {}
        
        for horizon in [10, 15, 20]:
            valid_entries = self.find_entry_exits(horizon=horizon)
            self.trades = []  # Reset
            
            bb01 = self.data['BB01'].astype(int)
            all_events = [i for i in range(1, len(self.data)) if bb01.iloc[i-1] == 1]
            
            open_positions = {}
            valid_entries = []
            
            for entry_idx in all_events:
                position_open = False
                for ex_idx in open_positions.values():
                    if entry_idx < ex_idx:
                        position_open = True
                        break
                
                if not position_open:
                    exit_idx = min(entry_idx + horizon, len(self.data) - 1)
                    open_positions[entry_idx] = exit_idx
                    valid_entries.append(entry_idx)
            
            # Calculate returns for this horizon
            returns = []
            for entry_idx in valid_entries:
                exit_idx = open_positions[entry_idx]
                entry_price = self.data.iloc[entry_idx]['open']
                exit_price = self.data.iloc[exit_idx]['close']
                
                gross_return = (exit_price - entry_price) / entry_price
                net_return = gross_return - 0.001  # 0.10% total costs
                returns.append(net_return)
            
            returns = np.array(returns)
            sensitivity[horizon] = {
                'n_trades': len(returns),
                'total_return_pct': returns.sum() * 100,
                'avg_return_pct': returns.mean() * 100,
                'win_rate_pct': (returns > 0).sum() / len(returns) * 100 if len(returns) > 0 else 0
            }
        
        print("\nResults by holding period:")
        for h, metrics in sensitivity.items():
            print(f"  {h}d: {metrics['n_trades']} trades, {metrics['total_return_pct']:.2f}% return, {metrics['win_rate_pct']:.1f}% win rate")
        
        self.results['sensitivity_horizons'] = sensitivity
        return sensitivity
    
    def run_full_analysis(self):
        """Execute complete strategy analysis."""
        print("\n" + "#"*80)
        print("# STRATEGY 1: BB01 BREAKOUT CONTINUATION")
        print("#"*80)
        
        # Main analysis: 20d horizon
        self.find_entry_exits(horizon=20)
        self.compute_equity_curve()
        self.calculate_metrics()
        self.calculate_yearly_performance()
        self.calculate_wfo_performance()
        self.sensitivity_check_horizons()
        
        return self.results
    
    def print_summary(self):
        """Print detailed summary."""
        print(f"\n{'='*80}")
        print("EXECUTABLE STRATEGY SUMMARY (20d holding period)")
        print(f"{'='*80}")
        
        print(f"\nSignal-level validation (all events):")
        print(f"  Total BB01 events: {self.results['all_events']}")
        print(f"  Signal spread: +0.323% (Welch t=2.03, validated)")
        
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
            
            print(f"\nYear-by-year:")
            for _, row in self.results['yearly'].iterrows():
                print(f"  {int(row['year'])}: {int(row['n_trades'])} trades, {row['total_return_pct']:.2f}% return, {row['win_rate_pct']:.1f}% win rate")
            
            print(f"\nWalk-forward validation:")
            for _, row in self.results['wfo'].iterrows():
                print(f"  Fold {int(row['fold'])} ({row['train_period']} → {row['test_period']}):")
                print(f"    Train: {int(row['train_trades'])} trades, {row['train_return_pct']:.2f}%")
                print(f"    Test:  {int(row['test_trades'])} trades, {row['test_return_pct']:.2f}%")
                print(f"    Sign consistency: {row['sign_consistency']}")
    
    def save_results(self, output_dir='research_output'):
        """Save all results to files."""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Trade-level CSV
        if len(self.trades) > 0:
            trades_df = pd.DataFrame(self.trades)
            trades_df = trades_df[[
                'entry_date', 'exit_date', 'entry_price', 'exit_price',
                'gross_return', 'entry_cost', 'exit_cost', 'net_return', 'holding_days'
            ]]
            trades_df['gross_return'] *= 100
            trades_df['entry_cost'] *= 100
            trades_df['exit_cost'] *= 100
            trades_df['net_return'] *= 100
            trades_df.to_csv(Path(output_dir) / 'strategy_bb01_trades.csv', index=False)
            
            # Equity curve CSV
            equity_df = pd.DataFrame({
                'trade_n': range(len(self.equity)),
                'equity': self.equity,
                'return_pct': (np.array(self.equity) - 1) * 100
            })
            equity_df.to_csv(Path(output_dir) / 'strategy_bb01_equity.csv', index=False)
        
        # Metrics JSON
        metrics_json = {
            'signal_events': self.results['all_events'],
            'skipped_events': self.results['skipped_events'],
            'executable_trades': self.results['executable_trades'],
            'metrics': self.results['metrics']
        }
        with open(Path(output_dir) / 'strategy_bb01_metrics.json', 'w') as f:
            json.dump(metrics_json, f, indent=2, default=str)
        
        # Yearly results
        if 'yearly' in self.results and len(self.results['yearly']) > 0:
            self.results['yearly'].to_csv(
                Path(output_dir) / 'strategy_bb01_yearly.csv', index=False
            )
        
        # WFO results
        if 'wfo' in self.results and len(self.results['wfo']) > 0:
            self.results['wfo'].to_csv(
                Path(output_dir) / 'strategy_bb01_wfo.csv', index=False
            )
        
        print(f"\nResults saved to {output_dir}/")


def main():
    """Run Strategy 1 analysis."""
    signals_path = 'signals_cleaned.csv'
    price_path = 'price_cleaned.csv'
    
    strategy = BB01Strategy(signals_path, price_path)
    results = strategy.run_full_analysis()
    strategy.print_summary()
    strategy.save_results()
    
    print("\n" + "#"*80)
    print("# STRATEGY 1 ANALYSIS COMPLETE")
    print("#"*80)


if __name__ == '__main__':
    main()
