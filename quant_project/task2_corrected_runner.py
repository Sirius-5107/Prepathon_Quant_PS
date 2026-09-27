"""
Corrected Task 2 runner: supplied signals are the only predictive inputs.

Execution convention:
- signal observed at date t
- order executes at date t+1 open
- fixed holding horizon is encoded by the strategy's exit signal
- performance is marked open-to-open
- transaction cost is charged exactly once per executed side
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
    """Return the causal target matching t signal -> t+1 open entry -> h-day open exit."""
    y = np.full(len(data), np.nan)
    for i in range(len(data) - h - 1):
        entry = float(data.iloc[i + 1]["open"])
        exit_px = float(data.iloc[i + 1 + h]["open"])
        y[i] = exit_px / entry - 1.0
    return pd.Series(y, index=data.index)


def backtest_events(data, sig, start=0, end=None, cost=COST):
    """
    Event backtest with causal next-open execution and open-to-open marking.

    A signal at t executes at t+1 open. The return from open[t-1] to open[t]
    is attributed to the position held before the t-open event. Costs are
    charged once at each executed entry/exit.
    """
    end = len(data) if end is None else min(end, len(data))
    start = max(start, 0)

    equity = 1.0
    position = 0
    completed = 0
    raw_events = 0
    entry_price = None
    trade_returns = []
    daily_equity = []

    for i in range(start, end):
        open_px = float(data.iloc[i]["open"])

        # Mark the position held before today's open using open-to-open return.
        if i > 0 and position != 0:
            prev_open = float(data.iloc[i - 1]["open"])
            equity *= 1.0 + position * (open_px / prev_open - 1.0)

        # signal[i-1] is the information observed at t-1 and executed at t open.
        signal = int(sig.iloc[i - 1]) if i > 0 else 0
        if signal != 0:
            raw_events += 1

        if position != 0 and signal == -position:
            gross = position * (open_px / entry_price - 1.0)
            net = gross - 2.0 * cost
            trade_returns.append(net)
            completed += 1
            equity *= 1.0 - cost
            position = 0
            entry_price = None

        elif position == 0 and signal != 0:
            position = signal
            entry_price = open_px
            equity *= 1.0 - cost

        daily_equity.append(equity)

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
    horizon = int(getattr(st, "horizon", 10))
    target = forward_target(tr_data, horizon)
    st.fit(st.generate_features(tr_sig), target)
    return st


def wfo(cls, signals, data, train=504, test=63):
    folds = []
    for k, start in enumerate(range(0, len(data) - train - test + 1, test), 1):
        train_end = start + train
        test_end = train_end + test
        st = fit_strategy(cls(), signals, data, start, train_end)

        # Generate signals using only observations available through the test date.
        # Execution is shifted one day by backtest_events.
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
