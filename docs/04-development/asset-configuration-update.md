# Asset Configuration Update: Separating Tradable Products from Indices

## Overview

This update implements a crucial separation between **tradable products** (used for backtesting/actual trading) and **underlying indices** (used for fundamental analysis like P/E ratios). This ensures the system uses realistic, tradable instruments for backtesting while maintaining accurate fundamental analysis based on underlying indices.

## Key Changes

### 1. New Configuration Structure

#### `TRADABLE_ASSETS` - For Backtesting and Real Trading
Contains actual tradable products (ETFs, funds) that investors can buy:

```python
TRADABLE_ASSETS = {
    'CSI300': {'akshare': '510300', 'yfinance': 'ASHR'},  # CSI300 ETF
    'SP500': {'akshare': None, 'yfinance': 'VOO'},        # S&P 500 ETF (Vanguard)
    'NASDAQ100': {'akshare': None, 'yfinance': 'QQQ'},    # NASDAQ 100 ETF
    # ... etc
}
```

#### `INDEX_ASSETS` - For Fundamental Analysis  
Contains underlying indices for P/E ratios and other fundamental data:

```python
INDEX_ASSETS = {
    'CSI300': {'akshare': '000300', 'yfinance': None},     # CSI 300 Index
    'SP500': {'akshare': None, 'yfinance': '^GSPC'},       # S&P 500 Index  
    'NASDAQ100': {'akshare': None, 'yfinance': '^NDX'},    # NASDAQ 100 Index
    # ... etc
}
```

#### `ASSET_DISPLAY_INFO` - For UI Enhancement
Provides rich display information showing both index and tradable products:

```python
ASSET_DISPLAY_INFO = {
    'SP500': {
        'name': 'S&P 500',
        'index': 'S&P 500 Index',           # Used for P/E analysis
        'tradable_us': 'VOO (ETF)',         # What users actually buy
        'region': 'US Large Cap'
    }
}
```

### 2. Updated Mappings

| Asset | Index (PE Data) | Tradable Product (CN) | Tradable Product (US) |
|-------|----------------|----------------------|----------------------|
| CSI 300 | CSI 300 Index | 510300 (ETF) | ASHR (ETF) |
| CSI 500 | CSI 500 Index | 110020 (Fund) | - |
| Hang Seng | Hang Seng Index | 159920 (ETF) | EWH (ETF) |
| Hang Seng Tech | HS Tech Index | 159742 (ETF) | KTEC (ETF) |
| S&P 500 | S&P 500 Index | - | VOO (ETF) |
| NASDAQ 100 | NASDAQ 100 Index | - | QQQ (ETF) |
| US Treasury | US 10Y Treasury | - | TLT (ETF) |
| Gold | Gold Spot Price | - | GLD (ETF) |
| Cash | US 10Y Yield | - | SHV (ETF) |

### 3. Data Flow Changes

#### Price Data (Backtesting)
- **Source**: `TRADABLE_ASSETS` 
- **Purpose**: Realistic backtesting with actual tradable products
- **Examples**: VOO for S&P 500, QQQ for NASDAQ 100

#### P/E Data (Fundamental Analysis)  
- **Source**: `INDEX_ASSETS` (for fallback methods)
- **Purpose**: Accurate fundamental analysis from underlying indices
- **Examples**: ^GSPC for S&P 500 P/E, ^NDX for NASDAQ 100 P/E

#### UI Display
- **Source**: `ASSET_DISPLAY_INFO`
- **Purpose**: Show both index (for analysis) and tradable products (for investing)
- **Format**: Displays region, index name, and available tradable products

### 4. Enhanced UI Features

The portfolio interface now shows:
- **Asset Name**: User-friendly name (e.g., "S&P 500")
- **Region**: Market classification (e.g., "US Large Cap")  
- **Index (PE Data)**: Source of fundamental analysis (e.g., "S&P 500 Index")
- **Tradable Products**: Actual investment options (e.g., "US: VOO (ETF)")
- **Target/Current Weights**: Allocation percentages
- **Reasoning**: Strategy logic explanation

### 5. Technical Implementation

#### Files Modified:
- `src/config.py`: New asset configuration structure
- `src/data_download.py`: Uses INDEX_ASSETS for P/E fallback methods
- `src/strategy.py`: Imports INDEX_ASSETS for reference
- `src/data_loader.py`: Imports INDEX_ASSETS for compatibility
- `src/gui.py`: Enhanced UI with detailed asset information

#### Backward Compatibility:
- `ASSETS = TRADABLE_ASSETS` maintains existing interfaces
- Existing backtesting code continues to work
- P/E data processing automatically uses correct index sources

### 6. Benefits

1. **Realistic Backtesting**: Uses actual tradable ETFs instead of theoretical indices
2. **Accurate Fundamentals**: P/E analysis based on proper underlying indices  
3. **Clear Investment Guidance**: Users see both analysis source and investment options
4. **International Flexibility**: Supports both Chinese and US tradable products
5. **Professional Presentation**: Enhanced UI shows comprehensive investment information

### 7. Migration Notes

- No user action required for existing installations
- New data downloads will automatically use the correct sources
- Existing P/E data files remain compatible
- Holdings files maintain backward compatibility

This update provides a more professional and realistic investment analysis platform while maintaining the accuracy of fundamental analysis.