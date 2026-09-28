"""Generic strictly-OOS dynamic allocator for Task 3."""
import numpy as np
import pandas as pd

class DynamicAllocator:
    def __init__(self,transaction_cost=0.0005):
        self.transaction_cost=float(transaction_cost); self.history_=[]

    def allocate(self,strategy_scores,constraints=None):
        s=pd.Series(strategy_scores,dtype=float).clip(lower=0)
        if s.sum()<=0: return pd.Series(1/len(s),index=s.index)
        return s/s.sum()

    def rebalance(self,current_weights,target_weights):
        c=pd.Series(current_weights,dtype=float); t=pd.Series(target_weights,dtype=float).reindex(c.index).fillna(0)
        turnover=float(np.abs(t-c).sum())
        return t,turnover

    def get_allocation_history(self): return pd.DataFrame(self.history_)

    def report(self):
        return {"training_window":504,"test_window":63,"transaction_cost_per_turnover":self.transaction_cost,
                "lookahead":"weights frozen before each OOS test window"}

    def walk_forward(self,returns,model,train_days=504,test_days=63):
        R=pd.DataFrame(returns).astype(float)
        rows=[]; oos=[]; current=pd.Series(1/len(R.columns),index=R.columns)
        for start in range(train_days,len(R),test_days):
            end=min(start+test_days,len(R)); train=R.iloc[start-train_days:start]; test=R.iloc[start:end]
            model.fit(train); scores=model.predict(train); target=self.allocate(scores)
            target,turnover=self.rebalance(current,target)
            test_r=test.to_numpy()@target.to_numpy()
            test_r=np.asarray(test_r,float); test_r[0]-=self.transaction_cost*turnover
            for j,(idx,val) in enumerate(zip(test.index,test_r)):
                rows.append({"date":idx,"window":len(self.history_)+1,"turnover":turnover,"return":val,**{f"w_{c}":target[c] for c in R.columns}})
            self.history_.append({"window":len(self.history_)+1,"train_start":R.index[start-train_days],
                                  "train_end":R.index[start-1],"test_start":R.index[start],"test_end":R.index[end-1],"turnover":turnover})
            oos.extend(test_r.tolist()); current=target
        return pd.DataFrame(rows),np.asarray(oos)
