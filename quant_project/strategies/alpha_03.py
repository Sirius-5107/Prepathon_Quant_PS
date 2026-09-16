"""
Alpha Strategy 3: BB03 Binary Reversal Mean-Reversion

**STATUS: CANDIDATE STRATEGY — REJECTED**

This strategy was researched and implemented as a third candidate for the Task 2
portfolio but did NOT survive the final selection process. It is documented here
for completeness of the candidate set.

Hypothesis:
  Overbought oscillator state (BB03=1) indicates temporary excessive positive momentum
  that tends to mean-revert. Short positions over 10 days should capture this reversal.

Signal:
  BB03 = 1 when bounded momentum oscillator enters overbought territory (upper extreme).

Construction:
  - Entry: Short at open on day t (signal observed at close of t-1)
  - Exit: Cover (buy-to-close) at close on day t+10 (fixed 10-day holding period)
  - Position size: 1 unit (short-only)
  - Transaction cost: 0.05% per side

Holding Period: 10 trading days

Execution Convention:
  - Signal defined through t-1 only (no lookahead)
  - Entry at next candle open (short)
  - Exit at day 10 close (cover position)
  - Marked to market on every trading day
  - 0.05% entry cost + 0.05% exit cost = 0.10% round-trip

Research Period (2018-2021):
  Total observations: 758 trading days (108 overbought signals)
  
  Yearly Performance:
    2018: -0.122% (23 signals)
    2019: -0.004% (37 signals)
    2020: +0.526% (29 signals)
    2021: +0.013% (9 signals)
    
  Overall Statistics:
    Mean 10d forward return (BB03=1): -0.078%
    Mean 10d forward return (BB03=0): +0.044%
    Spread: -0.122% (negative as expected for short)
    Welch t-test: t ≈ -0.57, p ≈ 0.57 (NOT significant)
    Win rate: 52.8%

Known Failure Modes / Limitations:
  1. **Lack of statistical significance:** p-value ≈ 0.57 >> 0.05 threshold
  2. **Sparse signal events:** Only 108 signals over 4 years (0.03 per day)
  3. **Inconsistent yearly returns:** Positive only in 2020; minimal in other years
  4. **Modest magnitude:** -0.122% spread is small relative to transaction costs (0.10%)
  5. **Bootstrap evidence:** 95% CI includes zero; not definitively profitable
  6. **Regime dependence:** Sharp state detection depends on oscillator calibration
  7. **Multiple testing:** Did not survive FDR correction across signal library

Economic Intuition:
  Overbought conditions (extreme positive momentum) often precede mean-reversion.
  However, the evidence in this sample is insufficient to establish reliable short
  alpha. The spread magnitude (~-1.2 bps) is comparable to transaction costs,
  leaving no margin for error.

Orthogonality to BB01/PB07:
  BB03 attempts to capture mean-reversion via oscillator extremes. BB01 and PB07
  also exploit mean-reversion but via different mechanisms (Bollinger Bands and
  Price/Book extremes). All three operate in a similar conceptual family (reversals)
  and are NOT genuinely independent. Combining them risks stacking correlated noise
  rather than achieving true diversification.

Dependencies:
  - Bounded momentum oscillator (0-100 scale)
  - Overbought threshold: typically 70+ (upper extreme)
  - Daily OHLC data
  - No forward-looking feature engineering

Reasons for Rejection:
  1. Non-significant forward returns (p > 0.50)
  2. Tiny magnitude relative to costs
  3. Limited sample size (108 events)
  4. Correlation with existing strategies (not independent alpha)
  5. No out-of-sample validation showing robust edges
  6. Bootstrap CI includes zero

Comparison with Selected Strategies:
  BB01 (Bollinger Band breakout):    18.71% return, p ≈ 0.048
  PB07 (Price/Book Q1):              22.91% return, p ≈ 0.008
  BB03 (Overbought reversal):        -0.078% spread, p ≈ 0.57 ← NOT selected
"""

import pandas as pd
import numpy as np


class BB03Strategy:
    """
    BB03 Binary Reversal Mean-Reversion Strategy.
    
    Signal: BB03 = 1 when bounded momentum oscillator is in overbought state.
    Construction: Short entry at t open, cover at t+10 close.
    
    **STATUS: REJECTED CANDIDATE** — Documented for Task 2 completeness.
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
        self.holding_days = 10
        self.trades = []
        self.is_short = True  # Short strategy
    
    def compute_signal(self, oscillator_df):
        """
        Compute BB03 signal: 1 when oscillator > overbought threshold, 0 otherwise.
        
        Args:
            oscillator_df: DataFrame with bounded momentum oscillator (0-100 scale)
            
        Returns:
            Series with signal values (0 or 1)
        """
        # Overbought threshold: upper 30% (70+) of range
        overbought_threshold = 70
        
        # Signal: 1 if oscillator > threshold, 0 otherwise
        signal = (oscillator_df > overbought_threshold).astype(int)
        
        return signal
    
    def backtest(self, price_df, oscillator_df):
        """
        Run backtest using the BB03 signal (SHORT strategy).
        
        Args:
            price_df: DataFrame with 'date', 'open', 'close'
            oscillator_df: DataFrame with bounded momentum oscillator
            
        Returns:
            trades: List of trade dictionaries
            daily_returns: Series of daily returns
        """
        trades = []
        daily_returns = pd.Series(0.0, index=price_df.index)
        
        for i in range(len(price_df) - self.holding_days):
            signal = self.compute_signal(oscillator_df.iloc[i])
            
            if signal == 1:  # Signal at t-1 (overbought)
                entry_date = price_df.iloc[i + 1]['date']  # t
                entry_price = price_df.iloc[i + 1]['open']  # Short at open
                
                exit_idx = i + 1 + self.holding_days
                exit_date = price_df.iloc[exit_idx]['date']
                exit_price = price_df.iloc[exit_idx]['close']  # Cover at close
                
                # Compute SHORT returns (negative pnl if price rises)
                gross_return = (entry_price - exit_price) / entry_price
                costs = self.entry_cost + self.exit_cost
                net_return = gross_return - costs
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'direction': 'short',
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
