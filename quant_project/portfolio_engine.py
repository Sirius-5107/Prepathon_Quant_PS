"""Generic Task 3 portfolio engine over the corrected nine-strategy return matrix."""
from pathlib import Path
import numpy as np
import pandas as pd

class PortfolioEngine:
    def __init__(self,data_dir="research_output"):
        df=pd.read_csv(Path(data_dir)/"portfolio_daily_returns.csv",parse_dates=["date"]).sort_values("date")
        if df["date"].duplicated().any(): raise ValueError("Duplicate dates")
        self.dates=pd.DatetimeIndex(df["date"]); self.n_obs=len(df)
        self.strategy_names=[c for c in df.columns if c!="date"]
        if len(self.strategy_names)<3: raise AssertionError("Task 3 requires the corrected multi-strategy return matrix")
        self.returns=df[self.strategy_names].astype(float)
        if self.returns.isna().any().any(): raise AssertionError("Canonical returns contain NaNs")
        if (self.returns<=-1).any().any(): raise AssertionError("Return <= -100% is invalid")
        if self.n_obs!=986: raise AssertionError(f"Expected 986 observations, found {self.n_obs}")
        self.bb01_returns=self.returns["BB01_Breakout_20D"].to_numpy()
        self.pb07_returns=self.returns["PB07_TailReversal_10D"].to_numpy()

    @staticmethod
    def metrics(returns):
        r=np.asarray(returns,float); eq=np.cumprod(1+r)
        return {"total_return":float(eq[-1]-1),"cagr":float(eq[-1]**(252/len(r))-1),
                "annual_vol":float(r.std(ddof=0)*np.sqrt(252)),
                "sharpe":float(r.mean()/(r.std(ddof=0)+1e-12)*np.sqrt(252)),
                "max_drawdown":float(np.min(eq/np.maximum.accumulate(eq)-1))}

    def portfolio(self,weights,returns=None):
        w=pd.Series(weights,index=self.strategy_names,dtype=float)
        if (w<0).any() or not np.isclose(w.sum(),1): raise ValueError("Weights must be non-negative and sum to one")
        R=self.returns if returns is None else pd.DataFrame(returns,columns=self.strategy_names)
        r=R.to_numpy()@w.to_numpy()
        return {"returns":r,"dates":pd.DatetimeIndex(R.index) if not isinstance(R.index,pd.RangeIndex) else self.dates[:len(R)],
                "weights":w.to_dict(),"metrics":self.metrics(r),"equity_curve":np.cumprod(1+r)}

    def apply_rebalance_cost(self,returns,old_weights,new_weights,cost=0.0005):
        turnover=float(np.abs(pd.Series(new_weights)-pd.Series(old_weights)).sum())
        r=np.asarray(returns,float).copy()
        if len(r): r[0]-=cost*turnover
        return r,turnover
