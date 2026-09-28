"""Simple interpretable factor model for Task 3."""
import numpy as np
import pandas as pd

class FactorModel:
    def __init__(self):
        self.alphas_, self.betas_, self.residuals_, self.factors_ = {}, {}, None, []

    def fit(self, strategy_returns, factors):
        R=pd.DataFrame(strategy_returns).astype(float)
        F=pd.DataFrame(factors,index=R.index).astype(float)
        X=np.column_stack([np.ones(len(F)),F.to_numpy()])
        residuals={}
        for col in R.columns:
            b=np.linalg.lstsq(X,R[col].to_numpy(),rcond=None)[0]
            self.alphas_[col]=float(b[0]); self.betas_[col]=b[1:].astype(float)
            residuals[col]=R[col].to_numpy()-X@b
        self.factors_=list(F.columns); self.residuals_=pd.DataFrame(residuals,index=R.index)
        return self

    def predict(self,strategy_returns,factors):
        F=pd.DataFrame(factors); X=np.column_stack([np.ones(len(F)),F.to_numpy()])
        return pd.DataFrame({c:X@np.r_[self.alphas_[c],self.betas_[c]] for c in pd.DataFrame(strategy_returns).columns},index=F.index)
    def get_alpha(self): return dict(self.alphas_)
    def get_beta(self): return dict(self.betas_)
    def get_residuals(self): return self.residuals_.copy()
    def report(self):
        return {"n_strategies":len(self.alphas_),"factors":self.factors_,"specification":"intercept + OLS","lookahead":"chronological alignment required"}
