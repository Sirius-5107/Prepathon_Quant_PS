"""
Return-space independence analysis for candidate alpha families.

Purpose
-------
Test whether the candidate breakout family (BB01) contributes a genuinely
separate return component from the mean-reversion family (BB03, PB07, BB04).

This is deliberately a research diagnostic, NOT a trading strategy.

Method
------
1. Merge causal signals with price data using the existing project convention.
2. Build a common 20-day forward-return target:
       fwd_20d[t] = close[t+20] / open[t+1] - 1
3. Convert each signal into a direction-aware, centered score:
   - BB03: overbought is negative -> reverse BB03
   - PB07: high trend-distance is negative -> reverse percentile score
   - BB04: oversold is positive -> positive BB04
   - BB01: breakout is positive -> centered breakout indicator
4. Standardize the individual signal scores to unit RMS and form an equal-
   weight mean-reversion family score. No threshold search is performed.
5. Form research payoff streams:
       family_score[t] * fwd_20d[t]
   These are signal-conditioned return vectors, not executable strategy P&L.
6. Apply QR / Gram-Schmidt to the return vectors. Project BB01's return
   stream onto the mean-reversion return stream and measure the residual.
7. Also run the reverse projection and report cosine similarity, correlation,
   R^2, residual norm share, and residual mean.

Why a common 20-day horizon?
----------------------------
BB01's candidate effect was identified at 20d. Using the same forward-return
horizon for both families avoids making the independence result a comparison
of different target horizons. A 10d sensitivity check is also reported.

Interpretation
--------------
- High R^2 / small residual: BB01 return behavior is largely explained by the
  mean-reversion return space -> weak evidence for a distinct family.
- Low R^2 / large residual: BB01 occupies a different return direction ->
  evidence supporting an independent breakout family.

Important limitation
--------------------
QR orthogonality is descriptive. It does not establish statistical significance
or economic causality. The result must be combined with temporal stability,
multiple-testing awareness, and later walk-forward robustness.
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ROOT / "signals_cleaned.csv"
PRICE = ROOT / "price_cleaned.csv"
OUT = ROOT / "research_output"
OUT.mkdir(exist_ok=True)

SIGNAL_COLUMNS = ["BB03", "PB07", "BB04", "BB01"]


def centered_rank_score(series: pd.Series, reverse: bool = False) -> pd.Series:
    """Map a signal to a centered percentile score in approximately [-1, 1]."""
    x = series.astype(float)
    pct = x.rank(method="average", pct=True)
    score = 2.0 * pct - 1.0
    if reverse:
        score = -score
    return score


def centered_binary_score(series: pd.Series, positive_state: int = 1) -> pd.Series:
    """Create a centered binary score while preserving zero net mean."""
    x = series.astype(float)
    p = x.mean()
    if positive_state == 1:
        score = x - p
    else:
        score = (1.0 - x) - (1.0 - p)
    return score


def unit_rms(series: pd.Series) -> pd.Series:
    """Scale a score by its RMS; linear scaling does not change its direction."""
    rms = float(np.sqrt(np.nanmean(np.square(series.values))))
    if not np.isfinite(rms) or rms == 0:
        raise ValueError("Signal score has zero or invalid RMS")
    return series / rms


def make_data() -> pd.DataFrame:
    """Load data and compute the project's causal forward-return convention."""
    s = pd.read_csv(SIGNALS, parse_dates=["date"])
    p = pd.read_csv(PRICE, parse_dates=["date"])

    s = s.sort_values("date").drop_duplicates("date")
    p = p.sort_values("date").drop_duplicates("date")

    missing = [c for c in SIGNAL_COLUMNS if c not in s.columns]
    if missing:
        raise ValueError(f"Missing required signal columns: {missing}")

    df = s.merge(
        p[["date", "open", "close"]],
        on="date",
        how="inner",
    ).sort_values("date").reset_index(drop=True)

    # Existing competition timing convention:
    # signal at t -> execution at t+1 open -> close at t+h.
    df["fwd_20d"] = df["close"].shift(-20) / df["open"].shift(-1) - 1.0
    df["fwd_10d"] = df["close"].shift(-10) / df["open"].shift(-1) - 1.0
    return df


