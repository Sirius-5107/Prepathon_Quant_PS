"""Return-space independence analysis for candidate alpha families.

Research diagnostic only — not a trading strategy.

Question:
    Does BB01 @ 20d contain a return component that is not explained by the
    mean-reversion family {BB03, PB07, BB04}?

Method:
    * Use the existing causal forward-return convention.
    * Build a common 20d target (10d sensitivity is also reported).
    * Convert candidate signals to direction-aware centered scores.
    * Build one payoff vector per candidate signal: score * forward return.
    * Apply QR / Gram-Schmidt to the three mean-reversion payoff vectors.
    * Project the BB01 payoff vector onto the full mean-reversion return space.
    * Measure R^2 explained, residual norm share, and numerical orthogonality.

The output is return-space geometry, not statistical significance or P&L.
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

MR_SIGNALS = ["BB03", "PB07", "BB04"]
ALL_SIGNALS = MR_SIGNALS + ["BB01"]


def centered_rank_score(series: pd.Series, reverse: bool = False) -> pd.Series:
    """Centered percentile score, optionally reversing the economic direction."""
    pct = series.astype(float).rank(method="average", pct=True)
    score = 2.0 * pct - 1.0
    return -score if reverse else score


def centered_binary_score(series: pd.Series, positive_state: int = 1) -> pd.Series:
    """Centered binary score with positive values representing the stated side."""
    x = series.astype(float)
    p = x.mean()
    if positive_state == 1:
        return x - p
    return (1.0 - x) - (1.0 - p)


def unit_rms(series: pd.Series) -> pd.Series:
    """Normalize by RMS; only scale, not direction, is changed."""
    rms = float(np.sqrt(np.nanmean(np.square(series.to_numpy()))))
    if not np.isfinite(rms) or rms == 0:
        raise ValueError("Signal score has zero or invalid RMS")
    return series / rms


def load_data() -> pd.DataFrame:
    """Load signals/prices and compute the project's causal forward returns."""
    s = pd.read_csv(SIGNALS, parse_dates=["date"]).sort_values("date")
    p = pd.read_csv(PRICE, parse_dates=["date"]).sort_values("date")
    s = s.drop_duplicates("date")
    p = p.drop_duplicates("date")

    missing = [c for c in ALL_SIGNALS if c not in s.columns]
    if missing:
        raise ValueError(f"Missing required signals: {missing}")

    df = s.merge(p[["date", "open", "close"]], on="date", how="inner")
    df = df.sort_values("date").reset_index(drop=True)

    # Competition timing convention:
    # signal at t -> execution at t+1 open -> close at t+h.
    for h in [10, 20]:
        df[f"fwd_{h}d"] = df["close"].shift(-h) / df["open"].shift(-1) - 1.0
    return df


