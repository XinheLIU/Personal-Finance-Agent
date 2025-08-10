"""
Centralized configuration for the Personal Finance Agent.
"""

# -- Data Configuration --

# TRADABLE_ASSETS: Actual tradable products used for backtesting and real trading
# These are ETFs, funds, and other instruments that investors can actually buy
TRADABLE_ASSETS = {
    'CSI300': {'akshare': '510300', 'yfinance': 'ASHR'},  # CSI300 ETF (CN: 510300, US: ASHR)
    'CSI500': {'akshare': '110020', 'yfinance': None},    # CSI500 Fund (CN: 110020)
    'HSI': {'akshare': '159920', 'yfinance': 'EWH'},      # Hang Seng ETF (CN: 159920, US: EWH)
    'HSTECH': {'akshare': '159742', 'yfinance': 'KTEC'},  # Hang Seng Tech ETF (CN: 159742, US: KTEC)
    'SP500': {'akshare': None, 'yfinance': 'VOO'},        # S&P 500 ETF (Vanguard VOO)
    'NASDAQ100': {'akshare': None, 'yfinance': 'QQQ'},    # NASDAQ 100 ETF (Invesco QQQ)
    'TLT': {'akshare': None, 'yfinance': 'TLT'},          # US Treasury Bond ETF (Long-term)
    'GLD': {'akshare': None, 'yfinance': 'GLD'},          # Gold ETF
    'CASH': {'akshare': None, 'yfinance': 'SHV'},         # Short-term Treasury ETF (cash equivalent)
    'DBC': {'akshare': None, 'yfinance': 'DBC'},          # Commodity ETF (broad commodities)
    'VEA': {'akshare': None, 'yfinance': 'VEA'},          # Developed International Markets ETF
    'VWO': {'akshare': None, 'yfinance': 'VWO'},          # Emerging Markets ETF
    'VNQ': {'akshare': None, 'yfinance': 'VNQ'},          # Real Estate ETF (REITs)
    'TIP': {'akshare': None, 'yfinance': 'TIP'},          # Treasury Inflation-Protected Securities ETF
    'IEF': {'akshare': None, 'yfinance': 'IEF'},          # Intermediate-Term Treasury Bond ETF
    'SHY': {'akshare': None, 'yfinance': 'SHY'},          # Short-Term Treasury Bond ETF (1-3 year)
}

# INDEX_ASSETS: Underlying indices used for fundamental analysis (PE ratios, etc.)
# These provide the benchmark data but may not be directly tradable
INDEX_ASSETS = {
    'CSI300': {'akshare': '000300', 'yfinance': None},     # CSI 300 Index
    'CSI500': {'akshare': '000905', 'yfinance': None},     # CSI 500 Index
    'HSI': {'akshare': None, 'yfinance': '^HSI'},          # Hang Seng Index
    'HSTECH': {'akshare': None, 'yfinance': '^HSTECH'},    # Hang Seng Tech Index
    'SP500': {'akshare': None, 'yfinance': '^GSPC'},       # S&P 500 Index
    'NASDAQ100': {'akshare': None, 'yfinance': '^NDX'},    # NASDAQ 100 Index
}

# ASSET_DISPLAY_INFO: Information for UI display showing both index and tradable product
ASSET_DISPLAY_INFO = {
    'CSI300': {
        'name': 'CSI 300',
        'index': 'CSI 300 Index',
        'tradable_cn': '510300 (ETF)',
        'tradable_us': 'ASHR (ETF)',
        'region': 'China A-Share'
    },
    'CSI500': {
        'name': 'CSI 500', 
        'index': 'CSI 500 Index',
        'tradable_cn': '110020 (Fund)',
        'tradable_us': None,
        'region': 'China A-Share'
    },
    'HSI': {
        'name': 'Hang Seng',
        'index': 'Hang Seng Index',
        'tradable_cn': '159920 (ETF)',
        'tradable_us': 'EWH (ETF)',
        'region': 'Hong Kong'
    },
    'HSTECH': {
        'name': 'Hang Seng Tech',
        'index': 'Hang Seng Tech Index', 
        'tradable_cn': '159742 (ETF)',
        'tradable_us': 'KTEC (ETF)',
        'region': 'Hong Kong Tech'
    },
    'SP500': {
        'name': 'S&P 500',
        'index': 'S&P 500 Index',
        'tradable_cn': None,
        'tradable_us': 'VOO (ETF)',
        'region': 'US Large Cap'
    },
    'NASDAQ100': {
        'name': 'NASDAQ 100',
        'index': 'NASDAQ 100 Index',
        'tradable_cn': None, 
        'tradable_us': 'QQQ (ETF)',
        'region': 'US Tech'
    },
    'TLT': {
        'name': 'US Treasury Bonds',
        'index': 'US 10Y Treasury',
        'tradable_cn': None,
        'tradable_us': 'TLT (ETF)',
        'region': 'US Bonds'
    },
    'GLD': {
        'name': 'Gold',
        'index': 'Gold Spot Price',
        'tradable_cn': None,
        'tradable_us': 'GLD (ETF)', 
        'region': 'Commodities'
    },
    'CASH': {
        'name': 'USD Cash',
        'index': 'US 10Y Yield',
        'tradable_cn': None,
        'tradable_us': 'SHV (ETF)',
        'region': 'Cash/Money Market'
    },
    'DBC': {
        'name': 'Commodities',
        'index': 'Commodity Index',
        'tradable_cn': None,
        'tradable_us': 'DBC (ETF)',
        'region': 'Commodities'
    },
    'VEA': {
        'name': 'Developed International',
        'index': 'FTSE Developed Markets',
        'tradable_cn': None,
        'tradable_us': 'VEA (ETF)',
        'region': 'International Developed'
    },
    'VWO': {
        'name': 'Emerging Markets',
        'index': 'FTSE Emerging Markets',
        'tradable_cn': None,
        'tradable_us': 'VWO (ETF)',
        'region': 'International Emerging'
    },
    'VNQ': {
        'name': 'Real Estate',
        'index': 'MSCI US REIT Index',
        'tradable_cn': None,
        'tradable_us': 'VNQ (ETF)',
        'region': 'Real Estate'
    },
    'TIP': {
        'name': 'TIPS Bonds',
        'index': 'US TIPS Index',
        'tradable_cn': None,
        'tradable_us': 'TIP (ETF)',
        'region': 'US Inflation-Protected Bonds'
    },
    'IEF': {
        'name': 'Intermediate Treasury',
        'index': 'US 7-10 Year Treasury',
        'tradable_cn': None,
        'tradable_us': 'IEF (ETF)',
        'region': 'US Intermediate Bonds'
    },
    'SHY': {
        'name': 'Short Treasury',
        'index': 'US 1-3 Year Treasury',
        'tradable_cn': None,
        'tradable_us': 'SHY (ETF)',
        'region': 'US Short-Term Bonds'
    }
}

# For backward compatibility, ASSETS now points to TRADABLE_ASSETS
ASSETS = TRADABLE_ASSETS

# A dictionary defining the assets for which to download PE data.
# Uses manual downloads for accurate historical P/E ratios + akshare for Chinese indices
# Note: For fallback PE data (Yahoo Finance, price estimation), uses INDEX_ASSETS not TRADABLE_ASSETS
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
    'DBC': 'DBC',
    'VEA': 'VEA',
    'VWO': 'VWO',
    'VNQ': 'VNQ',
    'TIP': 'TIP',
    'IEF': 'IEF',
    'SHY': 'SHY',
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
