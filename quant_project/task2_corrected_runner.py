"""
Corrected Task 2 runner: supplied signals are the only predictive inputs.
Performance uses fixed one-unit notional and supports long/short events.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from strategies.alpha_01 import Alpha01
from strategies.alpha_02 import Alpha02
from strategies.alpha_03 import Alpha03
from strategies.alpha_04 import Alpha04
from strategies.alpha_05 import Alpha05

SIGNALS = (
    [f"PB{i:02d}" for i in range(1, 9)]
    + [f"BB{i:02d}" for i in range(1, 8)]
    + [f"VB{i:02d}" for i in range(1, 6)]
)
COST = 0.0005


def load_data():
    s = pd.read_csv(ROOT / "signals_cleaned.csv", parse_dates=["date"])
    p = pd.read_csv(ROOT / "price_cleaned.csv", parse_dates=["date"])
    s = s[["date"] + SIGNALS].sort_values("date").drop_duplicates("date")
    p = p.sort_values("date").drop_duplicates("date")
    data = s.merge(p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    return s.reset_index(drop=True), p.reset_index(drop=True), data


def forward_target(data, h=10):
    y = np.full(len(data), np.nan)
    for i in range(len(data) - h):
        y[i] = data.iloc[i + h]["close"] / data.iloc[i + 1]["open"] - 1.0
    return pd.Series(y, index=data.index)


def backtest_events(data, sig, start=0, end=None, cost=COST):
    """Fixed-notional event backtest with long and short support."""
    end = len(data) if end is None else end
    equity = 1.0
    position = 0
    entry_price = None
    trade_returns = []
    daily_equity = []
    completed = 0
    raw_events = 0

    for i in range(start, end):
        signal = int(sig.iloc[i])
        px = float(data.iloc[i]["open"])

        if signal != 0:
            raw_events += 1

        if position != 0 and signal == -position:
            gross = position * (px / entry_price - 1.0)
            net = gross - 2.0 * cost
            equity *= 1.0 + net
            trade_returns.append(net)
            completed += 1
            position = 0
            entry_price = None

        elif position == 0 and signal != 0:
            position = signal
            entry_price = px
            equity *= 1.0 - cost

        marked = equity
        if position != 0 and entry_price is not None:
            marked *= 1.0 + position * (float(data.iloc[i]["close"]) / entry_price - 1.0)
        daily_equity.append(marked)

    eq = pd.Series(daily_equity, dtype=float)
    rets = eq.pct_change().dropna()

    total_return = (eq.iloc[-1] - 1.0) * 100.0 if len(eq) else 0.0
    dd = ((eq / eq.cummax()) - 1.0).min() * 100.0 if len(eq) else 0.0
    vol = rets.std() * np.sqrt(252) * 100.0 if len(rets) > 1 else 0.0
    sharpe = (
        rets.mean() / (rets.std() + 1e-12) * np.sqrt(252)
        if len(rets) > 1 else 0.0
    )

    return {
        "total_return_%": float(total_return),
        "sharpe_ratio": float(sharpe),
        "volatility_%": float(vol),
        "max_drawdown_%": float(dd),
        "trades": int(completed),
        "raw_events": int(raw_events),
    }


def fit_strategy(st, signals, data, start, end):
    tr_sig = signals.iloc[start:end].copy()
    tr_data = data.iloc[start:end].copy()
    target = forward_target(tr_data, 10)
    st.fit(st.generate_features(tr_sig), target)
    return st


def wfo(cls, signals, data, train=504, test=63):
    folds = []
    for k, start in enumerate(range(0, len(data) - train - test + 1, test), 1):
        train_end = start + train
        test_end = train_end + test
        st = fit_strategy(cls(), signals, data, start, train_end)

        # Parameters are fitted only on the training window.
        hist = signals.iloc[:test_end].copy()
        sig = st.generate_signal(st.generate_features(hist))
        metrics = backtest_events(data, sig, train_end, test_end)

        folds.append({
            "fold": k,
            "train_start": str(signals.iloc[start]["date"].date()),
            "train_end": str(signals.iloc[train_end - 1]["date"].date()),
            "test_start": str(signals.iloc[train_end]["date"].date()),
            "test_end": str(signals.iloc[test_end - 1]["date"].date()),
            **metrics,
        })
    return folds


def main():
    signals, price, data = load_data()
    classes = [Alpha01, Alpha02, Alpha03, Alpha04, Alpha05]
    results = []
    streams = {}

    for cls in classes:
        st = fit_strategy(cls(), signals, data, 0, min(504, len(data)))
        sig = st.generate_signal(st.generate_features(signals))
        folds = wfo(cls, signals, data)

        # Descriptive frozen-fit statistic; WFO is the primary OOS evidence.
        full = backtest_events(data, sig)

        results.append({
            "strategy": st.name,
            "metadata": st.get_metadata(),
            "full_sample_frozen_fit": full,
            "wfo_folds": folds,
            "wfo_mean_return_%": float(np.mean([f["total_return_%"] for f in folds])),
            "wfo_mean_sharpe": float(np.mean([f["sharpe_ratio"] for f in folds])),
            "wfo_positive_folds": int(sum(f["total_return_%"] > 0 for f in folds)),
        })
        streams[st.name] = sig.to_numpy(dtype=float)

    corr = pd.DataFrame(streams).corr()
    out = ROOT / "research_output"
    out.mkdir(exist_ok=True)
    (out / "TASK2_CORRECTED_RESULTS.json").write_text(json.dumps(results, indent=2))
    corr.to_csv(out / "TASK2_RETURN_SPACE_CORRELATION.csv")

    print(json.dumps(results, indent=2))
    print(corr.round(4))


if __name__ == "__main__":
    main()
