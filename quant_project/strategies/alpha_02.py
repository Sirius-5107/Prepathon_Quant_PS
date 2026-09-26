"""Alpha 02: PB07 supplied-signal tail reversal. No P/B reconstruction."""
from signal_base import FixedHorizonSignalStrategy, causal_tail_threshold
class Alpha02(FixedHorizonSignalStrategy):
    required_signals=["PB07"]
    def __init__(self,horizon=10,q=0.20,min_obs=60):
        super().__init__("PB07_TailReversal_10D",horizon,1)
        self.q=q; self.min_obs=min_obs; self.threshold_=None
    def fit(self,data,targets=None):
        x=data["PB07"].astype(float)
        self.threshold_=x.dropna().quantile(self.q)
        self.fitted=True
    def _entry_mask(self,data):
        if self.threshold_ is None: self.fit(data)
        return data["PB07"].astype(float)<=self.threshold_
    def get_metadata(self):
        return {**super().get_metadata(),"threshold_type":"training-window empirical quantile",
                "quantile":self.q,"min_training_observations":self.min_obs}
