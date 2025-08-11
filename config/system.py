"""
System Configuration
Core system parameters for backtesting and trading.
"""

# -- Backtesting Configuration --
INITIAL_CAPITAL = 1000000
COMMISSION = 0.0

# -- Strategy Configuration --
# Parameters for the DynamicAllocationStrategy
DYNAMIC_STRATEGY_PARAMS = {
    'rebalance_days': 360,
    'threshold': 0.05,
}

# -- System Configuration --
# Data refresh settings
DATA_REFRESH_INTERVAL_HOURS = 24
CACHE_EXPIRY_DAYS = 7

# Performance analysis settings
PERFORMANCE_LOOKBACK_YEARS = 10
ROLLING_WINDOW_DAYS = [252, 504, 1260]  # 1Y, 2Y, 5Y

# Risk management
MAX_POSITION_SIZE = 0.25  # 25% max allocation per asset
MAX_SECTOR_ALLOCATION = 0.40  # 40% max allocation per sector
REBALANCE_THRESHOLD = 0.05  # 5% deviation triggers rebalance

# Logging configuration
LOG_LEVEL = "INFO"
LOG_ROTATION = "1 week"
LOG_RETENTION = "4 weeks"