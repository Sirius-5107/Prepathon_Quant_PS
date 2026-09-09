"""
Backtester orchestrating data → signals → execution → portfolio → analysis.
Enforces timing convention and lookahead prevention.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from strategy import BaseStrategy
from execution_engine import ExecutionEngine
from portfolio import Portfolio
from performance import PerformanceAnalyzer


class Backtester:
    """Run historical simulation with proper timing and costs."""
    
    def __init__(self, initial_capital: float = 1e6):
        self.initial_capital = initial_capital
        self.signals = None
        self.price_df = None
        self.strategy = None
        self.execution_engine = None
        self.portfolio = None
        self.analyzer = None
        self.results = {}
    
    def run(self, price_df: pd.DataFrame, signals_df: pd.DataFrame, 
            strategy: BaseStrategy) -> Dict[str, Any]:
        """
        Run a historical simulation.
        
        Timing convention:
        - At candle t: use signals available through candle t-1
        - Generate trading signal for candle t
        - Execute at candle t's open price
        - Mark to market at candle t's close
        """
        self.price_df = price_df.sort_values('date').reset_index(drop=True)
        self.signals_df = signals_df.sort_values('date').reset_index(drop=True)
        self.strategy = strategy
        
        # Align signals and price by date
        merged = self._align_data()
        if len(merged) == 0:
            raise ValueError("No overlapping dates between signals and price data")
        
        # Generate signals (enforcing t-1 cutoff)
        all_signals = self.generate_signals(merged)
        
        # Execute signals
        executions = self.execute_signals(all_signals, merged)
        
        # Update portfolio
        self.update_portfolio(executions, merged)
        
        # Analyze
        return self.analyze(merged)
    
    def _align_data(self) -> pd.DataFrame:
        """Merge signals and price by date."""
        merged = pd.merge(
            self.signals_df,
            self.price_df,
            on='date',
            how='inner'
        )
        return merged.sort_values('date').reset_index(drop=True)
    
    def generate_signals(self, merged: pd.DataFrame) -> pd.Series:
        """
        Generate strategy decisions respecting timing convention.
        
        For candle t: use signals from rows 0..t-1 only.
        """
        signals = []
        
        # Get signal columns only
        signal_cols = [col for col in self.signals_df.columns if col != 'date']
        
        for t in range(len(merged)):
            # Inputs: rows 0..t-1 (signal values available through yesterday)
            if t == 0:
                # First candle: no historical data, neutral
                sig = 0
            else:
                # Use historical data up to t-1
                inputs = merged.iloc[:t][signal_cols].copy()
                # Add date column for context
                inputs['date'] = merged.iloc[:t]['date'].values
                
                # Generate signal
                sig = self.strategy.generate_signal(inputs)
                
                # Signal should be scalar or Series; extract if needed
                if isinstance(sig, pd.Series):
                    sig = sig.iloc[-1]  # Take last value
            
            signals.append(sig)
        
        return pd.Series(signals, index=merged.index)
    
    def execute_signals(self, signals: pd.Series, merged: pd.DataFrame) -> List[Dict]:
        """
        Simulate signal execution.
        
        Execute at candle t's open price (the price at which trade would fill).
        """
        self.execution_engine = ExecutionEngine(self.initial_capital)
        trades = self.execution_engine.execute(signals, merged)
        
        # Convert to list of dicts for portfolio
        executions = [t.to_dict() for t in trades]
        
        return executions
    
    def update_portfolio(self, executions: List[Dict], merged: pd.DataFrame):
        """Update portfolio with executed trades."""
        self.portfolio = Portfolio(self.initial_capital)
        
        # Track equity at each candle
        equity_values = [self.initial_capital]
        
        for idx, row in merged.iterrows():
            # Trades executed at this candle
            candle_trades = [e for e in executions if e['candle_idx'] == idx]
            
            if candle_trades:
                self.portfolio.update(candle_trades)
            
            # Mark to market at close
            current_equity = self.portfolio.get_equity(row['close'])
            equity_values.append(current_equity)
        
        # Store equity curve
        self.portfolio.equity_history = equity_values
    
    def analyze(self, merged: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance."""
        equity_series = pd.Series(self.portfolio.equity_history)
        
        self.analyzer = PerformanceAnalyzer(equity_series)
        perf_report = self.analyzer.report()
        
        # Add trade statistics
        trade_log = self.execution_engine.get_trade_log()
        
        self.results = {
            'performance': perf_report,
            'equity_curve': self.portfolio.equity_history,
            'trades': trade_log,
            'portfolio': self.portfolio,
            'analyzer': self.analyzer,
        }
        
        return self.results
    
    def get_results(self) -> Dict[str, Any]:
        """Return backtest results."""
        return self.results