def build_payoff_streams(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Build normalized signal-conditioned return vectors at one common horizon."""
    ret_col = f"fwd_{horizon}d"
    cols = ["date", ret_col] + ALL_SIGNALS
    x = df[cols].copy()

    # Direction is fixed from the earlier research findings; no threshold
    # optimization is introduced here.
    x["BB03_score"] = centered_binary_score(x["BB03"], positive_state=0)
    x["PB07_score"] = centered_rank_score(x["PB07"], reverse=True)
    x["BB04_score"] = centered_binary_score(x["BB04"], positive_state=1)
    x["BB01_score"] = centered_binary_score(x["BB01"], positive_state=1)

    score_cols = [f"{s}_score" for s in ALL_SIGNALS]
    valid = x[score_cols + [ret_col]].notna().all(axis=1)
    x = x.loc[valid].reset_index(drop=True)

    # Put each signal on the same geometric scale before constructing return
    # vectors. This prevents a raw-unit difference from driving QR geometry.
    for c in score_cols:
        x[c] = unit_rms(x[c])

    for sig in ALL_SIGNALS:
        x[f"{sig}_return"] = x[f"{sig}_score"] * x[ret_col]

    # Equal-weight mean-reversion composite is retained as a descriptive
    # convenience, but the actual independence test uses the FULL 3D span of
    # BB03/PB07/BB04 return vectors rather than collapsing it to one dimension.
    x["mean_reversion_score"] = unit_rms(
        x[["BB03_score", "PB07_score", "BB04_score"]].mean(axis=1)
    )
    x["mean_reversion_return"] = x["mean_reversion_score"] * x[ret_col]
    return x


def center_matrix(a: np.ndarray) -> np.ndarray:
    """Center each return-space vector before geometric analysis."""
    return a - np.mean(a, axis=0, keepdims=True)


def qr_project(target: np.ndarray, basis: np.ndarray, names: list[str]) -> dict:
    """Project target onto the span of basis using QR decomposition."""
    target = np.asarray(target, dtype=float).reshape(-1)
    basis = np.asarray(basis, dtype=float)

    mask = np.isfinite(target) & np.isfinite(basis).all(axis=1)
    target = target[mask]
    basis = basis[mask]

    target = target - target.mean()
    basis = center_matrix(basis)

    # Reduced QR gives an orthonormal basis for the column space. np.linalg.qr
    # handles near-collinearity more safely than manually inverting X'X.
    Q, R = np.linalg.qr(basis, mode="reduced")
    diag = np.abs(np.diag(R))
    tol = np.finfo(float).eps * max(basis.shape) * (diag.max() if len(diag) else 0.0)
    rank = int(np.sum(diag > tol)) if len(diag) else 0
    Q = Q[:, :rank]

    if rank == 0:
        raise ValueError("Mean-reversion return space has zero numerical rank")

    projection = Q @ (Q.T @ target)
    residual = target - projection

    target_ss = float(np.dot(target, target))
    projection_ss = float(np.dot(projection, projection))
    residual_ss = float(np.dot(residual, residual))

    r2 = projection_ss / target_ss if target_ss else np.nan
    residual_share = np.sqrt(residual_ss / target_ss) if target_ss else np.nan

    # Pairwise correlations are supplemental diagnostics, not the independence
    # test itself.
    corr = np.corrcoef(np.column_stack([basis, target]).T)[-1, :-1]
    pairwise = {names[i]: float(corr[i]) for i in range(len(names))}

    # The residual is orthogonal to every retained Q column by construction.
    max_q_orth = float(np.max(np.abs(Q.T @ residual))) if rank else np.nan

    return {
        "n": int(len(target)),
        "basis_rank": rank,
        "basis_dimension": int(basis.shape[1]),
        "projection_r_squared": float(r2),
        "residual_norm_share": float(residual_share),
        "residual_mean": float(residual.mean()),
        "residual_std": float(residual.std(ddof=1)),
        "r2_plus_residual_sq": float(r2 + residual_share ** 2),
        "max_Q_residual_dot": max_q_orth,
        "pairwise_correlations": pairwise,
        "Q": Q,
        "R": R,
        "residual": residual,
        "projection": projection,
        "target": target,
    }


def run_horizon(df: pd.DataFrame, horizon: int) -> tuple[dict, pd.DataFrame]:
    """Run full-space QR test and return summary plus inspectable streams."""
    streams = build_payoff_streams(df, horizon)

    basis_cols = [f"{s}_return" for s in MR_SIGNALS]
    target_col = "BB01_return"
    result = qr_project(
        streams[target_col].to_numpy(),
        streams[basis_cols].to_numpy(),
        MR_SIGNALS,
    )

    summary = {
        "horizon": horizon,
        "target_stream": target_col,
        "basis_streams": ",".join(basis_cols),
        "n": result["n"],
        "basis_dimension": result["basis_dimension"],
        "basis_rank": result["basis_rank"],
        "bb01_explained_r2": result["projection_r_squared"],
        "bb01_residual_norm_share": result["residual_norm_share"],
        "bb01_residual_mean": result["residual_mean"],
        "bb01_residual_std": result["residual_std"],
        "r2_plus_residual_sq": result["r2_plus_residual_sq"],
        "max_Q_residual_dot": result["max_Q_residual_dot"],
        "corr_bb03": result["pairwise_correlations"]["BB03"],
        "corr_pb07": result["pairwise_correlations"]["PB07"],
        "corr_bb04": result["pairwise_correlations"]["BB04"],
    }

    # Add the orthogonal BB01 component as an inspectable research vector.
    streams["bb01_projection_from_mr"] = result["projection"]
    streams["bb01_orthogonal_residual"] = result["residual"]
    return summary, streams


def component_summary(streams: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Basic diagnostics for individual payoff vectors and composite."""
    names = ["BB03", "PB07", "BB04", "BB01", "MeanReversion"]
    cols = [
        "BB03_return", "PB07_return", "BB04_return", "BB01_return",
        "mean_reversion_return",
    ]
    rows = []
    for name, col in zip(names, cols):
        rows.append({
            "horizon": horizon,
            "stream": name,
            "n": len(streams),
            "mean": float(streams[col].mean()),
            "std": float(streams[col].std(ddof=1)),
        })
    return pd.DataFrame(rows)


def main() -> None:
    df = load_data()
    summaries = []
    components = []

    for horizon in [20, 10]:
        summary, streams = run_horizon(df, horizon)
        summaries.append(summary)
        components.append(component_summary(streams, horizon))
        if horizon == 20:
            streams.to_csv(OUT / "return_space_streams_20d.csv", index=False)

    summary_df = pd.DataFrame(summaries)
    component_df = pd.concat(components, ignore_index=True)
    summary_df.to_csv(OUT / "return_space_qr_summary.csv", index=False)
    component_df.to_csv(OUT / "return_space_component_summary.csv", index=False)

    p = summary_df.iloc[0]
    print("\n" + "=" * 80)
    print("RETURN-SPACE INDEPENDENCE — QR / GRAM-SCHMIDT")
    print("=" * 80)
    print("Question: Does BB01 contain return-space information outside the")
    print("          full {BB03, PB07, BB04} mean-reversion return space?")
    print("Primary common horizon: 20d")
    print("No threshold optimization; no strategy construction.")
    print()
    print(f"N: {int(p['n'])}")
    print(f"Mean-reversion return-space rank: {int(p['basis_rank'])}/3")
    print(f"BB01 explained R^2: {p['bb01_explained_r2']:.4f}")
    print(f"BB01 residual norm share: {p['bb01_residual_norm_share']:.4f}")
    print(f"R^2 + residual_share^2: {p['r2_plus_residual_sq']:.4f}")
    print(f"Max |Q' residual|: {p['max_Q_residual_dot']:.3e}")
    print(f"Pairwise corr(BB01, BB03): {p['corr_bb03']:.4f}")
    print(f"Pairwise corr(BB01, PB07): {p['corr_pb07']:.4f}")
    print(f"Pairwise corr(BB01, BB04): {p['corr_bb04']:.4f}")
    print()
    print("Interpretation:")
    print("  High explained R^2 / low residual share -> BB01 overlaps the")
    print("  mean-reversion return space.")
    print("  Low explained R^2 / high residual share -> BB01 has a distinct")
    print("  return direction, supporting a separate breakout family.")
    print()
    print("Outputs:")
    print("  research_output/return_space_streams_20d.csv")
    print("  research_output/return_space_qr_summary.csv")
    print("  research_output/return_space_component_summary.csv")


if __name__ == "__main__":
    main()
