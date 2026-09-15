"""
Central configuration for the PREPATHON Quant Task 1 backtesting pipeline.

All competition-mandated execution and portfolio assumptions are defined here
so that they are not duplicated across modules.

Reference: Inter-IIT Tech Meet 15.0 Quantitative Finance Prepathon Task 1.1
"""

# ============================================================================
# PORTFOLIO
# ============================================================================

INITIAL_CAPITAL = 1_000_000.0  # $1M starting capital per competition spec


# ============================================================================
# EXECUTION ASSUMPTIONS (MANDATORY - DO NOT MODIFY)
# ============================================================================

# Transaction Costs
TRANSACTION_COST_PER_SIDE = 0.0005  # 0.05% per side (competition-mandated)
# Full round-trip cost = 0.05% entry + 0.05% exit = 0.10%

# Slippage
SLIPPAGE_PER_SIDE = 0.0  # No additional slippage specified in competition rules

# Position Sizing
DEFAULT_POSITION_SIZE = 1.0  # 1 unit per trade (no leverage, no fractional sizing)


# ============================================================================
# RESEARCH TIMING CONVENTION (MANDATORY - DO NOT MODIFY)
# ============================================================================

# Signal Availability
SIGNAL_CUTOFF = "t-1"
# Signals available through the CLOSE of candle t-1.
# Decision for candle t is based on information known at t-1 close.
# This prevents look-ahead bias.

# Execution Price
EXECUTION_PRICE = "open"
# All trades execute at the OPEN price of the candle on which the signal fires.
# NOT at the close of t-1, NOT at the close of t, NOT intra-candle.

# Per-candle loop structure (enforced in backtester):
# for t in candles:
#     inputs_t = signal_library rows up to and including t-1
#     decision_t = strategy.generate_signal(inputs_t)
#     execute decision_t at price = open[t]


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

TRADING_DAYS_PER_YEAR = 252  # Standard calendar trading days
RISK_FREE_RATE = 0.02  # 2.0% annual risk-free rate (for Sharpe, Sortino, Calmar)


# ============================================================================
# DATA REQUIREMENTS
# ============================================================================

# Expected columns in price data
PRICE_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']

# Expected date column name
DATE_COLUMN = 'date'

# Minimum data quality thresholds
MIN_TRADING_DAYS = 100  # Require at least 100 days of data
MAX_MISSING_PCT = 0.05  # Allow up to 5% missing values


# ============================================================================
# BACKTESTER SETTINGS
# ============================================================================

# Mark-to-Market
MARK_TO_MARKET = True  # Update portfolio equity daily using market prices
MTM_FREQUENCY = "daily"  # Mark to market at end of each trading day

# Reporting
REPORT_YEARLY = True  # Generate yearly performance breakdown
REPORT_DRAWDOWN = True  # Track and report maximum drawdown
REPORT_TRADES = True  # Log individual trade results


# ============================================================================
# VALIDATION
# ============================================================================

# These settings enforce research integrity per Task 1.1

# Check for look-ahead
CHECK_LOOKAHEAD = True

# Enforce chronological ordering
ENFORCE_CHRONOLOGICAL = True

# Detect and handle duplicates
DETECT_DUPLICATES = True

# Handle missing observations
HANDLE_MISSING = True

# Validate transaction cost application
VALIDATE_TRANSACTION_COSTS = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_transaction_cost(notional):
    """Calculate total transaction cost for a given notional amount."""
    return notional * (2 * TRANSACTION_COST_PER_SIDE)  # Entry + exit


def get_round_trip_cost_pct():
    """Get the round-trip cost as a percentage."""
    return 2 * TRANSACTION_COST_PER_SIDE


def get_sharpe_denominator():
    """Get the denominator for Sharpe ratio calculation."""
    return np.sqrt(TRADING_DAYS_PER_YEAR)


if __name__ == "__main__":
    print("Task 1 Configuration Loaded")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,.0f}")
    print(f"Transaction Cost (round-trip): {get_round_trip_cost_pct()*100:.2f}%")
    print(f"Execution Price: {EXECUTION_PRICE}")
    print(f"Signal Cutoff: {SIGNAL_CUTOFF}")
    print(f"Trading Days/Year: {TRADING_DAYS_PER_YEAR}")
    print(f"Risk-Free Rate: {RISK_FREE_RATE*100:.1f}%")