def build_streams(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Build the two family-conditioned return vectors at one common horizon."""
    ret_col = f"fwd_{horizon}d"
    x = df[["date", "BB03", "PB07", "BB04", "BB01", ret_col]].copy()

    # Directional scores reflect the hypotheses established earlier in the
    # research funnel. No new thresholds or fitted parameters are introduced.
    x["bb03_score"] = centered_binary_score(x["BB03"], positive_state=0)
    x["pb07_score"] = centered_rank_score(x["PB07"], reverse=True)
    x["bb04_score"] = centered_binary_score(x["BB04"], positive_state=1)
    x["bb01_score"] = centered_binary_score(x["BB01"], positive_state=1)

    # Restrict the scaling sample to rows with all candidate signals and target.
    valid = x[["bb03_score", "pb07_score", "bb04_score", "bb01_score", ret_col]].notna().all(axis=1)
    z = x.loc[valid].copy().reset_index(drop=True)

    for c in ["bb03_score", "pb07_score", "bb04_score", "bb01_score"]:
        z[c + "_rms"] = unit_rms(z[c])

    # Equal-weight family score after unit-RMS normalization.
    z["mean_reversion_score"] = z[[
        "bb03_score_rms", "pb07_score_rms", "bb04_score_rms"
    ]].mean(axis=1)
    z["mean_reversion_score"] = unit_rms(z["mean_reversion_score"])
    z["bb01_score_rms"] = unit_rms(z["bb01_score_rms"])

    # Research return streams. These are payoff vectors for geometric
    # independence analysis, not a backtest and not executable P&L.
    z["mean_reversion_return"] = z["mean_reversion_score"] * z[ret_col]
    z["bb01_return"] = z["bb01_score_rms"] * z[ret_col]

    return z


def qr_two_vectors(a: np.ndarray, b: np.ndarray) -> dict:
    """Gram-Schmidt projection of b onto a plus return-space diagnostics."""
    A = np.asarray(a, dtype=float)
    B = np.asarray(b, dtype=float)

    mask = np.isfinite(A) & np.isfinite(B)
    A = A[mask]
    B = B[mask]

    # Center payoff vectors before measuring geometric similarity. This avoids
    # a common unconditional mean dominating the direction comparison.
    A = A - A.mean()
    B = B - B.mean()

    norm_a = np.linalg.norm(A)
    norm_b = np.linalg.norm(B)
    if norm_a == 0 or norm_b == 0:
        raise ValueError("One return vector has zero variance")

    q1 = A / norm_a
    projection = np.dot(B, q1) * q1
    residual = B - projection

    corr = float(np.corrcoef(A, B)[0, 1])
    cosine = float(np.dot(A, B) / (norm_a * norm_b))
    r2 = float(np.dot(projection, projection) / np.dot(B, B))
    residual_share = float(np.linalg.norm(residual) / norm_b)

    # Numerical guard: R2 + residual_share^2 should be ~1.
    residual_mean = float(residual.mean())
    residual_std = float(residual.std(ddof=1))

    return {
        "n": int(len(A)),
        "correlation": corr,
        "cosine_similarity": cosine,
        "projection_r_squared": r2,
        "residual_norm_share": residual_share,
        "residual_mean": residual_mean,
        "residual_std": residual_std,
        "gram_schmidt_check": float(r2 + residual_share ** 2),
    }


def component_matrix(streams: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Pairwise return-space diagnostics for the family and its components."""
    cols = {
        "BB03": "bb03_score_rms",
        "PB07": "pb07_score_rms",
        "BB04": "bb04_score_rms",
        "BB01": "bb01_score_rms",
        "MeanReversion": "mean_reversion_score",
    }
    rows = []
    ret_col = f"fwd_{horizon}d"

    for name, score_col in cols.items():
        payoff = streams[score_col] * streams[ret_col]
        rows.append({
            "horizon": horizon,
            "stream": name,
            "mean": payoff.mean(),
            "std": payoff.std(ddof=1),
            "n": len(payoff),
        })

    return pd.DataFrame(rows)


def run(horizon: int) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    streams = build_streams(make_data(), horizon)
    ret_col = f"fwd_{horizon}d"

    # QR / Gram-Schmidt in return space: BB01 explained by the mean-reversion
    # return vector, then the residual is the candidate independent component.
    forward = qr_two_vectors(
        streams["mean_reversion_return"].values,
        streams["bb01_return"].values,
    )
    reverse = qr_two_vectors(
        streams["bb01_return"].values,
        streams["mean_reversion_return"].values,
    )

    summary = {
        "horizon": horizon,
        "target": ret_col,
        "direction": "BB01_return projected onto MeanReversion_return",
        **forward,
        "reverse_projection_r_squared": reverse["projection_r_squared"],
    }

    component = component_matrix(streams, horizon)
    return streams, component, summary


def main() -> None:
    all_summaries = []
    all_components = []

    for horizon in [20, 10]:
        streams, components, summary = run(horizon)
        all_summaries.append(summary)
        all_components.append(components)

        if horizon == 20:
            # Save the primary candidate-horizon return vectors for inspection.
            streams.to_csv(OUT / "return_space_streams_20d.csv", index=False)

    summary_df = pd.DataFrame(all_summaries)
    component_df = pd.concat(all_components, ignore_index=True)

    summary_df.to_csv(OUT / "return_space_qr_summary.csv", index=False)
    component_df.to_csv(OUT / "return_space_component_summary.csv", index=False)

    primary = summary_df.loc[summary_df["horizon"] == 20].iloc[0]

    print("\n" + "=" * 80)
    print("RETURN-SPACE INDEPENDENCE — QR / GRAM-SCHMIDT")
    print("=" * 80)
    print("Primary comparison: Mean-Reversion family vs BB01 breakout")
    print("Primary common horizon: 20d")
    print("No threshold optimization; no strategy construction.")
    print()
    print(f"N: {int(primary['n'])}")
    print(f"Correlation: {primary['correlation']:.4f}")
    print(f"Cosine similarity: {primary['cosine_similarity']:.4f}")
    print(f"BB01 explained R^2 by mean-reversion return space: {primary['projection_r_squared']:.4f}")
    print(f"BB01 residual norm share: {primary['residual_norm_share']:.4f}")
    print(f"Gram-Schmidt check (R^2 + residual_share^2): {primary['gram_schmidt_check']:.4f}")
    print(f"Residual mean: {primary['residual_mean']:.6f}")
    print(f"Reverse projection R^2: {primary['reverse_projection_r_squared']:.4f}")
    print()
    print("10d sensitivity is saved in return_space_qr_summary.csv")
    print()
    print("Interpretation rule:")
    print("  High R^2 / low residual share -> BB01 largely overlaps the")
    print("  mean-reversion return space.")
    print("  Low R^2 / high residual share -> BB01 has a distinct return direction.")
    print()
    print("Outputs:")
    print("  research_output/return_space_streams_20d.csv")
    print("  research_output/return_space_qr_summary.csv")
    print("  research_output/return_space_component_summary.csv")


if __name__ == "__main__":
    main()
