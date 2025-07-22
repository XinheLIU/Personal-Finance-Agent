# Personal Finance Agent - Multi-Asset Backtesting Framework

A modular backtesting framework for testing custom asset allocation strategies across global markets (Chinese, US, Hong Kong). Features smart data management, professional visualization, and comprehensive testing.

## What It Does

- **Backtest portfolio strategies** with real historical data
- **Smart data downloading** with automatic caching and fallbacks
- **Professional analysis** with performance metrics and charts
- **Easy customization** through modular architecture

**Included Strategies:**
- **Dynamic Allocation**: PE-based valuation strategy with yield considerations
- **Buy & Hold**: Simple benchmark for comparison

## Quick Start

### 1. Setup
```bash
conda activate py-fin  # Use your conda environment
git clone <repo-url>
cd Personal-Finance-Agent
pip install -r requirements.txt
```

### 2. Download Data
```bash
python -m src.data_download
```
Downloads historical price and PE data for all assets with smart caching.

### 3. Run Backtest
```bash
python -m src.main
```

### 4. View Results
- **Console**: Performance summary with key metrics
- **Files**: CSV data and PNG charts in project directory
- **Logs**: Detailed execution logs in `logs/app.log`

## File Structure

```
Personal-Finance-Agent/
├── src/                    # Core framework
│   ├── main.py            # Run backtests
│   ├── strategy.py        # Strategy implementations
│   ├── config.py          # Configuration
│   ├── data_download.py   # Smart data management
│   └── ...               # Other modules
├── tests/                 # Unit tests
├── data/                  # Historical data (auto-generated)
└── logs/                  # Execution logs
```

## Create Your Own Strategy

### 1. Add Strategy Class
```python
# In src/strategy.py
class MyStrategy(bt.Strategy):
    def __init__(self):
        self.market_data = load_market_data()
        self.pe_cache = load_pe_data()
        self.portfolio_values = []
        self.portfolio_dates = []
    
    def calculate_target_weights(self, current_date):
        # Your allocation logic here
        weights = {
            'SP500': 0.6,
            'GLD': 0.4
        }
        return weights
```

### 2. Update Main File
```python
# In src/main.py
from src.strategy import MyStrategy
run_backtest(MyStrategy, "My Strategy")
```

### 3. Test
```bash
python -m pytest tests/ -v
python -m src.main
```

## Configuration

Edit `src/config.py` to:
- **Add new assets** with data source mappings
- **Modify strategy parameters** (rebalancing, thresholds)
- **Adjust backtesting settings** (capital, commission)

## Smart Data Features

- **Automatic caching**: Only downloads missing data periods
- **Date-range naming**: Files named like `CSI300_price_20040101_to_20250715.csv`
- **Multi-source fallbacks**: akshare → yfinance with error handling
- **Refresh option**: Use `--refresh` flag to force re-download

## Troubleshooting

### Common Issues
- **"No PE data available"**: Run `python -m src.data_download`
- **Import errors**: Use `python -m src.main` (not `python src/main.py`)
- **Missing data**: Check `data/` directory and re-run data download

### Useful Commands
```bash
# Check available data
ls data/

# Re-download data
python -m src.data_download --refresh

# Run tests
python -m pytest tests/ -v

# Check logs
tail -f logs/app.log
```

## Dependencies

- **backtrader**: Backtesting engine
- **akshare/yfinance**: Market data sources
- **pandas/numpy**: Data processing
- **matplotlib/seaborn**: Visualization
- **loguru**: Professional logging

## License

Educational use only. Ensure compliance with data provider terms.

