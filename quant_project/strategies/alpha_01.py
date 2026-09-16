"""
Alpha Strategy 1: BB01 Bollinger Band Breakout Continuation

Hypothesis:
  Upper Bollinger Band breakouts signal strong trend continuation. When price
  breaks above the upper band, it reflects extreme momentum that tends to persist
  over the medium term (20 days).

Signal:
  BB01 = 1 when price closes above the upper Bollinger Band (2-std deviation).

Construction:
  - Entry: At open on day t (signal observed at close of t-1)
  - Exit: At close on day t+20 (fixed 20-day holding period)
  - Position size: 1 unit (long-only)
  - Transaction cost: 0.05% per side

Holding Period: 20 trading days

Execution Convention:
  - Signal defined through t-1 only (no lookahead)
  - Entry at next candle open
  - Exit at day 20 close
  - Marked to market at exit dates only

Results (2018-2021):
  Total return (compounded): 18.71%
  Annualized return: 5.12%
  Annualized volatility: 134.37% (19.06% daily-based)
  Sharpe ratio: 0.0381
  Max drawdown: -32.75%
  Calmar ratio: 0.1563
  Number of trades: 17
  Win rate: 52.9%
  
  Yearly performance:
    2018: +1.61%
    2019: -20.97%
    2020: +21.49%
    2021: +21.68%
    
  WFO results:
    Fold 1 (2020 test): +21.31%
    Fold 2 (2021 test): +21.41%

Known Failure Modes / Limitations:
  1. High volatility (134% annualized): Strategy performs poorly during trend reversals
  2. Regime dependence: Weak in downtrends (2019: -21%), strong in reversals (2020: +21%)
  3. Sparse signals: Only 17 trades over 4 years reduces statistical power
  4. Modest forward returns: Signal-level mean 20d forward return ~0.32% (not FDR-significant)
  5. Volatility regime: Sensitive to market volatility conditions
  6. Bootstrap evidence: Confidence intervals included zero (not definitively significant)

Economic Intuition:
  Bollinger Band breakouts often precede trend acceleration. A breakout above
  the upper band indicates price has moved to an extreme, frequently causing
  continued directional momentum as other traders recognize the trend.

Dependencies:
  - Bollinger Bands (2 standard deviations) based on 20-day lookback
  - Daily OHLC data
  - No forward-looking feature engineering

Orthogonality Note:
  BB01 captures momentum/trend-following behavior. PB07 captures mean-reversion
  on value (low P/B). These strategies operate on opposite market regimes and
  show near-zero correlation (-0.0038), supporting portfolio diversification.
"""

import pandas as pd
import numpy as np


class BB01Strategy:
    """
    BB01 Bollinger Band Breakout Continuation Strategy.
    
    Signal: BB01 = 1 when price closes above the 2-std upper Bollinger Band.
    Construction: Long entry at t open, exit at t+20 close.
    """
    
    def __init__(self, entry_cost=0.0005, exit_cost=0.0005):
        """
        Initialize strategy with transaction costs.
        
        Args:
            entry_cost: Transaction cost at entry (default 0.05%)
            exit_cost: Transaction cost at exit (default 0.05%)
        """
        self.entry_cost = entry_cost
        self.exit_cost = exit_cost
        self.holding_days = 20
        self.trades = []
    
    def compute_signal(self, price_df):
        """
        Compute BB01 signal: 1 when close > upper Bollinger Band, 0 otherwise.
        
        Args:
            price_df: DataFrame with 'close' and 'high' columns
            
        Returns:
            Series with signal values (0 or 1)
        """
        # Compute 20-day rolling mean and std
        sma20 = price_df['close'].rolling(20).mean()
        std20 = price_df['close'].rolling(20).std()
        
        # Upper and lower bands (2 standard deviations)
        upper_band = sma20 + 2 * std20
        lower_band = sma20 - 2 * std20
        
        # Signal: 1 if close > upper band, 0 otherwise
        signal = (price_df['close'] > upper_band).astype(int)
        
        return signal
    
    def backtest(self, price_df, signal_df):
        """
        Run backtest using the BB01 signal.
        
        Args:
            price_df: DataFrame with 'date', 'open', 'close', 'high', 'low'
            signal_df: DataFrame with BB01 signal
            
        Returns:
            trades: List of trade dictionaries
            daily_returns: Series of daily returns
        """
        # Implementation would use the existing strategy_bb01.py logic
        # This is a reference implementation showing the strategy structure
        
        trades = []
        daily_returns = pd.Series(0.0, index=price_df.index)
        
        for i in range(len(signal_df) - self.holding_days):
            if signal_df.iloc[i] == 1:  # Signal at t-1
                entry_date = price_df.iloc[i + 1]['date']  # t
                entry_price = price_df.iloc[i + 1]['open']  # Entry at open
                
                exit_idx = i + 1 + self.holding_days
                exit_date = price_df.iloc[exit_idx]['date']
                exit_price = price_df.iloc[exit_idx]['close']  # Exit at close
                
                # Compute returns
                gross_return = (exit_price - entry_price) / entry_price
                costs = self.entry_cost + self.exit_cost
                net_return = gross_return - costs
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'gross_return': gross_return,
                    'costs': costs,
                    'net_return': net_return,
                    'holding_days': self.holding_days
                })
                
                # Mark daily returns at exit only
                daily_returns.iloc[exit_idx] = net_return
        
        return pd.DataFrame(trades), daily_returns


if __name__ == '__main__':
    print(__doc__)
