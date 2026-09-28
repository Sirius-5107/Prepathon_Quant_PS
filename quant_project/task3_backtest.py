"""Task 3 multi-alpha portfolio construction with frozen Task 2 selection."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from portfolio_engine import PortfolioEngine
from portfolio_optimizer import PortfolioOptimizer
from meta_model import AlphaMetaModel
from dynamic_allocator import DynamicAllocator
from factor_model import FactorModel
from final_evaluation import FinalEvaluator

TRAIN,TEST,COST=504,63,0.0005
SELECTED_STRATEGIES=["PB07_TailReversal_10D","PB07_BB03_BB04_Conditional","BB03_Reversal_10D"]

def residual_r2(y,X):
    y=np.asarray(y,float); X=np.asarray(X,float)
    if X.ndim==1: X=X.reshape(-1,1)
    X=np.column_stack([np.ones(len(X)),X])
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b
    d=np.sum((y-y.mean())**2)
    return 0.0 if d<=1e-15 else float(1-np.sum(e**2)/d)

def main():
    out=Path("research_output")
    results=json.loads((out/"TASK2_CORRECTED_RESULTS.json").read_text())
    evidence={x["strategy"]:x for x in results}
    if any(s not in evidence for s in SELECTED_STRATEGIES):
        raise AssertionError("Selected strategy missing from corrected Task 2 results")

    engine=PortfolioEngine()
    R=engine.returns[SELECTED_STRATEGIES].copy()
    names=list(R.columns)

    rows=[]; prior=[]
    for s in names:
        r2=residual_r2(R[s],R[prior]) if prior else 0.0
        rows.append({"strategy":s,"wfo_mean_return_pct":evidence[s]["wfo_mean_return_%"],
            "wfo_mean_sharpe":evidence[s]["wfo_mean_sharpe"],"wfo_positive_folds":evidence[s]["wfo_positive_folds"],
            "incremental_r2_on_selected_prior":r2,"residual_variance_share_pct":100*(1-r2)})
        prior.append(s)
    pd.DataFrame(rows).to_csv(out/"task3_strategy_selection.csv",index=False)

    opt=PortfolioOptimizer().fit(R.to_numpy())
    ew=opt.optimize("equal_weight"); erc=opt.optimize("erc"); ms=opt.optimize("max_sharpe")
    best_name=max(names,key=lambda s:evidence[s]["wfo_mean_return_%"])
    best=np.eye(len(names))[names.index(best_name)]
    static=[]
    for label,w,ref in [("best_individual",best,best_name),("equal_weight",ew,""),
                        ("risk_based_erc",erc,""),("optimized_max_sharpe",ms,"")]:
        static.append({"allocator":label,"evaluation":"full_sample_descriptive",
            "selection_basis":"corrected Task 2 WFO" if label=="best_individual" else "descriptive full-sample",
            "reference_strategy":ref,**engine.metrics(R.to_numpy()@w),
            **{f"w_{n}":float(w[i]) for i,n in enumerate(names)}})

    meta=AlphaMetaModel(null_reps=500,random_state=42)
    allocator=DynamicAllocator(transaction_cost=COST)
    prev=pd.Series(1/len(names),index=names,dtype=float)
    folds=[]; oos_parts=[]; nulls=[]; factor_rows=[]

    for fold,start in enumerate(range(TRAIN,len(R),TEST),1):
        end=min(start+TEST,len(R)); train=R.iloc[start-TRAIN:start]; test=R.iloc[start:end]
        split=int(len(train)*.8); tr=train.iloc[:split]; val=train.iloc[split:]
        meta.fit(tr); vw=allocator.allocate(meta.predict(tr))
        train_r=tr.to_numpy()@vw.reindex(names).to_numpy()
        val_r=val.to_numpy()@vw.reindex(names).to_numpy()
        meta.fit(train); target=allocator.allocate(meta.predict(train))
        target,turnover=allocator.rebalance(prev,target)
        test_r=np.asarray(test.to_numpy()@target.reindex(names).to_numpy(),float)
        test_r[0]-=COST*turnover
        _,null=meta.null_allocation_returns(train,test); nulls.append(null)
        fm=FactorModel().fit(train,R.iloc[start-TRAIN:start].mean(axis=1).to_frame("strategy_basket"))
        resid=fm.get_residuals()
        factor_rows.append({"fold":fold,"residual_rms_mean":float(np.sqrt(np.mean(resid.to_numpy()**2)))})
        folds.append({"fold":fold,"train_start":str(engine.dates[start-TRAIN].date()),
            "train_end":str(engine.dates[start-1].date()),"validation_start":str(engine.dates[start-TRAIN+split].date()),
            "validation_end":str(engine.dates[start-1].date()),"test_start":str(engine.dates[start].date()),
            "test_end":str(engine.dates[end-1].date()),"train_return":engine.metrics(train_r)["total_return"],
            "validation_return":engine.metrics(val_r)["total_return"],"test_return":engine.metrics(test_r)["total_return"],
            "train_sharpe":engine.metrics(train_r)["sharpe"],"validation_sharpe":engine.metrics(val_r)["sharpe"],
            "test_sharpe":engine.metrics(test_r)["sharpe"],"turnover":turnover,
            **{f"w_{n}":float(target[n]) for n in names}})
        oos_parts.append(test_r); prev=target

    folds=pd.DataFrame(folds)
    folds.to_csv(out/"task3_dynamic_folds.csv",index=False)
    folds[["fold","test_start","test_end","turnover"]+[f"w_{n}" for n in names]].to_csv(out/"task3_dynamic_weights.csv",index=False)
    oos=np.concatenate(oos_parts); om=engine.metrics(oos)
    nd=np.prod(1+np.vstack(nulls),axis=0)-1
    null_summary={"observed_oos_total_return":om["total_return"],"null_mean_total_return":float(nd.mean()),
        "null_std_total_return":float(nd.std(ddof=1)),"null_p95_total_return":float(np.quantile(nd,.95)),
        "null_exceed_count":int(np.sum(nd>=om["total_return"])),"n_permutations":500}
    (out/"task3_null_baseline.json").write_text(json.dumps(null_summary,indent=2))
    pd.DataFrame(factor_rows).to_csv(out/"task3_factor_model.csv",index=False)
    pd.DataFrame({"date":engine.dates[TRAIN:],"dynamic_meta_oos_equity":np.cumprod(1+oos)}).to_csv(out/"task3_dynamic_oos_equity.csv",index=False)

    dyn={"allocator":"proposed_dynamic_meta_model","evaluation":"stitched_OOS","selection_basis":"frozen corrected Task 2 selection",
         "reference_strategy":"","total_return":om["total_return"],"cagr":om["cagr"],"annual_vol":om["annual_vol"],
         "sharpe":om["sharpe"],"max_drawdown":om["max_drawdown"]}
    dyn.update({f"w_{n}_mean":float(folds[f"w_{n}"].mean()) for n in names})
    pd.DataFrame(static+[dyn]).to_csv(out/"task3_allocator_comparison.csv",index=False)

    meta.folds_=len(folds)
    discipline=FinalEvaluator().report(
        train_metrics={"mean_fold_return":float(folds.train_return.mean()),"mean_fold_sharpe":float(folds.train_sharpe.mean())},
        validation_metrics={"mean_fold_return":float(folds.validation_return.mean()),"mean_fold_sharpe":float(folds.validation_sharpe.mean())},
        test_metrics={"mean_fold_return":float(folds.test_return.mean()),"mean_fold_sharpe":float(folds.test_sharpe.mean()),**om},
        null=null_summary)
    discipline["meta_model"]=meta.report(); discipline["selected_strategies"]=names
    discipline["selection_rule"]="Frozen corrected Task 2 WFO evidence plus non-redundant return-space contribution"
    (out/"task3_model_discipline.json").write_text(json.dumps(discipline,indent=2))

    report=f"""# Task 3: Multi-Alpha Portfolio Construction

