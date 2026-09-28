"""Task 2 canonical integrity audit for the corrected 986-row signal-library run."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent; OUT=ROOT/"research_output"
daily=pd.read_csv(OUT/"portfolio_daily_returns.csv")
results=json.loads((OUT/"TASK2_CORRECTED_RESULTS.json").read_text())
expected=[
"BB01_Breakout_20D","PB07_TailReversal_10D","BB03_Reversal_10D",
"MeanReversion_Composite_10D","BB03_RegimeFiltered_10D","BB04_Reversal_5D",
"VB03_Continuation_5D","BB07_UpperTail_10D","PB07_BB03_BB04_Conditional"]
checks={
"986 observations":len(daily)==986,
"all nine corrected streams":all(c in daily.columns for c in expected),
"date column": "date" in daily.columns,
"no NaNs": not daily[expected].isna().any().any(),
"nine result records":len(results)==9,
"no return below -100%": bool((daily[expected]<=-1).any().any()) is False,
}
for k,v in checks.items(): print(f"{'PASS' if v else 'FAIL':4s}  {k}")
assert all(checks.values()),"Corrected Task 2 audit failed"
print("Status: PASS")
