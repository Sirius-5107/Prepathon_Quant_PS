"""
Portfolio accounting.
Tracks positions, equity value, and P&L.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple


class Portfolio:
    """Track portfolio state and performance."""
    
    def __init__(self, initial_capital: float = 1e6):
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.current_position = 0  # net position in units
        self.equity_history = [initial_capital]
        self.position_history = [0]
        self.date_history = []
        self.pnl_history = []
        self.mark_to_market_price = None
    
    def update(self, executions: List[Dict]) -> float:
        """
        Update portfolio state from executed trades.
        
        executions: List of trade dictionaries with 'signal', 'quantity', 'entry_price', 'entry_cost'
        """
        for execution in executions:
            signal = execution['signal']
            quantity = execution['quantity']
            entry_price = execution['entry_price']
            entry_cost = execution['entry_cost']
            
            # Update position
            if signal == 1:  # Long
                self.current_position += quantity
                cost = quantity * entry_price + entry_cost
                self.current_cash -= cost
            elif signal == -1:  # Short
                self.current_position -= quantity
                proceeds = quantity * entry_price - entry_cost
                self.current_cash += proceeds
            
            # Record
            self.position_history.append(self.current_position)
        
        # Return current equity
        return self.get_equity()
    
    def mark_to_market(self, market_data: pd.DataFrame):
        """Mark positions to market at given prices."""
        if len(market_data) == 0:
            return
        
        # Use close price from most recent candle
        self.mark_to_market_price = market_data.iloc[-1]['close']
    
    def get_equity_curve(self) -> List[float]:
        """Return portfolio value history."""
        return self.equity_history
    
    def get_positions(self) -> List[float]:
        """Return position history."""
        return self.position_history
    
    def get_pnl(self) -> pd.Series:
        """Return P&L series."""
        if not self.equity_history:
            return pd.Series([])
        
        returns = [(self.equity_history[i] - self.equity_history[i-1]) / self.equity_history[i-1]
                   for i in range(1, len(self.equity_history))]
        
        return pd.Series(returns)
    
    def get_equity(self, current_price: float = None) -> float:
        """
        Calculate current equity.
        
        equity = cash + (position * current_price)
        """
        if current_price is None:
            current_price = self.mark_to_market_price if self.mark_to_market_price else 0
        
        position_value = self.current_position * current_price
        return self.current_cash + position_value
