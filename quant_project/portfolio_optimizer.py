"""Long-only portfolio optimization utilities for Task 3."""
import numpy as np
from scipy.optimize import minimize

class PortfolioOptimizer:
    def __init__(self,min_weight=0.0,max_weight=1.0):
        self.min_weight=float(min_weight); self.max_weight=float(max_weight); self.weights_=None

    def fit(self,strategy_returns,risk_model=None,constraints=None):
        self.returns_=np.asarray(strategy_returns,float)
        self.risk_model_=np.asarray(risk_model if risk_model is not None else np.cov(self.returns_,rowvar=False,ddof=1),float)
        self.constraints_=constraints or {}; return self

    def optimize(self,method="erc"):
        n=self.risk_model_.shape[0]
        if method=="equal_weight": w=np.ones(n)/n
        elif method=="erc":
            def loss(x):
                rc=x*(self.risk_model_@x); return float(np.sum((rc-rc.mean())**2))
            res=minimize(loss,np.ones(n)/n,bounds=[(self.min_weight,self.max_weight)]*n,
                         constraints={"type":"eq","fun":lambda x:np.sum(x)-1},method="SLSQP")
            w=res.x if res.success else np.ones(n)/n
        else: raise ValueError("method must be equal_weight or erc")
        w=np.maximum(w,self.min_weight); w=w/w.sum(); self.weights_=w; return w

    def evaluate(self,weights):
        r=self.returns_@np.asarray(weights); eq=np.cumprod(1+r)
        return {"total_return":float(eq[-1]-1),"annual_vol":float(r.std()*np.sqrt(252)),
                "sharpe":float(r.mean()/(r.std()+1e-12)*np.sqrt(252)),
                "max_drawdown":float(np.min(eq/np.maximum.accumulate(eq)-1))}
    def get_weights(self): return None if self.weights_ is None else self.weights_.copy()
    def report(self): return {"methods":["equal_weight","erc"],"long_only":True}
