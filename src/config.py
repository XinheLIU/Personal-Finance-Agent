"""
Centralized configuration for the Personal Finance Agent.
"""

# -- Data Configuration --

# A dictionary mapping asset names to their corresponding file names and data sources.
ASSETS = {
    'CSI300': {'akshare': '000300', 'yfinance': None},
    'CSI500': {'akshare': '000905', 'yfinance': None},
    'HSTECH': {'akshare': '399006', 'yfinance': '^HSI'},  # Fallback to Hang Seng
    'SP500': {'akshare': None, 'yfinance': '^GSPC'},
    'NASDAQ100': {'akshare': None, 'yfinance': '^NDX'},
    'TLT': {'akshare': None, 'yfinance': 'TLT'},
    'GLD': {'akshare': None, 'yfinance': 'GLD'},
    'CASH': {'akshare': None, 'yfinance': 'CASHX'},
    'US10Y': {'akshare': None, 'yfinance': '^TNX'},
}

# A dictionary defining the assets for which to download PE data.
PE_ASSETS = {
    'CSI300': {'akshare': 'INDEX_PE', 'yfinance': None},
    'CSI500': {'akshare': 'MARKET_PE', 'yfinance': None},
    'HSTECH': {'akshare': None, 'yfinance': '^HSI'},
    'SP500': {'akshare': None, 'yfinance': '^GSPC'},
    'NASDAQ100': {'akshare': None, 'yfinance': '^NDX'},
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
}

# -- Backtesting Configuration --

INITIAL_CAPITAL = 1000000
COMMISSION = 0.001

# -- Strategy Configuration --

# Parameters for the DynamicAllocationStrategy
DYNAMIC_STRATEGY_PARAMS = {
    'rebalance_days': 30,
    'threshold': 0.01,
}
