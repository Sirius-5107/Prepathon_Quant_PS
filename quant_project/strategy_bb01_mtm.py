"""
BB01 Breakout Continuation Strategy - Daily Mark-to-Market Implementation.

Marks positions to market every trading day during the holding period,
not just at exit. This provides a true daily return stream for portfolio construction.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

class BB01DailyMarkToMarket:
    """BB01 strategy with daily mark-to-market."""
    
    def __init__(self, signals_path, price_path):
        self.signals_df = pd.read_csv(signals_path, parse_dates=['date'])
        self.price_df = pd.read_csv(price_path, parse_dates=['date'])
        
        self.signals_df = self.signals_df.sort_values('date').reset_index(drop=True)
        self.price_df = self.price_df.sort_values('date').reset_index(drop=True)
        
        self.data = pd.merge(self.signals_df, self.price_df, on='date', how='inner')
        self.data = self.data.sort_values('date').reset_index(drop=True)
        self.data['year'] = self.data['date'].dt.year
        
        print(f"BB01 Daily Mark-to-Market Strategy")
        print(f"Data: {len(self.data)} rows, {self.data['date'].min().date()} to {self.data['date'].max().date()}")
    
    def find_entries_exits(self, horizon=20):
        """Find all BB01 signal events and holding periods."""
        print(f"\nFinding BB01 entries (20-day holding)...")
        
        bb01 = self.data['BB01'].values
        dates = self.data['date'].values
        prices = self.data[['open', 'close']].values
        
        all_events = []
        for i in range(1, len(self.data)):
            if bb01[i-1] == 1:  # Signal through t-1
                all_events.append(i)  # Entry at open[i]
        
        print(f"Total BB01 signal events: {len(all_events)}")
        
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
        
        print(f"Entries skipped (overlap): {skipped}")
        print(f"Valid entries: {len(valid_entries)}")
        
        self.trades = []
        for entry_idx in valid_entries:
            exit_idx = open_positions[entry_idx]
            
            entry_date = pd.to_datetime(self.data.loc[entry_idx, 'date'])
            exit_date = pd.to_datetime(self.data.loc[exit_idx, 'date'])
            entry_price = self.data.loc[entry_idx, 'open']
            exit_price = self.data.loc[exit_idx, 'close']
            
            gross_return = (exit_price - entry_price) / entry_price
            net_return = gross_return - 0.001  # 0.05% entry + 0.05% exit
            
            self.trades.append({
                'entry_idx': entry_idx,
                'exit_idx': exit_idx,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'gross_return': gross_return,
                'net_return': net_return,
                'holding_days': (exit_date - entry_date).days
            })
    
    def build_daily_returns_mtm(self):
        """Build daily return stream with mark-to-market."""
        print(f"\nBuilding daily mark-to-market returns...")
        
        daily_returns = []
        
        for date in self.data['date']:
            daily_ret = 0.0
            
            # Check if we're in any open position on this date
            for trade in self.trades:
                entry_date = trade['entry_date']
                exit_date = trade['exit_date']
                entry_price = trade['entry_price']
                
                # Is this date within holding period?
                if entry_date <= date <= exit_date:
                    # Get close price on this date
                    close_price = self.data[self.data['date'] == date]['close'].values
                    
                    if len(close_price) > 0:
                        close_price = close_price[0]
                        
                        # Calculate daily mark-to-market return
                        daily_mtm = (close_price - entry_price) / entry_price
                        
                        # Apply costs only at exit
                        if date == exit_date:
                            daily_mtm = daily_mtm - 0.001  # costs
                        
                        daily_ret = daily_mtm
                        break
            
            daily_returns.append({
                'date': date,
                'bb01_daily_return': daily_ret
            })
        
        self.daily_returns_df = pd.DataFrame(daily_returns)
        print(f"Daily returns built: {len(self.daily_returns_df)} trading days")
        print(f"Non-zero days: {(self.daily_returns_df['bb01_daily_return'] != 0).sum()}")
        
        return self.daily_returns_df
    
    def calculate_metrics(self):
        """Calculate performance metrics from daily returns."""
        rets = self.daily_returns_df['bb01_daily_return'].values
        
        total = ((1 + rets).prod() - 1) * 100
        n_days = len(rets)
        years = n_days / 252
        
        rets_nz = rets[rets != 0]
        daily_vol_nz = np.std(rets_nz) * np.sqrt(252) * 100 if len(rets_nz) > 0 else 0
        ann_ret = (((1 + total/100) ** (1/years)) - 1) * 100 if years > 0 else 0
        sharpe = ann_ret / daily_vol_nz if daily_vol_nz > 0 else 0
        
        equity = np.cumprod(1 + rets)
        dd = (equity - np.maximum.accumulate(equity)) / np.maximum.accumulate(equity)
        max_dd = np.min(dd) * 100
        calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0
        
        self.metrics = {
            'total_return': total,
            'annualized_return': ann_ret,
            'volatility': daily_vol_nz,
            'sharpe': sharpe,
            'max_drawdown': max_dd,
            'calmar': calmar
        }
        
        return self.metrics
    
    def save_results(self):
        """Save daily returns and metrics."""
        self.daily_returns_df.to_csv('research_output/strategy_bb01_daily_mtm.csv', index=False)
        
        # Compact trade list
        trades_df = pd.DataFrame(self.trades)
        trades_df = trades_df[[
            'entry_date', 'exit_date', 'entry_price', 'exit_price', 
            'gross_return', 'net_return', 'holding_days'
        ]]
        trades_df['gross_return'] = trades_df['gross_return'] * 100
        trades_df['net_return'] = trades_df['net_return'] * 100
        trades_df.to_csv('research_output/strategy_bb01_trades_mtm.csv', index=False)
        
        with open('research_output/strategy_bb01_metrics_mtm.json', 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"\nResults saved:")
        print(f"  strategy_bb01_daily_mtm.csv ({len(self.daily_returns_df)} rows)")
        print(f"  strategy_bb01_trades_mtm.csv ({len(self.trades)} trades)")
        print(f"  strategy_bb01_metrics_mtm.json")
    
    def print_summary(self):
        """Print summary."""
        m = self.metrics
        print(f"\n{'='*60}")
        print("BB01 SUMMARY (Daily Mark-to-Market)")
        print(f"{'='*60}")
        print(f"Trades: {len(self.trades)}")
        print(f"Total return: {m['total_return']:.2f}%")
        print(f"Annualized return: {m['annualized_return']:.2f}%")
        print(f"Annualized volatility: {m['volatility']:.2f}%")
        print(f"Sharpe ratio: {m['sharpe']:.4f}")
        print(f"Max drawdown: {m['max_drawdown']:.2f}%")
        print(f"Calmar ratio: {m['calmar']:.4f}")


def main():
    strategy = BB01DailyMarkToMarket('signals_cleaned.csv', 'price_cleaned.csv')
    strategy.find_entries_exits(horizon=20)
    strategy.build_daily_returns_mtm()
    strategy.calculate_metrics()
    strategy.save_results()
    strategy.print_summary()


if __name__ == '__main__':
    main()
