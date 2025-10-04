# Market Data Download & Management Workflow

## Overview
Downloads market data from external APIs (akshare, yfinance), merges with existing historical data, and stores in singleton CSV files for consumption by backtesting and analysis workflows.

## 🏗️ Architecture

```
src/modules/data_management/
├── data_center/
│   ├── download.py           # Main download logic ⭐
│   ├── data_loader.py         # Load & normalize data
│   └── data_processor.py      # Strategy-specific processing
```

## 📊 Data Flow

```
External APIs → Download → Merge with Existing → Singleton CSV → Data Loader → Strategies
    │              │              │                    │
    │              │              │                    └─ data/raw/{type}/{asset}_{type}.csv
    │              │              └─ Deduplicate, keep latest
    │              └─ akshare (CN), yfinance (US), manual PE
    └─ Price, P/E, Yield data
```

## 🔄 Workflow Steps

### 1. Data Download
**Entry**: `python -m src.modules.data_management.data_center.download`

```python
# Main download function
def download_all_data():
    download_price_data()     # Historical prices
    download_pe_data()        # P/E ratios
    download_yield_data()     # Interest rates
    process_manual_pe_data()  # User-uploaded PE files
```

### 2. Singleton File Storage Pattern

**Naming**: `{asset_name}_{data_type}.csv`
- Examples: `SP500_price.csv`, `CSI300_pe.csv`, `TLT_yield.csv`

**Merge Logic**:
```python
# _merge_with_existing_and_save_singleton()
1. Load existing singleton file (if exists)
2. Concatenate existing + new data
3. Deduplicate by date (keep='last')  # New data wins
4. Sort by date
5. Save to singleton file
```

### 3. Data Sources

| Data Type | CN Assets | US Assets | Manual |
|-----------|-----------|-----------|--------|
| **Price** | akshare (stock_zh_index_daily) | yfinance | ❌ |
| **P/E** | akshare (index_value_hist_funddb) | Manual upload | ✅ |
| **Yield** | akshare (bond_zh_us_rate) | FRED API / yfinance | ❌ |

### 4. Manual P/E Data Processing

**Location**: `data/raw/pe/manual/`

**Supported Formats**:
- HSI: `date,pe` (Hong Kong format)
- SPX/NASDAQ: `date,pe_ratio` (US format)

**Command**: `python -m src.modules.data_management.data_center.download --process-manual-pe`

## 📁 File Structure

```
data/raw/
├── price/
│   ├── SP500_price.csv
│   ├── CSI300_price.csv
│   └── ...
├── pe/
│   ├── manual/              # User uploads here
│   │   ├── HSI_pe.csv
│   │   └── SPX_pe.csv
│   ├── SP500_pe.csv         # Processed output
│   └── ...
└── yield/
    ├── TLT_yield.csv
    └── ...
```

## 💡 Key Functions

### `download_price_data()`
Downloads price data for all assets in `ASSETS` config.

**CN Assets**: `ak.stock_zh_index_daily(symbol=ticker)`
**US Assets**: `yf.Ticker(ticker).history(period="max")`

### `download_pe_data()`
Downloads P/E ratio data for assets in `PE_ASSETS` config.

**CN Assets**: `ak.index_value_hist_funddb(symbol=ticker, indicator="市盈率")`
**US Assets**: Manual upload required

### `download_yield_data()`
Downloads yield/interest rate data for `YIELD_ASSETS`.

**US Rates**: FRED API → yfinance fallback

### `_merge_with_existing_and_save_singleton()`
Core merge logic that preserves historical data while updating with new downloads.

## ⚠️ Error Handling

**Missing Data**: Logs warning, continues with other assets
**API Failures**: Tries fallback sources (FRED → yfinance)
**Invalid Dates**: Skips rows with parse errors
**Duplicate Dates**: Keeps most recent value

## 🔗 Integration Points

**Consumed By**:
- `data_loader.py::DataLoader` - Loads singleton files into DataFrames
- `data_processor.py::DataProcessor` - Creates strategy-specific datasets
- Backtesting engine - Reads processed data for strategy execution

**Configuration**:
- `config/assets.py` - Defines `ASSETS`, `PE_ASSETS`, `YIELD_ASSETS`
- Asset ticker mappings for each data source

## 📝 CLI Usage

```bash
# Download all data types
python -m src.modules.data_management.data_center.download

# Force refresh (re-download even if exists)
python -m src.modules.data_management.data_center.download --refresh

# Process manual PE data only
python -m src.modules.data_management.data_center.download --process-manual-pe
```

## 📊 Output Example

**SP500_price.csv**:
```csv
date,open,high,low,close,volume
2020-01-02,3244.67,3258.85,3235.53,3257.85,3253000000
2020-01-03,3226.36,3246.84,3222.34,3234.85,3458000000
...
```

**CSI300_pe.csv**:
```csv
date,pe
2020-01-02,12.54
2020-01-03,12.58
...
```
