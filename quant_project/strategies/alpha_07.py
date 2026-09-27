"""Alpha 07: sparse VB03 supplied-signal continuation."""
from .signal_base import FixedHorizonSignalStrategy

class Alpha07(FixedHorizonSignalStrategy):
    required_signals = ["VB03"]

    def __init__(self, horizon=5):
        super().__init__("VB03_Continuation_5D", horizon, 1)

    def _entry_mask(self, data):
        return data["VB03"].fillna(0).astype(float) > 0
