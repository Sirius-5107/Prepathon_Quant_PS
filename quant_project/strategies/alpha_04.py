"""Alpha 04: learned mean-reversion composite using supplied signals only."""
import numpy as np
import pandas as pd
from strategy import BaseStrategy
class Alpha04(BaseStrategy):
    required_signals=["BB03","PB07","BB04"]
    def __init__(self,horizon=10):
        super().__init__("MeanReversion_Composite_10D"); self.horizon=horizon; self.weights_=np.array([-1.,1.,1.]); self.pb_median_=0.; self.pb_scale_=1.
    def generate_features(self,data): return data[["date"]+self.required_signals].copy()
    def _features(self,data):
        X=data[self.required_signals].astype(float).copy()
        X["PB07"]=((self.pb_median_-X["PB07"])/(self.pb_scale_+1e-12)).clip(-5,5)
        return X
    def fit(self,data,targets=None):
        raw=data[self.required_signals].astype(float)
        self.pb_median_=float(raw["PB07"].median())
        self.pb_scale_=float(np.median(np.abs(raw["PB07"]-self.pb_median_))+1e-12)
        X=self._features(data)
        if targets is not None:
            y=pd.Series(targets,index=data.index,dtype=float)
            z=X.replace([np.inf,-np.inf],np.nan).dropna(); y=y.loc[z.index].dropna(); z=z.loc[y.index]
            if len(z)>=40:
                beta=np.linalg.lstsq(z.to_numpy(),y.to_numpy(),rcond=None)[0]
                if np.all(np.isfinite(beta)): self.weights_=beta
        self.fitted=True
    def generate_signal(self,data):
        x=data.reset_index(drop=True).copy(); X=self._features(x); score=X.to_numpy()@self.weights_
        sig=pd.Series(0,index=x.index,dtype=int); next_free=0
        for i in np.flatnonzero(np.isfinite(score) & (np.abs(score)>0)):
            j=i+self.horizon
            if i<next_free or j>=len(sig): continue
            sig.iloc[i]=1 if score[i]>0 else -1; sig.iloc[j]=-sig.iloc[i]; next_free=j+1
        return sig
    def get_metadata(self):
        return {**super().get_metadata(),"predictive_inputs":self.required_signals,
                "weights_training_only":True,"training_pb_transform":"median/MAD-like robust scale"}
