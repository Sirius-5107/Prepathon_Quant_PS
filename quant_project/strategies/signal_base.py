"""Shared helpers for signal-library-only Task 2 strategies."""
import numpy as np
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from strategy import BaseStrategy

class FixedHorizonSignalStrategy(BaseStrategy):
    def __init__(self, name, horizon, direction):
        super().__init__(name)
        self.horizon=int(horizon); self.direction=int(direction)
    def fit(self, data, targets=None):
        self.fitted=True
    def _entry_mask(self, data):
        raise NotImplementedError
    def generate_features(self, data):
        return data[["date"] + self.required_signals].copy()
    def generate_signal(self, data):
        x=data.reset_index(drop=True).copy()
        mask=pd.Series(self._entry_mask(x), index=x.index).fillna(False).astype(bool)
        sig=pd.Series(0,index=x.index,dtype=int)
        used=set()
        for i in np.flatnonzero(mask.to_numpy()):
            if i in used: continue
            j=i+self.horizon
            if j >= len(sig): continue
            sig.iloc[i]=self.direction
            sig.iloc[j]=-self.direction
            used.add(i)
            used.add(j)
        return sig
    def get_metadata(self):
        return {**super().get_metadata(),"predictive_inputs":self.required_signals,
                "holding_period_days":self.horizon,"transaction_cost_per_side":0.0005,
                "information_set":"supplied signal library only"}

def causal_tail_threshold(series, q=0.20, min_obs=60):
    s=pd.Series(series,dtype=float)
    out=pd.Series(np.nan,index=s.index)
    for i in range(len(s)):
        hist=s.iloc[:i].dropna()
        if len(hist)>=min_obs:
            out.iloc[i]=hist.quantile(q)
    return out
