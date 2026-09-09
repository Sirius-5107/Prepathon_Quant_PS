"""
Execution engine.
Handles order execution, transaction costs, slippage, and trade recording.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Trade:
    """Represent a single executed trade."""
    date: pd.Timestamp
    candle_idx: int
    signal: int  # 1, 0, -1
    quantity: float
    entry_price: float
    entry_cost: float
    status: str  # 'entry' or 'exit'
    
    def to_dict(self) -> dict:
        return {
            'date': self.date,
            'candle_idx': self.candle_idx,
            'signal': self.signal,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'entry_cost': self.entry_cost,
            'status': self.status,
        }


class ExecutionEngine:
    """Simulate trade execution with costs."""
    
    TRANSACTION_COST_PER_SIDE = 0.0005  # 0.05% per side (mandatory)
    
    def __init__(self, initial_capital: float = 1e6):
        self.initial_capital = initial_capital
        self.trades = []
        self.execution_log = []
    
    def execute(self, signal: pd.Series, price_df: pd.DataFrame) -> List[Trade]:
        """
        Simulate execution.
        
        signal: Series indexed by candle, values in {-1, 0, 1}
        price_df: OHLCV data sorted chronologically with open prices for execution
        
        Returns: List of Trade objects
        """
        self.trades = []
        
        for idx in range(len(signal)):
            sig = signal.iloc[idx]
            
            if sig == 0:
                continue  # No trade
            
            date = price_df.iloc[idx]['date']
            candle_idx = idx
            
            # Execute at open price (per timing convention)
            exec_price = price_df.iloc[idx]['open']
            
            # Calculate transaction cost: 0.05% per side
            quantity = 1  # Unit position
            notional = abs(quantity * exec_price)
            trans_cost = notional * self.TRANSACTION_COST_PER_SIDE
            
            trade = Trade(
                date=date,
                candle_idx=candle_idx,
                signal=sig,
                quantity=quantity,
                entry_price=exec_price,
                entry_cost=trans_cost,
                status='entry'
            )
            
            self.trades.append(trade)
            self.execution_log.append(trade.to_dict())
        
        return self.trades
    
    def apply_transaction_cost(self, trades: List[Trade]) -> float:
        """Calculate total transaction costs."""
        return sum([t.entry_cost for t in trades])
    
    def apply_slippage(self, trades: List[Trade], slippage_bps: float = 0.0) -> float:
        """
        Apply execution slippage (basis points).
        Default: 0 (not modeled; could be extended).
        """
        if slippage_bps == 0:
            return 0.0
        
        total_slippage = 0.0
        for trade in trades:
            notional = abs(trade.quantity * trade.entry_price)
            slippage_cost = notional * (slippage_bps / 10000)
            total_slippage += slippage_cost
        
        return total_slippage
    
    def record_trade(self, trade: Trade):
        """Record an executed trade."""
        self.trades.append(trade)
    
    def get_trade_log(self) -> pd.DataFrame:
        """Return trade history as DataFrame."""
        if not self.execution_log:
            return pd.DataFrame()
        
        return pd.DataFrame(self.execution_log)
