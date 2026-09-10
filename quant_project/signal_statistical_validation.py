from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.api import OLS, add_constant
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
# Match the existing research script's data layout, but also support files at repo root.
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

print("=" * 72)
print("SIGNAL DATA AUDIT + STATISTICAL VALIDATION")
print("=" * 72)
print(f"Signals rows: {len(s):,} | unique dates: {s.date.nunique():,} | {s.date.min().date()} -> {s.date.max().date()}")
print(f"Price rows:   {len(p):,} | unique dates: {p.date.nunique():,} | {p.date.min().date()} -> {p.date.max().date()}")

signal_dates = set(s.date)
price_dates = set(p.date)
overlap = signal_dates & price_dates
print(f"Date overlap: {len(overlap):,}")
print(f"Signal-only dates: {len(signal_dates - price_dates):,}")
print(f"Price-only dates:  {len(price_dates - signal_dates):,}")

missing = s[SIGS].isna().sum().sort_values(ascending=False)
print("\nMissing signal values:")
print(missing[missing > 0].to_string() if (missing > 0).any() else "None")

# Merge only the columns needed for target construction.
df = s.merge(p[['date','open','close']], on='date', how='inner').sort_values('date').reset_index(drop=True)
print(f"\nMerged rows before signal/target filtering: {len(df):,}")
print(f"Rows with complete 20-signal vector: {df[SIGS].notna().all(axis=1).sum():,}")
print(f"Rows lost to any missing signal: {df[SIGS].isna().any(axis=1).sum():,}")
print(f"Rows with missing open/close: {df[['open','close']].isna().any(axis=1).sum():,}")

# Official timing: signal at t -> execution at t+1 open.
for h in H:
    df[f'fwd_{h}d'] = df['close'].shift(-h) / df['open'].shift(-1) - 1

# Exact usable-N audit by horizon and signal.
aud_rows = []
for sig in SIGS:
    binary = set(df[sig].dropna().unique()).issubset({0, 1})
    for h in H:
        x = df[[sig, f'fwd_{h}d']].dropna()
        aud_rows.append({
            'signal': sig,
            'horizon': h,
            'usable_n': len(x),
            'missing_signal': int(df[sig].isna().sum()),
            'missing_target': int(df[f'fwd_{h}d'].isna().sum()),
            'signal_type': 'binary' if binary else 'continuous'
        })
aud = pd.DataFrame(aud_rows)
aud.to_csv(OUT / 'signal_statistical_audit.csv', index=False)
print("\nUsable N by horizon (range across signals):")
print(aud.groupby('horizon')['usable_n'].agg(['min','max']).to_string())

# Statistical validation.
# For binary signals, regress forward return on the 0/1 signal and use HAC SEs.
# HAC is important because h-day forward returns overlap heavily for h>1.
# For continuous signals, use the same HAC regression plus Spearman/Pearson diagnostics.
rows = []
for sig in SIGS:
    binary = set(df[sig].dropna().unique()).issubset({0, 1})
    for h in H:
        ycol = f'fwd_{h}d'
        x = df[[sig, ycol]].dropna().copy()
        if len(x) < 30 or x[sig].nunique() < 2:
            continue

        y = x[ycol].to_numpy(float)
        xx = x[sig].to_numpy(float)
        model = OLS(y, add_constant(xx)).fit(cov_type='HAC', cov_kwds={'maxlags': max(1, h - 1)})
        coef = float(model.params[1])
        hac_t = float(model.tvalues[1])
        hac_p = float(model.pvalues[1])

        pearson_r, pearson_p = stats.pearsonr(xx, y)
        spearman_r, spearman_p = stats.spearmanr(xx, y)

        if binary:
            m1 = y[xx == 1].mean()
            m0 = y[xx == 0].mean()
            spread = m1 - m0
            n1 = int((xx == 1).sum())
            n0 = int((xx == 0).sum())
        else:
            m1 = m0 = spread = np.nan
            n1 = n0 = np.nan

        rows.append({
            'signal': sig,
            'type': 'binary' if binary else 'continuous',
            'horizon': h,
            'n': len(x),
            'n1': n1,
            'n0': n0,
            'mean_1': m1,
            'mean_0': m0,
            'spread_1_minus_0': spread,
            'hac_coef': coef,
            'hac_tstat': hac_t,
            'hac_pvalue': hac_p,
            'pearson_ic': pearson_r,
            'pearson_pvalue_iid': pearson_p,
            'spearman_ic': spearman_r,
            'spearman_pvalue_iid': spearman_p,
        })

