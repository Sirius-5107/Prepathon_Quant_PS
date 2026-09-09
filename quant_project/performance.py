"""
Performance analysis and metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


class PerformanceAnalyzer:
    """Analyze strategy and portfolio performance."""
    
    def __init__(self, equity_curve: pd.Series, returns: pd.Series = None, 
                 risk_free_rate: float = 0.02):
        self.equity_curve = equity_curve
        self.risk_free_rate = risk_free_rate
        
        if returns is None:
            # Compute returns from equity curve
            self.returns = equity_curve.pct_change().dropna()
        else:
            self.returns = returns
    
    def total_return(self) -> float:
        """Total return (%)."""
        if len(self.equity_curve) < 2:
            return 0.0
        return (self.equity_curve.iloc[-1] / self.equity_curve.iloc[0] - 1) * 100
    
    def annualized_return(self, periods_per_year: int = 252) -> float:
        """Annualized return (%)."""
        total_ret = self.equity_curve.iloc[-1] / self.equity_curve.iloc[0]
        years = len(self.returns) / periods_per_year
        
        if years == 0:
            return 0.0
        
        ann_ret = (total_ret ** (1 / years) - 1) * 100
        return ann_ret
    
    def volatility(self, periods_per_year: int = 252) -> float:
        """Volatility (%)."""
        if len(self.returns) < 2:
            return 0.0
        
        daily_vol = self.returns.std()
        ann_vol = daily_vol * np.sqrt(periods_per_year)
        return ann_vol * 100
    
    def sharpe_ratio(self, periods_per_year: int = 252) -> float:
        """Sharpe ratio."""
        if len(self.returns) < 2:
            return 0.0
        
        excess_return = self.annualized_return(periods_per_year) / 100 - self.risk_free_rate
        vol = self.volatility(periods_per_year) / 100
        
        if vol == 0:
            return 0.0
        
        return excess_return / vol
    
    def sortino_ratio(self, periods_per_year: int = 252) -> float:
        """Sortino ratio (downside volatility)."""
        if len(self.returns) < 2:
            return 0.0
        
        excess_return = self.annualized_return(periods_per_year) / 100 - self.risk_free_rate
        
        # Downside volatility (only negative returns)
        downside_returns = self.returns[self.returns < 0]
        if len(downside_returns) == 0:
            downside_vol = 0
        else:
            downside_vol = downside_returns.std() * np.sqrt(periods_per_year)
        
        if downside_vol == 0:
            return 0.0
        
        return excess_return / downside_vol
    
    def max_drawdown(self) -> float:
        """Maximum drawdown (%)."""
        if len(self.equity_curve) < 2:
            return 0.0
        
        cummax = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - cummax) / cummax
        
        return drawdown.min() * 100
    
    def drawdown_duration(self) -> int:
        """Maximum drawdown duration (days)."""
        if len(self.equity_curve) < 2:
            return 0
        
        cummax = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - cummax) / cummax
        
        # Find longest sequence of non-zero drawdown
        in_drawdown = (drawdown < 0).astype(int)
        
        # Find consecutive 1s
        changes = in_drawdown.diff().fillna(0)
        starts = (changes == 1).cumsum()
        
        if starts.max() == 0:
            return 0
        
        durations = in_drawdown.groupby(starts).sum()
        return int(durations.max())
    
    def calmar_ratio(self, periods_per_year: int = 252) -> float:
        """Calmar ratio = annual return / max drawdown."""
        ann_ret = self.annualized_return(periods_per_year) / 100
        max_dd = abs(self.max_drawdown() / 100)
        
        if max_dd == 0:
            return 0.0
        
        return ann_ret / max_dd
    
    def trade_statistics(self, trades: pd.DataFrame = None) -> Dict[str, Any]:
        """Trade-level statistics."""
        if trades is None or len(trades) == 0:
            return {}
        
        return {
            'total_trades': len(trades),
            'avg_profit_per_trade': 0,  # Placeholder
            'win_rate': 0,  # Placeholder
        }
    
    def report(self) -> Dict[str, Any]:
        """Combined performance report."""
        return {
            'total_return_%': self.total_return(),
            'annualized_return_%': self.annualized_return(),
            'volatility_%': self.volatility(),
            'sharpe_ratio': self.sharpe_ratio(),
            'sortino_ratio': self.sortino_ratio(),
            'max_drawdown_%': self.max_drawdown(),
            'calmar_ratio': self.calmar_ratio(),
        }
