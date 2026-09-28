"""Task 3 reproducible multi-alpha portfolio study with strict rolling OOS discipline."""
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

TRAIN=504; TEST=63; COST=0.0005

def main():
    out=Path("research_output"); out.mkdir(exist_ok=True)
    engine=PortfolioEngine()
    R=engine.returns.copy(); names=engine.strategy_names

    # Static baselines are descriptive only.
    opt=PortfolioOptimizer().fit(R.to_numpy())
    eq=opt.optimize("equal_weight")
    erc=opt.optimize("erc")
    static_rows=[]
    for label,w in [("equal_weight",eq),("erc",erc)]:
        m=engine.metrics(R.to_numpy()@w)
        static_rows.append({"allocator":label,"evaluation":"full_sample_descriptive",**m,**{f"w_{n}":w[i] for i,n in enumerate(names)}})
    pd.DataFrame(static_rows).to_csv(out/"task3_allocator_comparison.csv",index=False)

    # Rolling meta-model: 80/20 train-validation inside each training window,
    # then refit on the complete 504-day window before the 63-day OOS test.
    meta=AlphaMetaModel(null_reps=500,random_state=42)
    allocator=DynamicAllocator(transaction_cost=COST)
    factor_rows=[]; oos_parts=[]; fold_rows=[]; null_totals=[]
    prev=pd.Series(1/len(names),index=names,dtype=float)

    for fold,start in enumerate(range(TRAIN,len(R),TEST),1):
        end=min(start+TEST,len(R)); train=R.iloc[start-TRAIN:start]; test=R.iloc[start:end]
        split=int(len(train)*0.8); tr=train.iloc[:split]; val=train.iloc[split:]

        # Validation performance uses weights learned only from the first 80% of train.
        meta.fit(tr); val_w=allocator.allocate(meta.predict(tr))
        train_r=tr.to_numpy()@val_w.reindex(names).to_numpy()
        val_r=val.to_numpy()@val_w.reindex(names).to_numpy()

        # Final fit uses all information available before this OOS test block.
        meta.fit(train); scores=meta.predict(train); target=allocator.allocate(scores)
        target,turnover=allocator.rebalance(prev,target)
        test_r=test.to_numpy()@target.reindex(names).to_numpy()
        test_r=np.asarray(test_r,float); test_r[0]-=COST*turnover

        # Permutation null: preserve the learned weight magnitudes but randomly
        # assign them to strategy labels before evaluating the same OOS block.
        _,null_fold=meta.null_allocation_returns(train,test)
        null_fold=np.asarray(null_fold,float)
        null_totals.append(null_fold)

        factor=R.iloc[start-TRAIN:start].mean(axis=1).to_frame("strategy_basket")
        fm=FactorModel().fit(train,factor)
        residuals=fm.get_residuals()
        factor_rows.append({"fold":fold,"residual_rms_mean":float(np.sqrt(np.mean(residuals.to_numpy()**2))),
                            "n_train":len(train),"test_start":str(engine.dates[start].date()),
                            "test_end":str(engine.dates[end-1].date())})

        oos_parts.append(test_r)
        fold_rows.append({
            "fold":fold,"train_start":str(engine.dates[start-TRAIN].date()),
            "train_end":str(engine.dates[start-1].date()),
            "validation_start":str(engine.dates[start-TRAIN+split].date()),
            "validation_end":str(engine.dates[start-1].date()),
            "test_start":str(engine.dates[start].date()),
            "test_end":str(engine.dates[end-1].date()),
            "train_sharpe":engine.metrics(train_r)["sharpe"],
            "validation_sharpe":engine.metrics(val_r)["sharpe"],
            "test_sharpe":engine.metrics(test_r)["sharpe"],
            "train_return":engine.metrics(train_r)["total_return"],
            "validation_return":engine.metrics(val_r)["total_return"],
            "test_return":engine.metrics(test_r)["total_return"],
            "turnover":turnover,
            **{f"w_{n}":target[n] for n in names}
        })
        prev=target

    folds=pd.DataFrame(fold_rows); folds.to_csv(out/"task3_dynamic_folds.csv",index=False)
    weights=folds[["fold","test_start","test_end","turnover"]+[f"w_{n}" for n in names]]
    weights.to_csv(out/"task3_dynamic_weights.csv",index=False)

    oos=np.concatenate(oos_parts); oos_metrics=engine.metrics(oos)
    # Compound fold-level permutation outcomes to a full OOS null distribution.
    null_matrix=np.vstack(null_totals)
    null_distribution=np.prod(1+null_matrix,axis=0)-1
    null_summary={"observed_oos_total_return":oos_metrics["total_return"],
                   "null_mean_total_return":float(null_distribution.mean()),
                   "null_std_total_return":float(null_distribution.std(ddof=1)),
                   "null_p95_total_return":float(np.quantile(null_distribution,.95)),
                   "null_exceed_count":int(np.sum(null_distribution>=oos_metrics["total_return"])),
                   "n_permutations":500}
    (out/"task3_null_baseline.json").write_text(json.dumps(null_summary,indent=2))

    factor_df=pd.DataFrame(factor_rows); factor_df.to_csv(out/"task3_factor_model.csv",index=False)

    # OOS equity only; no pre-training backfill.
    eq_curve=np.cumprod(1+oos)
    pd.DataFrame({"date":engine.dates[TRAIN:],"dynamic_meta_oos_equity":eq_curve}).to_csv(out/"task3_dynamic_oos_equity.csv",index=False)

    evaluator=FinalEvaluator()
    meta.folds_=len(folds)
    discipline=evaluator.report(
        train_metrics={"mean_fold_sharpe":float(folds.train_sharpe.mean()),"mean_fold_return":float(folds.train_return.mean())},
        validation_metrics={"mean_fold_sharpe":float(folds.validation_sharpe.mean()),"mean_fold_return":float(folds.validation_return.mean())},
        test_metrics={"mean_fold_sharpe":float(folds.test_sharpe.mean()),"mean_fold_return":float(folds.test_return.mean()),**oos_metrics},
        null=null_summary)
    discipline["meta_model"]=meta.report()
    (out/"task3_model_discipline.json").write_text(json.dumps(discipline,indent=2))

    report=f"""# Task 3: Multi-Alpha Portfolio Construction

## Scope
Task 3 consumes the corrected Task 2 daily return matrix containing {len(names)} strategy streams and {engine.n_obs} synchronized observations ({engine.dates[0].date()} to {engine.dates[-1].date()}).

All Task 3 inputs are already-realized Task 2 strategy returns. No Task 3 step reconstructs a signal from price or volume.

## Static baselines
Equal-weight and covariance ERC are reported as full-sample descriptive baselines. They are not OOS forecasts and are not used to select the dynamic model.

## Learned component and capacity
The AlphaMetaModel uses one statistic per strategy: trailing mean divided by trailing volatility. There are no cross-strategy fitted coefficients, hidden layers, or high-dimensional features. This is deliberately low capacity relative to the 504-observation training window.

## Validation and OOS protocol
There are {len(folds)} rolling folds. Each fold uses 504 prior observations for training and 63 subsequent observations for testing. Inside each 504-observation training window, the first 80% is used to assess an internal validation block; the final OOS test block is reached only after refitting on the full 504-observation training window.

Transaction cost is 0.05% per unit portfolio turnover at each rebalance. Strategy-level Task 2 costs are already embedded in the supplied return streams.

## Model discipline results
Mean fold train return: {folds.train_return.mean():.2%}; validation return: {folds.validation_return.mean():.2%}; OOS test return: {folds.test_return.mean():.2%}.
Mean fold train Sharpe: {folds.train_sharpe.mean():.3f}; validation Sharpe: {folds.validation_sharpe.mean():.3f}; OOS test Sharpe: {folds.test_sharpe.mean():.3f}.

These gaps are reported for overfitting assessment; no full-sample performance is substituted for OOS evidence.

## Null baseline
A 500-repetition permutation null randomly reassigns the learned weight magnitudes to strategy labels within each OOS fold. The observed OOS cumulative return is {oos_metrics["total_return"]:.2%}; the permutation-null mean is {null_summary["null_mean_total_return"]:.2%}, with standard deviation {null_summary["null_std_total_return"]:.2%}. {null_summary["null_exceed_count"]} of 500 null runs reached or exceeded the observed OOS cumulative return.

The null is a diagnostic, not a significance claim.

## OOS portfolio result
Dynamic meta-model OOS cumulative return: {oos_metrics["total_return"]:.2%}
CAGR: {oos_metrics["cagr"]:.2%}
Annual volatility: {oos_metrics["annual_vol"]:.2%}
Sharpe: {oos_metrics["sharpe"]:.3f}
Maximum drawdown: {oos_metrics["max_drawdown"]:.2%}

## Factor separation
A simple OLS factor model is fit fold-by-fold using the equal-weight strategy basket as an explicitly endogenous diagnostic factor. Residual RMS is recorded in task3_factor_model.csv. This is not presented as an external market-factor attribution.

## Files
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
