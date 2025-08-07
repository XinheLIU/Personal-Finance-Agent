# Personal Finance Agent - Multi-Asset Backtesting Framework

A modular backtesting framework for testing custom asset allocation strategies across global markets (Chinese, US, Hong Kong). Features smart data management, professional visualization, and comprehensive testing.

## What It Does

- **Interactive GUI** with Gradio for easy backtesting and portfolio management
- **Backtest portfolio strategies** with real historical data
- **Smart data downloading** with automatic caching and fallbacks
- **Professional analysis** with performance metrics and charts
- **Detailed analytics** with CSV reports and rebalancing logs
- **Easy customization** through modular architecture

**Included Strategies:**
- **Dynamic Allocation**: PE-based valuation strategy with yield considerations
- **60/40 Portfolio**: A classic balanced portfolio.
- **Permanent Portfolio**: Harry Browne's strategy for all economic conditions.
- **All-Weather Portfolio**: Ray Dalio's strategy for weathering economic storms.
- **David Swensen's Portfolio**: A diversified, equity-oriented portfolio.
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

### 3. Launch Application

**GUI Mode (Default):**
```bash
python -m src.main --mode gui
```
This launches the interactive GUI in your browser for easy backtesting and portfolio management.

**Command-Line Mode:**
```bash
# List all strategies
python -m src.main --list-strategies

# Run specific strategy
python -m src.main --strategy SixtyFortyStrategy

# Download data
python -m src.main --download-data

# Run CLI interface
python -m src.cli
```

**CLI Mode with Options:**
```bash
python -m src.cli list               # List all strategies
python -m src.cli run SixtyFortyStrategy  # Run specific strategy
python -m src.cli download --refresh      # Refresh all data
```

### 4. View Results
- **GUI**: Interactive performance charts and portfolio comparison tables
- **Analytics**: Detailed CSV reports and rebalancing logs in `analytics/` directory
- **Console**: Performance summary with key metrics (command-line mode)
- **Logs**: Detailed execution logs in `logs/app.log`

## File Structure

```
Personal-Finance-Agent/
├── src/                    # Core framework
│   ├── main.py            # Entry point (GUI/CLI modes)
│   ├── cli.py             # Command-line interface
│   ├── gui.py             # Gradio web interface
│   ├── strategies/        # Strategy architecture
│   │   ├── base.py        # Base strategy classes
│   │   ├── builtin/       # Built-in strategies
│   │   └── custom/        # User-defined strategies
│   ├── data_download.py   # Smart data management
│   ├── backtest_runner.py # Backtesting engine
│   └── ...               # Other modules
├── tests/                 # Unit tests
├── data/                  # Historical data (auto-generated)
├── analytics/             # Generated reports and logs
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
python -m src.main --mode cli
```

## GUI Features

The Gradio web interface provides four comprehensive tabs:

### **Backtest Tab**
- **Strategy Selection**: Choose from Dynamic Allocation, 60/40, Permanent Portfolio, All Weather, David Swensen, or create custom strategies
- **Strategy Details**: View the underlying assets and their weights for the selected strategy
- **Interactive Parameters**: Adjust rebalancing frequency and threshold sliders
- **Custom Start Date**: Specify backtest start date to analyze performance over different time periods
- **Real-time Results**: View performance metrics and portfolio value charts
- **Easy Testing**: No command-line knowledge required

### **Custom Strategy Tab**
- **Create Your Own**: Define your own fixed-weight portfolio by assigning weights to available assets
- **Backtest Your Creation**: Run a backtest on your custom strategy and see how it performs
- **Weight Validation**: Automatic validation ensures total weights equal 100%

### **Portfolio Tab**
- **Target vs Current**: Compare AI-recommended weights with your holdings
- **Gap Analysis**: Visualize the difference between selected strategy and your current holdings
- **Asset Details**: View region, index source (for PE data), and tradable products (CN/US options)
- **Reasoning Display**: See why each asset is recommended
- **Easy Editing**: Update your current portfolio allocation interactively
- **Auto-sync**: Save changes to local holdings file

### **Data Tab**
- **Available Data Overview**: View all downloaded data files with date ranges
- **Download Data**: Download or refresh all required market data with a single click
- **New Ticker Downloads**: Add new tickers directly from the GUI interface

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
- **"No PE data available"**: Run `python -m src.data_download` or use the "Download Data" button in the GUI.
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

- **gradio**: Interactive web GUI
- **backtrader**: Backtesting engine
- **akshare/yfinance**: Market data sources
- **pandas/numpy**: Data processing
- **matplotlib/seaborn**: Visualization
- **loguru**: Professional logging
- **python-dotenv**: Environment variable management

## License

Educational use only. Ensure compliance with data provider terms.