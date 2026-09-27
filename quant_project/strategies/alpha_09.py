"""Exact conditional PB07/BB03/BB04 decision-tree strategy supplied by the research hypothesis."""

import pandas as pd
from strategy import BaseStrategy


class Alpha09(BaseStrategy):
    required_signals = ["PB07", "BB03", "BB04"]

    def __init__(self):
        super().__init__("PB07_BB03_BB04_Conditional")
        self.fitted = False

    def fit(self, data, targets=None):
        # No parameters are learned; all thresholds are fixed ex ante.
        self.fitted = True

    def generate_features(self, data):
        return data[["date"] + self.required_signals].copy()

    def generate_signal(self, data):
        x = data.reset_index(drop=True).copy()
        sig = pd.Series(0, index=x.index, dtype=int)

        for i in x.index:
            pb07 = float(x.at[i, "PB07"])
            bb03 = float(x.at[i, "BB03"])
            bb04 = float(x.at[i, "BB04"])

            # Preserve the exact priority/order of the proposed rule.
            if pb07 < -0.025:
                sig.at[i] = 1
            elif bb03 == 1 and pb07 > 0.020:
                sig.at[i] = -1
            elif bb04 == 1 and pb07 < -0.010:
                sig.at[i] = 1

        return sig

    def get_metadata(self):
        return {
            **super().get_metadata(),
            "predictive_inputs": self.required_signals,
            "information_set": "supplied signal library only",
            "signal_semantics": "desired position; 0 means flat",
            "fixed_rules": [
                "PB07 < -0.025 -> +1",
                "BB03 == 1 and PB07 > 0.020 -> -1",
                "BB04 == 1 and PB07 < -0.010 -> +1",
            ],
            "thresholds_learned": False,
        }
