"""Alpha 01: BB01 supplied-signal breakout continuation."""
from signal_base import FixedHorizonSignalStrategy
class Alpha01(FixedHorizonSignalStrategy):
    required_signals=["BB01"]
    def __init__(self,horizon=20):
        super().__init__("BB01_Breakout_20D",horizon,1)
    def _entry_mask(self,data):
        return data["BB01"].fillna(0).astype(float)>0