## Selected strategy set
Task 3 uses three streams selected before portfolio construction:
- PB07 Tail Reversal: {evidence["PB07_TailReversal_10D"]["wfo_mean_return_%"]:.2f}% mean WFO return, {evidence["PB07_TailReversal_10D"]["wfo_positive_folds"]}/7 positive folds.
- PB07/BB03/BB04 Conditional: {evidence["PB07_BB03_BB04_Conditional"]["wfo_mean_return_%"]:.2f}% mean WFO return, {evidence["PB07_BB03_BB04_Conditional"]["wfo_positive_folds"]}/7 positive folds.
- BB03 Reversal: {evidence["BB03_Reversal_10D"]["wfo_mean_return_%"]:.2f}% mean WFO return, {evidence["BB03_Reversal_10D"]["wfo_positive_folds"]}/7 positive folds.

BB01, Mean-Reversion Composite, and BB04 are excluded because their corrected mean WFO returns are negative. BB03_RegimeFiltered is excluded as redundant with BB03. Other lower-return candidates are not carried into Task 3.

Return-space residual diagnostics are written to task3_strategy_selection.csv. They are diversification diagnostics, not proof of independent alpha. PB07's 3/7 positive-fold result is retained explicitly rather than hidden by portfolio aggregation.

## Required baselines
The comparison table contains best individual, equal-weight, risk-based ERC, long-only maximum-Sharpe optimization, and proposed dynamic allocation. The first four are full-sample descriptive baselines. The proposed dynamic result is stitched OOS only. The maximum-Sharpe baseline is explicitly not treated as OOS evidence.

