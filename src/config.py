"""
Centralized configuration for the Personal Finance Agent.
"""

# -- Data Configuration --

# A dictionary mapping asset names to their corresponding file names and data sources.
ASSETS = {
    'CSI300': {'akshare': '000300', 'yfinance': None},
    'CSI500': {'akshare': '000905', 'yfinance': None},
    'HSI': {'akshare': None, 'yfinance': '^HSI'},  # Hang Seng Index
    'HSTECH': {'akshare': '159742', 'yfinance': '^HSTECH'},  # Hang Seng Tech Index (ETF 159742)
    'SP500': {'akshare': None, 'yfinance': '^GSPC'},
    'NASDAQ100': {'akshare': None, 'yfinance': '^NDX'},
    'TLT': {'akshare': None, 'yfinance': 'TLT'},
    'GLD': {'akshare': None, 'yfinance': 'GLD'},
    'CASH': {'akshare': None, 'yfinance': 'CASHX'},
    # US10Y moved to YIELD_ASSETS for FRED API support
}

# A dictionary defining the assets for which to download PE data.
# Uses manual downloads for accurate historical P/E ratios + akshare for Chinese indices
PE_ASSETS = {
    'CSI300': {'akshare': 'INDEX_PE', 'manual_file': None},  # Use akshare stock_index_pe_lg()
    'CSI500': {'akshare': 'MARKET_PE', 'manual_file': None},  # Use akshare stock_market_pe_lg()
    'HSI': {'akshare': None, 'manual_file': 'HSI-hist-PE-ratio'},  # Manual download from hsi.com.hk (actual filename)
    'HSTECH': {'akshare': None, 'manual_file': 'HS-Tech-hist-PE-ratio'},  # Manual download from hsi.com.hk (actual filename)
    'SP500': {'akshare': None, 'manual_file': 'SPX-hist-PE-ratio'},  # Manual download from Macrotrends (converted to CSV)
    'NASDAQ100': {'akshare': None, 'manual_file': 'NASDAQ-historical-PE-ratio'},  # Manual download from Macrotrends
}

# A dictionary defining yield data sources
YIELD_ASSETS = {
    'US10Y': {'fred': 'DGS10', 'yfinance': '^TNX'},  # FRED 10-Year Treasury Rate, fallback to yfinance
}

# A dictionary mapping asset names to the names used in the backtesting data feeds.
DATA_FILES = {
    'CSI300': 'CSI300',
    'CSI500': 'CSI500', 
    'HSI': 'HSI',
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
