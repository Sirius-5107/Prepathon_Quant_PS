"""
Main entry point for Task 1: Data & Backtesting Infrastructure.

Loads data, cleans it, runs a baseline strategy, and produces output.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np

from data_loader import DataLoader
from data_cleaner import DataCleaner
from feature_engine import FeatureEngine
from backtester import Backtester
from strategies.baseline_strategy import BaselineTrendFollowing


def main():
    print("=" * 80)
    print("INTER-IIT QUANTITATIVE FINANCE — TASK 1")
    print("Data & Backtesting Infrastructure")
    print("=" * 80)
    print()
    
    # Configuration
    signals_path = '/mnt/user-data/uploads/signals_train.csv'
    price_path = '/mnt/user-data/uploads/price_train.csv'
    output_dir = '/mnt/user-data/outputs'
    
    os.makedirs(output_dir, exist_ok=True)
    
    # ========== STEP 1: LOAD DATA ==========
    print("[1/5] Loading data...")
    loader = DataLoader()
    signals_raw, price_raw = loader.load(signals_path, price_path)
    print(f"  Signals: {len(signals_raw)} rows, {len(signals_raw.columns)} columns")
    print(f"  Price:   {len(price_raw)} rows, {len(price_raw.columns)} columns")
    print(f"  Signals date range: {signals_raw['date'].min()} to {signals_raw['date'].max()}")
    print(f"  Price date range:   {price_raw['date'].min()} to {price_raw['date'].max()}")
    print()
    
    # ========== STEP 2: CLEAN DATA ==========
    print("[2/5] Cleaning data...")
    cleaner = DataCleaner()
    
    # Validate before cleaning
    quality_report = cleaner.validate(signals_raw, price_raw)
    print(f"  Quality checks:")
    print(f"    - Signals duplicates: {quality_report['signals_duplicates']}")
    print(f"    - Price duplicates:   {quality_report['price_duplicates']}")
    print(f"    - Price high < low:   {quality_report['price_nonsensical']['high_lt_low']}")
    
    signals, price = cleaner.clean(signals_raw, price_raw)
    print(f"  After cleaning:")
    print(f"    - Signals: {len(signals)} rows")
    print(f"    - Price:   {len(price)} rows")
    print()
    
    # ========== STEP 3: FEATURE ENGINEERING & TARGETS ==========
    print("[3/5] Engineering features and targets...")
    feat_engine = FeatureEngine()
    
    # Compute forward returns (for later use in Task 2)
    forward_returns_1 = feat_engine.compute_returns(price, horizon=1)
    forward_returns_5 = feat_engine.compute_returns(price, horizon=5)
    
    print(f"  Forward returns computed:")
    print(f"    - 1-period:   mean={forward_returns_1.mean():.4f}, std={forward_returns_1.std():.4f}")
    print(f"    - 5-period:   mean={forward_returns_5.mean():.4f}, std={forward_returns_5.std():.4f}")
    print()
    
    # ========== STEP 4: RUN BASELINE BACKTEST ==========
    print("[4/5] Running baseline strategy backtest...")
    strategy = BaselineTrendFollowing()
    backtester = Backtester(initial_capital=1e6)
    
    try:
        results = backtester.run(price, signals, strategy)
        
        perf = results['performance']
        print(f"  Baseline performance:")
        print(f"    - Total return:       {perf['total_return_%']:.2f}%")
        print(f"    - Annualized return:  {perf['annualized_return_%']:.2f}%")
        print(f"    - Volatility:         {perf['volatility_%']:.2f}%")
        print(f"    - Sharpe ratio:       {perf['sharpe_ratio']:.3f}")
        print(f"    - Max drawdown:       {perf['max_drawdown_%']:.2f}%")
        print(f"    - Calmar ratio:       {perf['calmar_ratio']:.3f}")
        
        trades_df = results['trades']
        print(f"    - Total trades:       {len(trades_df)}")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # ========== STEP 5: SAVE OUTPUTS ==========
    print("[5/5] Saving outputs...")
    
    # Save equity curve
    equity_df = pd.DataFrame({
        'equity': results['equity_curve']
    })
    equity_path = os.path.join(output_dir, 'baseline_equity_curve.csv')
    equity_df.to_csv(equity_path, index=False)
    print(f"  ✓ Equity curve: {equity_path}")
    
    # Save trades
    trades_path = os.path.join(output_dir, 'baseline_trades.csv')
    results['trades'].to_csv(trades_path, index=False)
    print(f"  ✓ Trade log:    {trades_path}")
    
    # Save performance report
    perf_path = os.path.join(output_dir, 'baseline_performance.json')
    with open(perf_path, 'w') as f:
        json.dump(perf, f, indent=2, default=str)
    print(f"  ✓ Performance:  {perf_path}")
    
    # Save data quality report
    quality_path = os.path.join(output_dir, 'data_quality_report.json')
    with open(quality_path, 'w') as f:
        json.dump(quality_report, f, indent=2, default=str)
    print(f"  ✓ Data quality: {quality_path}")
    
    # Save cleaned data
    signals.to_csv(os.path.join(output_dir, 'signals_cleaned.csv'), index=False)
    price.to_csv(os.path.join(output_dir, 'price_cleaned.csv'), index=False)
    print(f"  ✓ Cleaned data saved")
    
    print()
    print("=" * 80)
    print("TASK 1 COMPLETE")
    print("=" * 80)
    print()
    print("Deliverables ready for Task 2:")
    print("  - Modular backtesting framework")
    print("  - Working end-to-end pipeline")
    print("  - Baseline strategy with metrics")
    print("  - Data quality validation")


if __name__ == '__main__':
    main()