## ERC
ERC minimizes dispersion in log component risk contributions w_i*(Sigma w)_i under long-only weights summing to one. This replaces the prior implementation that collapsed to equal weights.

## Model discipline
The meta-model uses one trailing mean/volatility score per selected strategy. Each fold uses 504 training observations, an 80/20 internal train/validation split, refits on all 504 observations, and freezes weights for the following 63-observation OOS block. Transaction cost is 0.05% per unit turnover and is charged on the first day of each OOS rebalance block.

Mean train return: {folds.train_return.mean():.2%}
Mean validation return: {folds.validation_return.mean():.2%}
Mean OOS test return: {folds.test_return.mean():.2%}

Mean train Sharpe: {folds.train_sharpe.mean():.3f}
Mean validation Sharpe: {folds.validation_sharpe.mean():.3f}
Mean OOS test Sharpe: {folds.test_sharpe.mean():.3f}

These gaps are the primary overfitting diagnostic; the stitched OOS Sharpe is not presented in isolation.

## Permutation null
Observed stitched OOS return: {om["total_return"]:.2%}
Null mean: {null_summary["null_mean_total_return"]:.2%}
Null standard deviation: {null_summary["null_std_total_return"]:.2%}
Null runs reaching observed: {null_summary["null_exceed_count"]}/{null_summary["n_permutations"]}

The null is diagnostic, not a significance claim.

## Dynamic OOS result
Cumulative return: {om["total_return"]:.2%}
CAGR: {om["cagr"]:.2%}
Annual volatility: {om["annual_vol"]:.2%}
Sharpe: {om["sharpe"]:.3f}
Maximum drawdown: {om["max_drawdown"]:.2%}

These values are regenerated from the three-strategy selection and supersede prior nine-strategy Task 3 numbers.

## Factor diagnostic
The factor model uses the equal-weight basket of the selected strategies as an explicitly endogenous diagnostic factor. It is not external market-factor attribution.

## Outputs
- task3_strategy_selection.csv
- task3_allocator_comparison.csv
- task3_dynamic_folds.csv
- task3_dynamic_weights.csv
- task3_dynamic_oos_equity.csv
- task3_null_baseline.json
- task3_model_discipline.json
- task3_factor_model.csv
- TASK3_PORTFOLIO_REPORT.md
"""
    (out/"TASK3_PORTFOLIO_REPORT.md").write_text(report)

if __name__=="__main__":
    main()
