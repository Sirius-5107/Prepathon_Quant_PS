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
        if method=="equal_weight":
            w=np.ones(n)/n
        elif method=="erc":
            sigma=(self.risk_model_+self.risk_model_.T)/2 + np.eye(n)*1e-12
            eps=max(self.min_weight,1e-8)
            def loss(x):
                rc=np.maximum(x*(sigma@x),eps)
                z=np.log(rc)
                return float(np.sum((z-z.mean())**2))
            x0=1/np.sqrt(np.maximum(np.diag(sigma),1e-12)); x0=x0/x0.sum()
            res=minimize(loss,x0,bounds=[(eps,self.max_weight)]*n,
                         constraints={"type":"eq","fun":lambda x:np.sum(x)-1},
                         method="SLSQP",options={"maxiter":2000,"ftol":1e-12})
            if not res.success: raise RuntimeError(f"ERC optimization failed: {res.message}")
            w=res.x
        elif method=="max_sharpe":
            mu=self.returns_.mean(axis=0); cov=(self.risk_model_+self.risk_model_.T)/2
            eps=max(self.min_weight,1e-8)
            def objective(x):
                return -float(mu@x)/float(np.sqrt(max(x@cov@x,1e-16)))
            res=minimize(objective,np.ones(n)/n,bounds=[(eps,self.max_weight)]*n,
                         constraints={"type":"eq","fun":lambda x:np.sum(x)-1},
                         method="SLSQP",options={"maxiter":2000,"ftol":1e-12})
            if not res.success: raise RuntimeError(f"Max-Sharpe optimization failed: {res.message}")
            w=res.x
        else:
            raise ValueError("method must be equal_weight, erc, or max_sharpe")
        w=np.maximum(w,0.0); w=w/w.sum(); self.weights_=w; return w

    def evaluate(self,weights):
        r=self.returns_@np.asarray(weights); eq=np.cumprod(1+r)
        return {"total_return":float(eq[-1]-1),"annual_vol":float(r.std()*np.sqrt(252)),
                "sharpe":float(r.mean()/(r.std()+1e-12)*np.sqrt(252)),
                "max_drawdown":float(np.min(eq/np.maximum.accumulate(eq)-1))}

    def get_weights(self): return None if self.weights_ is None else self.weights_.copy()

    def report(self):
        return {"methods":["equal_weight","erc","max_sharpe"],"long_only":True,
                "erc_definition":"equalized component risk w_i*(Sigma w)_i",
                "max_sharpe_scope":"full-sample descriptive only"}
