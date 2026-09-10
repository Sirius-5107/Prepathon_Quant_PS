from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from statsmodels.api import OLS, add_constant

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
DATA_CANDIDATES = [ROOT, ROOT.parent]
for base in DATA_CANDIDATES:
    if (base / "signals_cleaned.csv").exists() and (base / "price_cleaned.csv").exists():
        DATA = base
        break
else:
    raise FileNotFoundError("Could not find signals_cleaned.csv and price_cleaned.csv")

OUT = DATA / "research_output"
OUT.mkdir(exist_ok=True)
H = [1, 3, 5, 10, 20]
SIGS = ['PB01','PB02','PB03','PB04','PB05','PB06','PB07','PB08','BB01','BB02','BB03','BB04','BB05','BB06','BB07','VB01','VB02','VB03','VB04','VB05']

s = pd.read_csv(DATA / "signals_cleaned.csv", parse_dates=['date']).sort_values('date').drop_duplicates('date')
p = pd.read_csv(DATA / "price_cleaned.csv", parse_dates=['date']).sort_values('date').drop_duplicates('date')
df = s.merge(p[['date','open','close']], on='date', how='inner').sort_values('date').reset_index(drop=True)

# Official timing: signal at t -> execution at t+1 open.
for h in H:
    df[f'fwd_{h}d'] = df['close'].shift(-h) / df['open'].shift(-1) - 1

df['year'] = df['date'].dt.year

rows = []
for sig in SIGS:
    binary = set(df[sig].dropna().unique()).issubset({0, 1})
    for h in H:
        ycol = f'fwd_{h}d'
        for year, g in df.groupby('year'):
            x = g[[sig, ycol]].dropna().copy()
            if len(x) < 30 or x[sig].nunique() < 2:
                continue
            y = x[ycol].to_numpy(float)
            xx = x[sig].to_numpy(float)
            model = OLS(y, add_constant(xx)).fit(cov_type='HAC', cov_kwds={'maxlags': max(1, h - 1)})
            row = {
                'signal': sig,
                'type': 'binary' if binary else 'continuous',
                'year': int(year),
                'horizon': h,
                'n': len(x),
                'coef': float(model.params[1]),
                'hac_tstat': float(model.tvalues[1]),
                'hac_pvalue': float(model.pvalues[1]),
                'spearman_ic': float(pd.Series(xx).corr(pd.Series(y), method='spearman')),
            }
            if binary:
                row['n1'] = int((xx == 1).sum())
                row['n0'] = int((xx == 0).sum())
                row['mean_1'] = float(y[xx == 1].mean())
                row['mean_0'] = float(y[xx == 0].mean())
                row['spread_1_minus_0'] = row['mean_1'] - row['mean_0']
            else:
                row['n1'] = row['n0'] = np.nan
                row['mean_1'] = row['mean_0'] = row['spread_1_minus_0'] = np.nan
            rows.append(row)

res = pd.DataFrame(rows)
res.to_csv(OUT / 'signal_temporal_stability.csv', index=False)

# Summary across years. A robust candidate should have repeated sign, not one giant outlier year.
summaries = []
for (sig, h), g in res.groupby(['signal','horizon']):
    coef = g['coef'].to_numpy()
    t = g['hac_tstat'].to_numpy()
    summaries.append({
        'signal': sig,
        'horizon': h,
        'years_present': len(g),
        'positive_years': int((coef > 0).sum()),
        'negative_years': int((coef < 0).sum()),
        'sign_consistency': float(max((coef > 0).mean(), (coef < 0).mean())),
        'mean_yearly_coef': float(coef.mean()),
        'median_yearly_coef': float(np.median(coef)),
        'mean_abs_yearly_t': float(np.mean(np.abs(t))),
        'max_abs_yearly_t': float(np.max(np.abs(t))),
    })
sumdf = pd.DataFrame(summaries)
sumdf['abs_median_coef'] = sumdf['median_yearly_coef'].abs()
sumdf = sumdf.sort_values(['sign_consistency','mean_abs_yearly_t','abs_median_coef'], ascending=[False,False,False])
sumdf.to_csv(OUT / 'signal_temporal_stability_summary.csv', index=False)

print('=' * 72)
print('SIGNAL TEMPORAL STABILITY AUDIT')
print('=' * 72)
print(f"Merged dates: {len(df):,} | {df.date.min().date()} -> {df.date.max().date()}")
print(f"Years: {', '.join(map(str, sorted(df.year.unique())))}")

# Focus first on the previously strongest candidates.
for sig, h in [('VB03', 5), ('BB03', 10), ('BB04', 5), ('PB07', 10), ('VB04', 3)]:
    z = res[(res.signal == sig) & (res.horizon == h)].copy()
    if z.empty:
        continue
    print(f"\n{sig} @ {h}d")
    cols = ['year','n','coef','hac_tstat','hac_pvalue','spearman_ic']
    if z['type'].iloc[0] == 'binary':
        cols += ['n1','n0','spread_1_minus_0']
    print(z[cols].to_string(index=False, formatters={
        'coef': lambda x: f'{x:.5f}',
        'hac_tstat': lambda x: f'{x:.2f}',
        'hac_pvalue': lambda x: f'{x:.4f}',
        'spearman_ic': lambda x: f'{x:.4f}',
        'spread_1_minus_0': lambda x: f'{x:.3%}',
    }))

print('\nTop signal x horizon combinations by sign consistency, then mean |yearly HAC t|:')
print(sumdf.head(25).to_string(index=False, formatters={
    'sign_consistency': lambda x: f'{x:.0%}',
    'mean_yearly_coef': lambda x: f'{x:.5f}',
    'median_yearly_coef': lambda x: f'{x:.5f}',
    'mean_abs_yearly_t': lambda x: f'{x:.2f}',
    'max_abs_yearly_t': lambda x: f'{x:.2f}',
}))

print('\nInterpretation rule:')
print('- Stronger evidence = same economic sign across most/all years AND no single year dominating the pooled effect.')
print('- A candidate with one strong year and sign reversals elsewhere is a regime-dependent hypothesis, not yet robust alpha.')
print('- Yearly p-values are descriptive because each year has a small sample; do not use them as the main discovery test.')
