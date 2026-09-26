"""Alpha 05: BB03 reversal filtered by supplied VB02 context."""
import numpy as np
import pandas as pd
from strategy import BaseStrategy
class Alpha05(BaseStrategy):
    required_signals=["BB03","VB02"]
    def __init__(self,horizon=10):
        super().__init__("BB03_RegimeFiltered_10D"); self.horizon=horizon; self.threshold_=None
    def generate_features(self,data): return data[["date"]+self.required_signals].copy()
    def fit(self,data,targets=None):
        self.threshold_=float(data["VB02"].astype(float).dropna().quantile(.50)); self.fitted=True
    def generate_signal(self,data):
        x=data.reset_index(drop=True).copy()
        if self.threshold_ is None: self.fit(x)
        entry=(x["BB03"].astype(float)>0)&(x["VB02"].astype(float)<=self.threshold_)
        sig=pd.Series(0,index=x.index,dtype=int); next_free=0
        for i in np.flatnonzero(entry.to_numpy()):
            j=i+self.horizon
            if i<next_free or j>=len(sig): continue
            sig.iloc[i]=-1; sig.iloc[j]=1; next_free=j+1
        return sig
    def get_metadata(self):
        return {**super().get_metadata(),"predictive_inputs":self.required_signals,
                "context_signal":"VB02","threshold":"training-window median"}
