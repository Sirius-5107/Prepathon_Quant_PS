"""Alpha 05: signal-library regime filter for BB03 reversal."""
import numpy as np
import pandas as pd
from strategy import BaseStrategy
class Alpha05(BaseStrategy):
    required_signals=["BB03","VB02"]
    def __init__(self,horizon=10):
        super().__init__("BB03_RegimeFiltered_10D"); self.horizon=horizon; self.vb02_threshold_=None
    def generate_features(self,data): return data[["date"]+self.required_signals].copy()
    def fit(self,data,targets=None):
        self.vb02_threshold_=data["VB02"].astype(float).dropna().quantile(.50)
        self.fitted=True
    def generate_signal(self,data):
        x=data.reset_index(drop=True).copy()
        if self.vb02_threshold_ is None: self.fit(x)
        entry=(x["BB03"].astype(float)>0)&(x["VB02"].astype(float)<=self.vb02_threshold_)
        sig=pd.Series(0,index=x.index,dtype=int); used=set()
        for i in np.flatnonzero(entry.to_numpy()):
            j=i+self.horizon
            if j<len(sig) and i not in used:
                sig.iloc[i]=-1; sig.iloc[j]=1; used|={i,j}
        return sig
    def get_metadata(self): return {**super().get_metadata(),"predictive_inputs":self.required_signals,"context_signal":"VB02","threshold":"training median"}
