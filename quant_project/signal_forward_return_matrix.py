from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ROOT / ".." / "signals_cleaned.csv"
PRICE = ROOT / ".." / "price_cleaned.csv"
OUT = ROOT / ".." / "research_output"
OUT.mkdir(exist_ok=True)
H = [1, 3, 5, 10, 20]
SIGS = ['PB01','PB02','PB03','PB04','PB05','PB06','PB07','PB08','BB01','BB02','BB03','BB04','BB05','BB06','BB07','VB01','VB02','VB03','VB04','VB05']

s = pd.read_csv(SIGNALS, parse_dates=['date']).sort_values('date').drop_duplicates('date')
p = pd.read_csv(PRICE, parse_dates=['date']).sort_values('date').drop_duplicates('date')
df = s.merge(p[['date','open','close']], on='date', how='inner').sort_values('date').reset_index(drop=True)

# Signal at t is usable for the decision executed at t+1 open.
# h=1 means next-session open -> next-session close.
for h in H:
    df[f'fwd_{h}d'] = df['close'].shift(-h) / df['open'].shift(-1) - 1

rows=[]
for sig in SIGS:
    binary = set(df[sig].dropna().unique()).issubset({0,1})
    for h in H:
        x=df[[sig,f'fwd_{h}d']].dropna()
        a=x.loc[x[sig]==1,f'fwd_{h}d'] if binary else pd.Series(dtype=float)
        b=x.loc[x[sig]==0,f'fwd_{h}d'] if binary else pd.Series(dtype=float)
        spread=a.mean()-b.mean() if binary else np.nan
        t=stats.ttest_ind(a,b,equal_var=False).statistic if binary and len(a)>1 and len(b)>1 else np.nan
        pearson=stats.pearsonr(x[sig],x[f'fwd_{h}d']).statistic if len(x)>2 and x[sig].nunique()>1 else np.nan
        spearman=stats.spearmanr(x[sig],x[f'fwd_{h}d']).statistic if len(x)>2 and x[sig].nunique()>1 else np.nan
        rows.append({'signal':sig,'type':'binary' if binary else 'continuous','horizon':h,'n':len(x),'n1':len(a),'n0':len(b),'mean_1':a.mean() if binary else np.nan,'mean_0':b.mean() if binary else np.nan,'spread_1_minus_0':spread,'tstat_spread':t,'pearson_ic':pearson,'spearman_ic':spearman})

res=pd.DataFrame(rows)
res.to_csv(OUT/'signal_forward_return_summary.csv',index=False)
res.pivot(index='signal',columns='horizon',values='spearman_ic').to_csv(OUT/'signal_forward_return_ic_matrix.csv')
res[res.type=='binary'].pivot(index='signal',columns='horizon',values='spread_1_minus_0').to_csv(OUT/'signal_forward_return_binary_spread_matrix.csv')

# Continuous-signal quintiles: useful for detecting monotonic/nonlinear effects.
qrows=[]
for sig in SIGS:
    if set(df[sig].dropna().unique()).issubset({0,1}): continue
    for h in H:
        z=df[[sig,f'fwd_{h}d']].dropna().copy()
        if len(z)<20 or z[sig].nunique()<5: continue
        z['q']=pd.qcut(z[sig],5,labels=False,duplicates='drop')+1
        for q,g in z.groupby('q'):
            qrows.append({'signal':sig,'horizon':h,'quintile':int(q),'n':len(g),'mean_forward_return':g[f'fwd_{h}d'].mean()})
pd.DataFrame(qrows).to_csv(OUT/'signal_forward_return_quintiles.csv',index=False)

df.to_csv(OUT/'signal_forward_return_dataset.csv',index=False)

print('\nSIGNAL x FORWARD RETURN MATRIX')
print(f'Rows={len(df)}, dates={df.date.min().date()} -> {df.date.max().date()}')
print('\nTop by mean absolute Spearman IC:')
ic=res.pivot(index='signal',columns='horizon',values='spearman_ic')
ic['mean_abs_ic']=ic.abs().mean(axis=1)
print(ic.sort_values('mean_abs_ic',ascending=False).to_string(float_format=lambda x:f'{x:.4f}'))
print('\nTop binary signals by mean absolute spread:')
sp=res[res.type=='binary'].pivot(index='signal',columns='horizon',values='spread_1_minus_0')
sp['mean_abs_spread']=sp.abs().mean(axis=1)
print(sp.sort_values('mean_abs_spread',ascending=False).to_string(float_format=lambda x:f'{x:.4%}'))
