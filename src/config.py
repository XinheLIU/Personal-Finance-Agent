"""
Centralized configuration for the Personal Finance Agent.
"""

# -- Data Configuration --

# A dictionary mapping asset names to their corresponding file names and data sources.
ASSETS = {
    'CSI300': {'akshare': '000300', 'yfinance': None},
    'CSI500': {'akshare': '000905', 'yfinance': None},
    'HSTECH': {'akshare': '159742', 'yfinance': '^HSI'},  # HSTECH ETF (159742), fallback to Hang Seng
    'SP500': {'akshare': None, 'yfinance': '^GSPC'},
    'NASDAQ100': {'akshare': None, 'yfinance': '^NDX'},
    'TLT': {'akshare': None, 'yfinance': 'TLT'},
    'GLD': {'akshare': None, 'yfinance': 'GLD'},
    'CASH': {'akshare': None, 'yfinance': 'CASHX'},
    # US10Y moved to YIELD_ASSETS for FRED API support
}

# A dictionary defining the assets for which to download PE data.
# Use ETF tickers for more accurate PE ratios instead of index tickers
PE_ASSETS = {
    'CSI300': {'akshare': 'INDEX_PE', 'yfinance': None},
    'CSI500': {'akshare': 'MARKET_PE', 'yfinance': None},
    'HSTECH': {'akshare': '159742', 'yfinance': 'FXI'},  # HSTECH ETF from akshare, fallback to FXI
    'SP500': {'akshare': None, 'yfinance': 'SPY'},       # SPDR S&P 500 ETF
    'NASDAQ100': {'akshare': None, 'yfinance': 'QQQ'},   # Invesco QQQ Trust ETF
}

# A dictionary defining yield data sources
YIELD_ASSETS = {
    'US10Y': {'fred': 'DGS10', 'yfinance': '^TNX'},  # FRED 10-Year Treasury Rate, fallback to yfinance
}

# A dictionary mapping asset names to the names used in the backtesting data feeds.
DATA_FILES = {
    'CSI300': 'CSI300',
    'CSI500': 'CSI500', 
    'HSTECH': 'HSTECH',
    'SP500': 'SP500',
    'NASDAQ100': 'NASDAQ100',
    'TLT': 'TLT',
    'GLD': 'GLD',
    'CASH': 'CASH',
    # US10Y data is handled separately in yield data
}

# -- Backtesting Configuration --

INITIAL_CAPITAL = 1000000
COMMISSION = 0.001

# -- Strategy Configuration --

# Parameters for the DynamicAllocationStrategy
DYNAMIC_STRATEGY_PARAMS = {
    'rebalance_days': 360,
    'threshold': 0.05,
}
