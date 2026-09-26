"""Alpha 03: BB03 supplied-signal reversal."""
from .signal_base import FixedHorizonSignalStrategy
class Alpha03(FixedHorizonSignalStrategy):
    required_signals=["BB03"]
    def __init__(self,horizon=10): super().__init__("BB03_Reversal_10D",horizon,-1)
    def _entry_mask(self,data): return data["BB03"].fillna(0).astype(float)>0
