"""
Data cleaning and preprocessing.
Handles missing values, chronological ordering, duplicates.
"""

import pandas as pd
import numpy as np
from typing import Tuple


class DataCleaner:
    """Clean and prepare research data."""
    
    def __init__(self):
        self.cleaning_report = {}
    
    def validate(self, signals: pd.DataFrame, price: pd.DataFrame) -> dict:
        """Check data quality and report issues."""
        report = {}
        
        # Signals validation
        report['signals_missing'] = signals.isna().sum().to_dict()
        report['signals_duplicates'] = signals['date'].duplicated().sum()
        
        # Price validation
        report['price_missing'] = price.isna().sum().to_dict()
        report['price_duplicates'] = price['date'].duplicated().sum()
        report['price_nonsensical'] = {
            'high_lt_low': (price['high'] < price['low']).sum(),
            'close_lt_low': (price['close'] < price['low']).sum(),
            'close_gt_high': (price['close'] > price['high']).sum(),
            'open_lt_low': (price['open'] < price['low']).sum(),
            'open_gt_high': (price['open'] > price['high']).sum(),
        }
        
        self.cleaning_report = report
        return report
    
    def clean(self, signals: pd.DataFrame, price: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Return research-ready data."""
        # Sort chronologically
        signals = self.sort_chronologically(signals)
        price = self.sort_chronologically(price)
        
        # Remove duplicates (keep first occurrence)
        signals = self.remove_duplicates(signals)
        price = self.remove_duplicates(price)
        
        # Handle missing values
        signals = self.handle_missing(signals, is_signals=True)
        price = self.handle_missing(price, is_signals=False)
        
        # Reset index after cleaning
        signals = signals.reset_index(drop=True)
        price = price.reset_index(drop=True)
        
        return signals, price
    
    def sort_chronologically(self, data: pd.DataFrame) -> pd.DataFrame:
        """Enforce time order."""
        return data.sort_values('date').reset_index(drop=True)
    
    def handle_missing(self, data: pd.DataFrame, is_signals: bool = True) -> pd.DataFrame:
        """Handle missing observations."""
        data = data.copy()
        
        if is_signals:
            # For boolean signals (0/1), fill with forward fill then backward fill
            bool_cols = [col for col in data.columns if col != 'date']
            for col in bool_cols:
                # Count NaN before and after
                before_nan = data[col].isna().sum()
                # Forward fill, then backward fill for leading NaNs
                data[col] = data[col].ffill().bfill()
                after_nan = data[col].isna().sum()
        else:
            # For price data, don't forward fill (missing trading day)
            # Just track which dates are missing and handle in backtester
            pass
        
        return data
    
    def remove_duplicates(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle duplicate observations."""
        before = len(data)
        data = data.drop_duplicates(subset=['date'], keep='first')
        after = len(data)
        
        if before > after:
            print(f"Removed {before - after} duplicate dates")
        
        return data
    
    def get_report(self) -> dict:
        """Return cleaning report."""
        return self.cleaning_report
