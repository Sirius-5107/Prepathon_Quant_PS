"""
Exploratory signal-shape analysis for Task 2.

Purpose
-------
1. Continuous signals: inspect quintile return shapes, monotonicity and tail spreads.
2. Binary signals: inspect conditional return distributions for selected candidate signals.

IMPORTANT: This is DESCRIPTIVE RESEARCH, not a strategy backtest. Full-sample
quantile cutoffs are intentionally used here to understand signal shape. Any
strategy built later MUST estimate thresholds/quantiles using training data only
inside walk-forward validation.

Timing convention
-----------------
Signal observed on date t -> trade at t+1 open.
For horizon h, target = close[t+h] / open[t+1] - 1.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT
OUT_DIR = ROOT / "research_output"
OUT_DIR.mkdir(exist_ok=True)

SIGNAL_PATH = DATA_DIR / "signals_cleaned.csv"
PRICE_PATH = DATA_DIR / "price_cleaned.csv"
HORIZONS = [1, 3, 5, 10, 20]
CONTINUOUS = ["PB07", "PB08", "BB06", "BB07", "VB05"]
BINARY_CANDIDATES = ["BB03", "BB04", "VB03", "VB04", "VB01", "BB01", "BB02"]


def load_data():
    sig = pd.read_csv(SIGNAL_PATH)
    px = pd.read_csv(PRICE_PATH)
    sig["date"] = pd.to_datetime(sig["date"])
    px["date"] = pd.to_datetime(px["date"])
    df = sig.merge(px[["date", "open", "close"]], on="date", how="inner")
    df = df.sort_values("date").reset_index(drop=True)

    for h in HORIZONS:
        # t signal -> t+1 open through t+h close
        df[f"fwd_{h}d"] = df["close"].shift(-h) / df["open"].shift(-1) - 1
    return df


def continuous_quintiles(df):
    rows = []
    summary = []

    for signal in CONTINUOUS:
        # Descriptive full-sample bins only; not used as a trading threshold.
        valid_signal = df[signal].notna()
        try:
            q = pd.qcut(df.loc[valid_signal, signal], 5, labels=False, duplicates="drop") + 1
        except ValueError:
            continue
        qfull = pd.Series(np.nan, index=df.index)
        qfull.loc[valid_signal] = q.to_numpy()

        for h in HORIZONS:
            tmp = pd.DataFrame({"q": qfull, "r": df[f"fwd_{h}d"]}).dropna()
            grouped = tmp.groupby("q")["r"]
            means = grouped.mean()
            medians = grouped.median()
            counts = grouped.size()
            hits = grouped.apply(lambda x: (x > 0).mean())

            for qi in means.index.astype(int):
                rows.append({
                    "signal": signal, "horizon": h, "quintile": qi,
                    "n": int(counts.loc[qi]),
                    "mean_return": means.loc[qi],
                    "median_return": medians.loc[qi],
                    "hit_rate": hits.loc[qi],
                })

            if len(means) >= 2:
                x = means.index.to_numpy(dtype=float)
                y = means.to_numpy(dtype=float)
                mono_rho, mono_p = stats.spearmanr(x, y)
                expected_monotone = mono_rho
                adjacent = np.diff(y)
                consistency = np.mean(np.sign(adjacent) == np.sign(adjacent).mean()) if len(adjacent) else np.nan
                # More interpretable directional consistency: fraction of adjacent
                # moves matching the overall Q5-Q1 direction.
                overall_dir = np.sign(y[-1] - y[0])
                directional_consistency = (
                    np.mean(np.sign(adjacent) == overall_dir)
                    if overall_dir != 0 and len(adjacent) else np.nan
                )
                summary.append({
                    "signal": signal, "horizon": h,
                    "q1_mean": y[0], "q5_mean": y[-1],
                    "q5_q1_spread": y[-1] - y[0],
                    "quintile_spearman": expected_monotone,
                    "quintile_spearman_p": mono_p,
                    "directional_adjacent_consistency": directional_consistency,
                    "n_total": int(len(tmp)),
                })

    return pd.DataFrame(rows), pd.DataFrame(summary)


def binary_distributions(df):
    rows = []
    for signal in BINARY_CANDIDATES:
        for h in HORIZONS:
            r = df[[signal, f"fwd_{h}d"]].dropna()
            if r.empty:
                continue
            r[signal] = r[signal].astype(int)
            for state in [0, 1]:
                x = r.loc[r[signal] == state, f"fwd_{h}d"]
                if len(x) == 0:
                    continue
                rows.append({
                    "signal": signal, "horizon": h, "state": state,
                    "n": len(x), "mean": x.mean(), "median": x.median(),
                    "std": x.std(ddof=1), "hit_rate": (x > 0).mean(),
                    "p25": x.quantile(.25), "p75": x.quantile(.75),
                })
    return pd.DataFrame(rows)


def binary_spreads(df):
    rows = []
    for signal in BINARY_CANDIDATES:
        for h in HORIZONS:
            r = df[[signal, f"fwd_{h}d"]].dropna()
            if r.empty:
                continue
            x0 = r.loc[r[signal] == 0, f"fwd_{h}d"]
            x1 = r.loc[r[signal] == 1, f"fwd_{h}d"]
            if len(x0) < 2 or len(x1) < 2:
                continue
            tstat, pval = stats.ttest_ind(x1, x0, equal_var=False)
            rows.append({
                "signal": signal, "horizon": h,
                "n1": len(x1), "n0": len(x0),
                "mean1": x1.mean(), "mean0": x0.mean(),
                "spread_1_minus_0": x1.mean() - x0.mean(),
                "median1": x1.median(), "median0": x0.median(),
                "hit1": (x1 > 0).mean(), "hit0": (x0 > 0).mean(),
                "welch_t": tstat, "welch_p": pval,
            })
    return pd.DataFrame(rows)


def main():
    df = load_data()
    print("=" * 72)
    print("SIGNAL SHAPE ANALYSIS")
    print("=" * 72)
    print(f"Merged rows: {len(df)}")
    print(f"Date range: {df.date.min().date()} -> {df.date.max().date()}")
    print("\nThis is descriptive research only; no strategy is being constructed.\n")

    q_detail, q_summary = continuous_quintiles(df)
    q_detail.to_csv(OUT_DIR / "signal_quintile_detail.csv", index=False)
    q_summary.to_csv(OUT_DIR / "signal_quintile_summary.csv", index=False)

    binary_detail = binary_distributions(df)
    binary_detail.to_csv(OUT_DIR / "signal_binary_distributions.csv", index=False)

    binary_summary = binary_spreads(df)
    binary_summary.to_csv(OUT_DIR / "signal_binary_spreads_detailed.csv", index=False)

    print("CONTINUOUS SIGNALS — strongest Q5-Q1 spreads by absolute value")
    print(q_summary.assign(abs_spread=q_summary.q5_q1_spread.abs())
          .sort_values("abs_spread", ascending=False)
          [["signal", "horizon", "q1_mean", "q5_mean", "q5_q1_spread",
            "quintile_spearman", "directional_adjacent_consistency", "n_total"]]
          .head(15).to_string(index=False))

    print("\nBINARY CANDIDATES — largest absolute state spreads")
    print(binary_summary.assign(abs_spread=binary_summary.spread_1_minus_0.abs())
          .sort_values("abs_spread", ascending=False)
          [["signal", "horizon", "n1", "n0", "mean1", "mean0",
            "spread_1_minus_0", "hit1", "hit0", "welch_t", "welch_p"]]
          .head(20).to_string(index=False))

    print("\nFiles written:")
    for p in ["signal_quintile_detail.csv", "signal_quintile_summary.csv",
              "signal_binary_distributions.csv", "signal_binary_spreads_detailed.csv"]:
        print(" -", OUT_DIR / p)


if __name__ == "__main__":
    main()
