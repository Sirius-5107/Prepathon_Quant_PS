"""
Data loading and validation for quant research.
Handles signals and price data with schema validation.
"""

import pandas as pd
import numpy as np
from typing import Tuple


class DataLoader:
    """Load and validate research data."""
    
    SIGNAL_COLUMNS = [
        'PB01', 'PB02', 'PB03', 'PB04', 'PB05', 'PB06', 'PB07', 'PB08',
        'BB01', 'BB02', 'BB03', 'BB04', 'BB05', 'BB06', 'BB07',
        'VB01', 'VB02', 'VB03', 'VB04', 'VB05'
    ]
    
    PRICE_COLUMNS = ['open', 'high', 'low', 'close', 'volume']
    
    def __init__(self):
        self.signals_df = None
        self.price_df = None
        self.validation_report = {}
    
    def load(self, signals_path: str, price_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load and validate signals and price data."""
        # Load signals
        self.signals_df = pd.read_csv(signals_path)
        self.signals_df['date'] = pd.to_datetime(self.signals_df['date'], format='%Y-%m-%d')
        
        # Load price with mixed format handling
        self.price_df = pd.read_csv(price_path)
        self.price_df['date'] = pd.to_datetime(self.price_df['date'], format='mixed', dayfirst=True)
        
        self.validate_schema(self.signals_df, is_signals=True)
        self.validate_schema(self.price_df, is_signals=False)
        
        return self.signals_df.copy(), self.price_df.copy()
    
    def validate_schema(self, data: pd.DataFrame, is_signals: bool = True):
        """Validate data structure and columns."""
        if is_signals:
            required = ['date'] + self.SIGNAL_COLUMNS
            df_name = 'signals'
        else:
            required = ['date'] + self.PRICE_COLUMNS
            df_name = 'price'
        
        missing = [col for col in required if col not in data.columns]
        if missing:
            raise ValueError(f"{df_name}: Missing columns {missing}")
        
        if data['date'].isna().any():
            raise ValueError(f"{df_name}: Contains NaT in date column")
        
        self.validation_report[df_name] = {
            'rows': len(data),
            'columns': len(data.columns),
            'date_range': (data['date'].min(), data['date'].max())
        }
    
    def get_report(self) -> dict:
        """Return validation report."""
        return self.validation_report
