"""Final Task 3 evaluation and model-discipline reporting."""
import numpy as np
import pandas as pd

class FinalEvaluator:
    @staticmethod
    def _metrics(r):
        r=np.asarray(r,float); eq=np.cumprod(1+r)
        return {"total_return":float(eq[-1]-1),"cagr":float(eq[-1]**(252/len(r))-1),
                "annual_vol":float(r.std()*np.sqrt(252)),
                "sharpe":float(r.mean()/(r.std()+1e-12)*np.sqrt(252)),
                "max_drawdown":float(np.min(eq/np.maximum.accumulate(eq)-1))}
    def evaluate(self,strategy_set): return {k:self._metrics(v) for k,v in pd.DataFrame(strategy_set).items()}
    def compare(self,methods): return pd.DataFrame(methods).T
    def robustness_test(self,results): return {"n_methods":len(results),"finite":all(np.isfinite(list(v.values())).all() for v in results.values())}
    def report(self,train_metrics=None,validation_metrics=None,test_metrics=None,null=None):
        return {"train":train_metrics or {},"validation":validation_metrics or {},"test":test_metrics or {},
                "null_baseline":null or {},"overfit_risk":"Judge from rolling train-to-validation/OOS gaps; do not select on full-sample OOS outcomes."}
