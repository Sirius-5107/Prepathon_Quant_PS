"""Alpha 04: learned mean-reversion composite using supplied signals only."""
import numpy as np
import pandas as pd
from strategy import BaseStrategy
class Alpha04(BaseStrategy):
    required_signals=["BB03","PB07","BB04"]
    def __init__(self,horizon=10):
        super().__init__("MeanReversion_Composite_10D"); self.horizon=horizon; self.weights_=np.array([-1.,1.,1.])
    def generate_features(self,data): return data[["date"]+self.required_signals].copy()
    def _features(self,data):
        X=data[self.required_signals].astype(float).copy()
        med=X["PB07"].median(); scale=np.median(np.abs(X["PB07"]-med))+1e-12
        X["PB07"]=((med-X["PB07"])/scale).clip(-5,5)
        return X
    def fit(self,data,targets=None):
        X=self._features(data)
        if targets is not None:
            y=pd.Series(targets,index=data.index,dtype=float)
            z=X.replace([np.inf,-np.inf],np.nan).dropna(); y=y.loc[z.index].dropna(); z=z.loc[y.index]
            if len(z)>=40:
                beta=np.linalg.lstsq(z.to_numpy(),y.to_numpy(),rcond=None)[0]
                if np.all(np.isfinite(beta)): self.weights_=beta
        self.fitted=True
    def generate_signal(self,data):
        x=data.reset_index(drop=True).copy(); X=self._features(x)
        score=X.to_numpy()@self.weights_
        sig=pd.Series(0,index=x.index,dtype=int); used=set()
        for i in np.flatnonzero(np.abs(score)>0):
            j=i+self.horizon
            if j<len(sig) and i not in used:
                sig.iloc[i]=1 if score[i]>0 else -1
                sig.iloc[j]=-sig.iloc[i]; used.update((i,j))
        return sig
    def get_metadata(self):
        return {**super().get_metadata(),"predictive_inputs":self.required_signals,
                "weights_training_only":True,"selection":"OLS fit on training forward returns"}
