"""Alpha 06: BB04 supplied-signal reversal / oversold state."""
from .signal_base import FixedHorizonSignalStrategy

class Alpha06(FixedHorizonSignalStrategy):
    required_signals = ["BB04"]

    def __init__(self, horizon=5):
        super().__init__("BB04_Reversal_5D", horizon, 1)

    def _entry_mask(self, data):
        return data["BB04"].fillna(0).astype(float) > 0
