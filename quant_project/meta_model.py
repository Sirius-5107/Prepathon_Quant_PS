"""Low-capacity rolling alpha meta-model with a permutation allocation null."""
import numpy as np
import pandas as pd

class AlphaMetaModel:
    def __init__(self,null_reps=500,random_state=42):
        self.null_reps=int(null_reps); self.rng=np.random.default_rng(random_state); self.folds_=0
        self.capacity_="one trailing mean/vol score per strategy; no cross-strategy fitted parameters"

    @staticmethod
    def _scores(history):
        x=pd.DataFrame(history).astype(float); vol=x.std(ddof=0).replace(0,np.nan)
        return (x.mean()/vol).replace([np.inf,-np.inf],np.nan).fillna(0.0)

    def fit(self,strategy_history,market_state=None):
        self.train_scores_=self._scores(strategy_history); return self
    def predict(self,strategy_history,market_state=None): return self._scores(strategy_history)
    def score(self,scores):
        s=pd.Series(scores,dtype=float).clip(lower=0)
        return s/s.sum() if s.sum()>0 else pd.Series(1.0/len(s),index=s.index)
    def get_feature_importance(self): return self.train_scores_.sort_values(ascending=False).to_dict()
    def null_allocation_returns(self,train_returns,test_returns):
        scores=self._scores(train_returns); cols=list(scores.index); actual=self.score(scores).to_numpy()
        x=pd.DataFrame(test_returns)[cols].to_numpy(); observed=x@actual
        null_totals=[]
        for _ in range(self.null_reps):
            w=actual[self.rng.permutation(len(actual))]
            null_totals.append(float(np.prod(1+x@w)-1))
        return observed,np.asarray(null_totals)
    def report(self):
        return {"capacity_justification":self.capacity_,"wfo_folds":self.folds_,
                "null_baseline_permutations":self.null_reps,"model":"trailing mean / volatility"}
