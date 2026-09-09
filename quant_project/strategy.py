"""
Base strategy interface.
All strategies inherit from this and implement generate_signal.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str):
        self.name = name
        self.fitted = False
        self.metadata = {'name': name}
    
    def generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Define strategy inputs from signal library.
        
        data: DataFrame with columns 'date' + all signals (PB01-VB05)
        Must NOT use future price/volume data.
        """
        return data.copy()
    
    def generate_signal(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading decisions.
        
        Input:  DataFrame with rows up to and including t-1
        Output: Series of signals (1=long, 0=neutral, -1=short) for each row
        
        Must be deterministic given the inputs.
        Must NOT use data[t] or later.
        """
        raise NotImplementedError(f"{self.name} must implement generate_signal")
    
    def fit(self, data: pd.DataFrame, targets: pd.Series = None):
        """
        Fit parameters/models if applicable.
        
        targets: forward returns (for supervised learning)
        """
        self.fitted = True
    
    def predict(self, data: pd.DataFrame) -> pd.Series:
        """Produce strategy outputs (typically same as generate_signal)."""
        return self.generate_signal(data)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return strategy metadata."""
        return {
            'name': self.name,
            'fitted': self.fitted,
            **self.metadata
        }
