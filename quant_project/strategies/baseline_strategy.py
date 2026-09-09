"""
Baseline strategy: Simple trend following using PB01 and PB02.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from strategy import BaseStrategy


class BaselineTrendFollowing(BaseStrategy):
    """
    Simple trend-following strategy.
    
    Hypothesis: Recent trends persist over short horizons.
    Uses PB01 (short-term trend) and PB02 (longer-term trend).
    """
    
    def __init__(self):
        super().__init__("Baseline Trend Following")
        self.metadata = {
            'description': 'Long-only when both short and long-term trends positive',
            'signals_used': ['PB01', 'PB02'],
            'hypothesis': 'Trend persistence in price-based signals'
        }
    
    def generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Use supplied signals directly."""
        return data[['date', 'PB01', 'PB02']].copy()
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """
        Generate signal based on trend indicators.
        
        Long (1):  Both short-term and longer-term trends positive
        Neutral (0): Otherwise
        """
        if len(data) == 0:
            return 0
        
        # Get most recent signal values
        latest = data.iloc[-1]
        
        pb01 = latest['PB01']
        pb02 = latest['PB02']
        
        # Simple logic: both positive → long
        if pb01 == 1 and pb02 == 1:
            return 1
        else:
            return 0
