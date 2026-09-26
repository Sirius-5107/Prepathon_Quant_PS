"""Alpha 04: BB03/PB07/BB04 mean-reversion composite using signals only."""
import numpy as np
import pandas as pd
from strategy import BaseStrategy
class Alpha04(BaseStrategy):
    required_signals=["BB03","PB07","BB04"]
    def __init__(self,horizon=10):
        super().__init__("MeanReversion_Composite_10D"); self.horizon=horizon; self.weights_=np.array([-1.0,1.0,1.0])
    def generate_features(self,data): return data[["date"]+self.required_signals].copy()
    def fit(self,data,targets=None):
        X=data[self.required_signals].astype(float).copy()
        pb=(X["PB07"]-X["PB07"].median())/(X["PB07"].mad()+1e-12)
        X["PB07"]=pb.clip(-5,5)
        y=pd.Series(targets,index=data.index,dtype=float) if targets is not None else None
        if y is not None:
            z=X.replace([np.inf,-np.inf],np.nan).dropna()
            yy=y.loc[z.index].dropna()
            z=z.loc[yy.index]
            if len(z)>=40:
                beta=np.linalg.lstsq(z.to_numpy(),yy.to_numpy(),rcond=None)[0]
                if np.all(np.isfinite(beta)): self.weights_=beta
        self.fitted=True
    def generate_signal(self,data):
        x=data.reset_index(drop=True).copy()
        pb=x["PB07"].astype(float)
        scale=pb.rolling(min(60,len(pb)),min_periods=20).median()
        mad=(pb-scale).abs().rolling(min(60,len(pb)),min_periods=20).median()
        pbn=((scale-pb)/(mad+1e-9)).clip(-5,5)
        score=(-self.weights_[0]*x["BB03"].astype(float)+self.weights_[1]*pbn+self.weights_[2]*x["BB04"].astype(float))
        entry=score>0
        sig=pd.Series(0,index=x.index,dtype=int); used=set()
        for i in np.flatnonzero(entry.to_numpy()):
            j=i+self.horizon
            if j<len(sig) and i not in used:
                sig.iloc[i]=1; sig.iloc[j]=-1; used|={i,j}
        return sig
    def get_metadata(self): return {**super().get_metadata(),"predictive_inputs":self.required_signals,"selection":"research composite; weights learned on training data only"}
