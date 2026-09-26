"""Shared helpers for signal-library-only Task 2 strategies."""
import numpy as np
import pandas as pd
from strategy import BaseStrategy

class FixedHorizonSignalStrategy(BaseStrategy):
    def __init__(self,name,horizon,direction):
        super().__init__(name); self.horizon=int(horizon); self.direction=int(direction)
    def fit(self,data,targets=None): self.fitted=True
    def _entry_mask(self,data): raise NotImplementedError
    def generate_features(self,data): return data[["date"]+self.required_signals].copy()
    def generate_signal(self,data):
        x=data.reset_index(drop=True).copy()
        mask=pd.Series(self._entry_mask(x),index=x.index).fillna(False).astype(bool)
        sig=pd.Series(0,index=x.index,dtype=int); next_free=0
        for i in np.flatnonzero(mask.to_numpy()):
            j=i+self.horizon
            if i<next_free or j>=len(sig): continue
            sig.iloc[i]=self.direction; sig.iloc[j]=-self.direction; next_free=j+1
        return sig
    def get_metadata(self):
        return {**super().get_metadata(),"predictive_inputs":self.required_signals,
                "holding_period_days":self.horizon,"transaction_cost_per_side":0.0005,
                "information_set":"supplied signal library only"}