res = pd.DataFrame(rows)

# Benjamini-Hochberg FDR across all 20 x 5 = 100 signal/horizon hypotheses.
res['qvalue_bh_10pct'] = np.nan
res['qvalue_bh_05pct'] = np.nan
mask = res['hac_pvalue'].notna()
rej10, q10, _, _ = multipletests(res.loc[mask, 'hac_pvalue'], alpha=0.10, method='fdr_bh')
rej05, q05, _, _ = multipletests(res.loc[mask, 'hac_pvalue'], alpha=0.05, method='fdr_bh')
res.loc[mask, 'qvalue_bh_10pct'] = q10
res.loc[mask, 'qvalue_bh_05pct'] = q05
res['fdr_significant_10pct'] = False
res['fdr_significant_05pct'] = False
res.loc[mask, 'fdr_significant_10pct'] = rej10
res.loc[mask, 'fdr_significant_05pct'] = rej05

res['abs_hac_t'] = res['hac_tstat'].abs()
res['abs_spearman_ic'] = res['spearman_ic'].abs()
res = res.sort_values(['abs_hac_t'], ascending=False)
res.to_csv(OUT / 'signal_statistical_validation.csv', index=False)

print("\nTop 20 signal x horizon results by |HAC t-stat|:")
cols = ['signal','type','horizon','n','hac_coef','hac_tstat','hac_pvalue','qvalue_bh_10pct','fdr_significant_10pct','spearman_ic']
show = res[cols].head(20).copy()
print(show.to_string(index=False, formatters={
    'hac_coef': lambda x: f'{x:.5f}',
    'hac_tstat': lambda x: f'{x:.2f}',
    'hac_pvalue': lambda x: f'{x:.4g}',
    'qvalue_bh_10pct': lambda x: f'{x:.4g}',
    'spearman_ic': lambda x: f'{x:.4f}',
}))

sig10 = res[res.fdr_significant_10pct]
sig05 = res[res.fdr_significant_05pct]
print(f"\nFDR significant at q < 10%: {len(sig10)} / {len(res)}")
if len(sig10):
    print(sig10[['signal','horizon','hac_tstat','hac_pvalue','qvalue_bh_10pct','spearman_ic']].to_string(index=False))
print(f"FDR significant at q < 5%:  {len(sig05)} / {len(res)}")
if len(sig05):
    print(sig05[['signal','horizon','hac_tstat','hac_pvalue','qvalue_bh_05pct','spearman_ic']].to_string(index=False))

# Compact binary table for quick interpretation.
b = res[res.type == 'binary'].copy()
if len(b):
    b[['signal','horizon','n','n1','n0','spread_1_minus_0','hac_tstat','hac_pvalue','qvalue_bh_10pct','fdr_significant_10pct']].sort_values('abs_hac_t', ascending=False).to_csv(OUT / 'binary_statistical_validation.csv', index=False)

print("\nIMPORTANT:")
print("- HAC p-values account for serial dependence caused by overlapping forward-return windows.")
print("- BH/FDR is applied across all 100 signal x horizon tests; it controls false discovery rate, not family-wise error.")
print("- IID Pearson/Spearman p-values are diagnostics only and should NOT be treated as the final significance test for overlapping horizons.")
print("- Statistical significance is not yet economic significance or proof of out-of-sample alpha.")
