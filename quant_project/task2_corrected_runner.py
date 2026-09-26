"""
Corrected Task 2 runner: supplied signals are the only predictive inputs.
"""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from strategies.alpha_01 import Alpha01
from strategies.alpha_02 import Alpha02
from strategies.alpha_03 import Alpha03
from strategies.alpha_04 import Alpha04
from strategies.alpha_05 import Alpha05
SIGNALS=[f"PB{i:02d}" for i in range(1,9)]+[f"BB{i:02d}" for i in range(1,8)]+[f"VB{i:02d}" for i in range(1,6)]

def load_data():
    s=pd.read_csv(ROOT/"signals_cleaned.csv",parse_dates=["date"])
    p=pd.read_csv(ROOT/"price_cleaned.csv",parse_dates=["date"])
    s=s[["date"]+SIGNALS].sort_values("date").drop_duplicates("date")
    p=p.sort_values("date").drop_duplicates("date")
    return s,p,s.merge(p,on="date",how="inner").sort_values("date").reset_index(drop=True)

def forward_target(data,h=10):
    y=np.full(len(data),np.nan)
    for i in range(len(data)-h): y[i]=data.iloc[i+h]["close"]/data.iloc[i+1]["open"]-1.0
    return pd.Series(y,index=data.index)

def backtest_events(data,sig,start=0,end=None,cost=.0005):
    end=len(data) if end is None else end
    cash=1.; pos=0; events=0; pairs=0; curve=[]
    for i in range(start,end):
        v=int(sig.iloc[i]); px=float(data.iloc[i]["open"])
        if v==1 and pos==0: cash-=px*(1+cost); pos=1; events+=1
        elif v==-1 and pos==1: cash+=px*(1-cost); pos=0; events+=1; pairs+=1
        curve.append(cash+pos*float(data.iloc[i]["close"]))
    eq=pd.Series(curve,dtype=float); ret=eq.pct_change().dropna()
    vol=ret.std()*np.sqrt(252) if len(ret)>1 else 0.
    sharpe=(ret.mean()*252)/(ret.std()*np.sqrt(252)+1e-12) if len(ret)>1 else 0.
    dd=(eq/eq.cummax()-1).min() if len(eq) else 0.
    return {"total_return_%":float((eq.iloc[-1]-1)*100) if len(eq) else 0.,"sharpe_ratio":float(sharpe),
            "volatility_%":float(vol*100),"max_drawdown_%":float(dd*100),"trades":pairs,"raw_events":events}

def fit_strategy(st,signals,data,start,end):
    tr_sig=signals.iloc[start:end].copy()
    tr_data=data.iloc[start:end].copy()
    target=forward_target(tr_data,10)
    st.fit(st.generate_features(tr_sig),target)
    return st

def wfo(cls,signals,data,train=504,test=63):
    folds=[]
    for k,start in enumerate(range(0,len(data)-train-test+1,test),1):
        train_end=start+train; test_end=train_end+test
        st=fit_strategy(cls(),signals,data,start,train_end)
        hist=signals.iloc[:test_end].copy()
        sig=st.generate_signal(st.generate_features(hist))
        m=backtest_events(data,sig,train_end,test_end)
        folds.append({"fold":k,"train_start":str(signals.iloc[start].date.date()),
                      "train_end":str(signals.iloc[train_end-1].date.date()),
                      "test_start":str(signals.iloc[train_end].date.date()),
                      "test_end":str(signals.iloc[test_end-1].date.date()),**m})
    return folds

def main():
    signals,price,data=load_data()
    classes=[Alpha01,Alpha02,Alpha03,Alpha04,Alpha05]
    results=[]; streams={}
    for cls in classes:
        st=fit_strategy(cls(),signals,data,0,min(504,len(data)))
        sig=st.generate_signal(st.generate_features(signals))
        folds=wfo(cls,signals,data)
        full=backtest_events(data,sig)
        results.append({"strategy":st.name,"metadata":st.get_metadata(),"full_sample":full,
                        "wfo_folds":folds,
                        "wfo_mean_return_%":float(np.mean([f["total_return_%"] for f in folds])),
                        "wfo_mean_sharpe":float(np.mean([f["sharpe_ratio"] for f in folds])),
                        "wfo_positive_folds":int(sum(f["total_return_%"]>0 for f in folds))})
        streams[st.name]=sig.to_numpy(dtype=float)
    corr=pd.DataFrame(streams).corr()
    out=ROOT/"research_output"; out.mkdir(exist_ok=True)
    (out/"TASK2_CORRECTED_RESULTS.json").write_text(json.dumps(results,indent=2))
    corr.to_csv(out/"TASK2_RETURN_SPACE_CORRELATION.csv")
    print(json.dumps(results,indent=2)); print(corr.round(4))
if __name__=="__main__": main()
