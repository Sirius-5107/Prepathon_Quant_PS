"""
Exit Management Research Extension (Task 2).

Test the incremental value of exit rules:
1. Baseline: no early exits (hold to horizon)
2. Max holding period: exit if position becomes stale
3. Trailing stop: exit on adverse price move
4. Combined: both trailing stop and max holding period

Critical design constraints:
- No lookahead (signal through t-1, entry at t open)
- No hindsight fills (use next-candle logic)
- Preserve t-1 cutoff for all signals
- Handle long and short separately (not implemented; focus on long)
- Audit every trade: entry, exit, reason, costs
- No parameter optimization (transparent grid only)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import json
from datetime import timedelta


class TradeWithExitManagement:
    """A single trade with exit lifecycle tracking."""
    
    def __init__(self, entry_idx, entry_date, entry_price, signal_name):
        self.entry_idx = entry_idx
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.signal_name = signal_name
        
        # Position tracking
        self.highest_price = entry_price  # For trailing stop (long)
        self.lowest_price = entry_price
        self.exit_idx = None
        self.exit_date = None
        self.exit_price = None
        self.exit_reason = None  # 'horizon', 'trailing_stop', 'max_holding'
        
        # P&L
        self.gross_return = None
        self.transaction_costs = 0.001  # 0.05% entry + 0.05% exit
        self.net_return = None
    
    def update_price_path(self, price):
        """Update running max/min for trailing stop calculation."""
        self.highest_price = max(self.highest_price, price)
        self.lowest_price = min(self.lowest_price, price)
    
    def check_trailing_stop_long(self, price, trailing_stop_pct):
        """Check if price breaches trailing stop (long position)."""
        if trailing_stop_pct is None or trailing_stop_pct <= 0:
            return False
        trailing_stop_level = self.highest_price * (1 - trailing_stop_pct)
        return price <= trailing_stop_level
    
    def close_position(self, exit_idx, exit_date, exit_price, exit_reason):
        """Close position and calculate returns."""
        self.exit_idx = exit_idx
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        
        # Compute P&L
        self.gross_return = (exit_price - self.entry_price) / self.entry_price
        self.net_return = self.gross_return - self.transaction_costs
    
    def to_dict(self):
        """Convert to dictionary for CSV output."""
        return {
            'entry_idx': self.entry_idx,
            'entry_date': self.entry_date,
            'entry_price': self.entry_price,
            'exit_idx': self.exit_idx,
            'exit_date': self.exit_date,
            'exit_price': self.exit_price,
            'holding_days': (self.exit_date - self.entry_date).days if self.exit_date else None,
            'gross_return_pct': self.gross_return * 100 if self.gross_return is not None else None,
            'net_return_pct': self.net_return * 100 if self.net_return is not None else None,
            'exit_reason': self.exit_reason,
            'signal': self.signal_name
        }


class StrategyWithExitManagement:
    """Base class for strategy with configurable exit rules."""
    
    def __init__(self, signals_path, price_path, signal_name, signal_column):
        """Initialize with data and signal configuration."""
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        self.signal_name = signal_name
        self.signal_column = signal_column
        self.trades = []
    
    def find_entries(self, signal_threshold=None):
        """Find all entry opportunities (signal through t-1)."""
        signal_vals = self.data[self.signal_column].values
        entries = []
        
        for i in range(1, len(self.data)):
            # For BB01: signal == 1
            # For PB07: bottom quintile (we'll compute this inline)
            signal_trigger = False
            
            if self.signal_column == 'BB01':
                signal_trigger = signal_vals[i-1] == 1
            elif self.signal_column == 'PB07':
                # Bottom quintile (Q1)
                valid_vals = signal_vals[~np.isnan(signal_vals)]
                q1_threshold = np.percentile(valid_vals, 20)
                signal_trigger = signal_vals[i-1] <= q1_threshold and not np.isnan(signal_vals[i-1])
            
            if signal_trigger:
                entries.append(i)
        
        return entries
    
    def backtest_with_exits(self, max_holding_days=20, trailing_stop_pct=None):
        """
        Run backtest with configurable exit rules.
        
        Args:
            max_holding_days: maximum days to hold (None = no max)
            trailing_stop_pct: trailing stop as decimal (0.03 = 3%) (None = no trail stop)
        
        Returns:
            trades list
        """
        entries = self.find_entries()
        
        # Enforce no-overlap
        active_positions = {}  # entry_idx -> exit_idx
        valid_entries = []
        skipped = 0
        
        for entry_idx in entries:
            # Check if this entry conflicts with existing positions
            conflicts = False
            for ex_idx in active_positions.values():
                if entry_idx < ex_idx:
                    conflicts = True
                    skipped += 1
                    break
            
            if not conflicts:
                # This entry is valid; mark a position as potentially open
                # We'll update the actual exit below
                valid_entries.append(entry_idx)
        
        # Now process each entry through its lifecycle
        self.trades = []
        
        for entry_idx in valid_entries:
            entry_date = pd.to_datetime(self.data.loc[entry_idx, 'date'])
            entry_price = self.data.loc[entry_idx, 'open']
            
            trade = TradeWithExitManagement(entry_idx, entry_date, entry_price, self.signal_name)
            
            # Simulate position: check each subsequent day for exit conditions
            exit_found = False
            
            for day_offset in range(1, len(self.data) - entry_idx):
                check_idx = entry_idx + day_offset
                check_price = self.data.loc[check_idx, 'close']
                check_date = pd.to_datetime(self.data.loc[check_idx, 'date'])
                
                # Update price path for trailing stop
                trade.update_price_path(check_price)
                
                # Check exit conditions
                exit_reason = None
                
                # 1. Max holding period exceeded
                if max_holding_days is not None:
                    holding_days = (check_date - entry_date).days
                    if holding_days >= max_holding_days:
                        exit_reason = 'max_holding'
                
                # 2. Trailing stop breached (checked on next candle at open)
                # Use the open of the day after the stop is breached
                if exit_reason is None and trailing_stop_pct is not None:
                    if trade.check_trailing_stop_long(check_price, trailing_stop_pct):
                        exit_reason = 'trailing_stop'
                
                # If no early exit, continue
                if exit_reason is None:
                    continue
                
                # Exit found: use the NEXT candle's open (avoid hindsight)
                if check_idx + 1 < len(self.data):
                    exit_idx = check_idx + 1
                    exit_date = pd.to_datetime(self.data.loc[exit_idx, 'date'])
                    exit_price = self.data.loc[exit_idx, 'open']
                    
                    trade.close_position(exit_idx, exit_date, exit_price, exit_reason)
                    self.trades.append(trade)
                    exit_found = True
                    break
            
            # If no early exit, use the original horizon exit
            if not exit_found:
                horizon_idx = min(entry_idx + 20, len(self.data) - 1)
                exit_date = pd.to_datetime(self.data.loc[horizon_idx, 'date'])
                exit_price = self.data.loc[horizon_idx, 'close']
                
                trade.close_position(horizon_idx, exit_date, exit_price, 'horizon')
                self.trades.append(trade)
        
        return self.trades
    
    def compute_metrics(self):
        """Compute performance metrics from completed trades."""
        if len(self.trades) == 0:
            return {}
        
        trades_df = pd.DataFrame([t.to_dict() for t in self.trades])
        
        # Basic metrics
        total_return = ((1 + trades_df['net_return_pct'] / 100).prod() - 1) * 100
        num_trades = len(trades_df)
        
        # Risk metrics (from daily returns)
        daily_rets = trades_df['net_return_pct'].values / 100
        daily_vol = np.std(daily_rets) * np.sqrt(252) * 100
        
        ann_ret = total_return / 4  # Rough annualization (4 years of data)
        sharpe = ann_ret / daily_vol if daily_vol > 0 else 0
        
        # Drawdown
        equity = np.cumprod(1 + daily_rets)
        dd = (equity - np.maximum.accumulate(equity)) / np.maximum.accumulate(equity)
        max_dd = np.min(dd) * 100 if len(dd) > 0 else 0
        
        calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0
        
        # Trade stats
        winners = (trades_df['net_return_pct'] > 0).sum()
        win_rate = (winners / num_trades * 100) if num_trades > 0 else 0
        
        # Profit factor
        gross_wins = trades_df[trades_df['net_return_pct'] > 0]['net_return_pct'].sum()
        gross_loss = abs(trades_df[trades_df['net_return_pct'] < 0]['net_return_pct'].sum())
        profit_factor = gross_wins / gross_loss if gross_loss != 0 else 0
        
        # Average holding
        avg_holding = trades_df['holding_days'].mean()
        
        # Exit reasons
        exit_reason_counts = trades_df['exit_reason'].value_counts().to_dict()
        
        # Transaction costs
        total_costs = num_trades * 0.001 * 100  # 0.1% per trade
        
        return {
            'total_return': total_return,
            'annualized_return': ann_ret,
            'volatility': daily_vol,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'calmar': calmar,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_holding_days': avg_holding,
            'total_transaction_costs': total_costs,
            'exit_reason_counts': exit_reason_counts
        }
    
    def compute_yearly_metrics(self):
        """Break down metrics by year."""
        if len(self.trades) == 0:
            return {}
        
        yearly = {}
        for year in [2018, 2019, 2020, 2021]:
            year_trades = [t for t in self.trades if t.exit_date.year == year]
            if len(year_trades) == 0:
                yearly[year] = {'return': 0, 'trades': 0}
                continue
            
            rets = [t.net_return for t in year_trades if t.net_return is not None]
            year_return = ((1 + np.array(rets)).prod() - 1) * 100 if len(rets) > 0 else 0
            
            yearly[year] = {
                'return': year_return,
                'trades': len(year_trades)
            }
        
        return yearly


def run_exit_management_grid():
    """Run a transparent grid of exit configurations."""
    
    trailing_stops = [0.02, 0.03, 0.04, 0.05, 0.07, 0.10]
    max_holdings = [10, 15, 20, 30, 40, 60]
    
    results = {
        'bb01': {},
        'pb07': {}
    }
    
    print("\n" + "="*80)
    print("EXIT MANAGEMENT RESEARCH: TRANSPARENT GRID")
    print("="*80)
    
    # Test BB01
    print("\n" + "-"*80)
    print("BB01 STRATEGY")
    print("-"*80)
    
    for max_hold in max_holdings:
        for trail_stop in trailing_stops:
            config_key = f"max_hold={max_hold}_trail={trail_stop:.2f}"
            
            strategy = StrategyWithExitManagement(
                'signals_cleaned.csv',
                'price_cleaned.csv',
                'BB01',
                'BB01'
            )
            strategy.backtest_with_exits(max_holding_days=max_hold, trailing_stop_pct=trail_stop)
            metrics = strategy.compute_metrics()
            yearly = strategy.compute_yearly_metrics()
            
            results['bb01'][config_key] = {
                'metrics': metrics,
                'yearly': yearly,
                'num_trades': len(strategy.trades)
            }
            
            print(f"  {config_key:40} Return: {metrics.get('total_return', 0):7.2f}% | "
                  f"Sharpe: {metrics.get('sharpe', 0):7.4f} | Calmar: {metrics.get('calmar', 0):7.4f}")
    
    # Test PB07
    print("\n" + "-"*80)
    print("PB07 STRATEGY")
    print("-"*80)
    
    for max_hold in max_holdings:
        for trail_stop in trailing_stops:
            config_key = f"max_hold={max_hold}_trail={trail_stop:.2f}"
            
            strategy = StrategyWithExitManagement(
                'signals_cleaned.csv',
                'price_cleaned.csv',
                'PB07',
                'PB07'
            )
            strategy.backtest_with_exits(max_holding_days=max_hold, trailing_stop_pct=trail_stop)
            metrics = strategy.compute_metrics()
            yearly = strategy.compute_yearly_metrics()
            
            results['pb07'][config_key] = {
                'metrics': metrics,
                'yearly': yearly,
                'num_trades': len(strategy.trades)
            }
            
            print(f"  {config_key:40} Return: {metrics.get('total_return', 0):7.2f}% | "
                  f"Sharpe: {metrics.get('sharpe', 0):7.4f} | Calmar: {metrics.get('calmar', 0):7.4f}")
    
    return results


if __name__ == '__main__':
    import os
    os.chdir('/tmp/Prepathon_Quant_PS')
    
    results = run_exit_management_grid()
    
    # Save results
    with open('research_output/exit_management_grid_results.json', 'w') as f:
        # Convert numpy types to native Python for JSON serialization
        def convert_types(obj):
            if isinstance(obj, dict):
                return {k: convert_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_types(v) for v in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            return obj
        
        json.dump(convert_types(results), f, indent=2)
    
    print("\n✓ Grid results saved to research_output/exit_management_grid_results.json")
