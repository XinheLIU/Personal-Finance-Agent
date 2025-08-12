# Personal Finance Agent

## System Architecture

### 🏗️ **Core Modules**

- **📊 Data Center**: Clean market data management with raw/processed separation
- **🎯 Strategy Module**: Professional strategy repository with metadata and documentation  
- **🔬 Backtesting Platform**: Historical testing with execution lag modeling and transaction costs
- **📈 Performance Analysis**: Comprehensive metrics, attribution analysis, and reporting
- **⚙️ Management Module**: System coordination, risk management, and strategy orchestration
- **💼 Trading Module**: Order execution framework (simulation/paper/live modes)


### 🚀 **Professional Features**

- **Execution Lag Modeling**: Realistic T+1 execution delays
- **Transaction Cost Analysis**: Commission and slippage modeling  
- **Performance Attribution**: Sector and factor-based analysis
- **Risk Management**: Drawdown analysis, VaR calculations, position limits
- **Strategy Metadata**: Complete documentation and parameter tracking
- **Real-time Health Monitoring**: System status and module diagnostics

## Quick Start

### 1. System Setup
```bash
# Clone and setup environment
git clone <repo-url>
cd Personal-Finance-Agent
conda activate py-fin  # or your preferred environment
pip install -r requirements.txt

# Validate system configuration
python -m src.main --validate
```

### 2. System Initialization
```bash
# Check system health and status
python -m src.main --mode system --status

# Download market data (first-time setup)
python -m src.main --download-data

# Initialize system (optional - done automatically)
python -m src.main --mode system --startup
```

### 3. Launch Interfaces

**🌐 Web GUI (Recommended)**
```bash
python -m src.main                    # Default Streamlit GUI mode
# Opens interactive web interface at http://localhost:8501
```

**⌨️ Command Line Interface**
```bash
python -m src.main --mode cli         # Interactive CLI
python -m src.main --list-strategies  # List available strategies
python -m src.main --strategy-details "Dynamic Allocation"  # Strategy info
```

**🔧 System Management**
```bash
python -m src.main --mode system --status    # System health check
python -m src.main --debug --validate        # Debug mode validation
```

### 4. Professional Workflow

#### Data Management
```bash
python -m src.main --download-data --refresh    # Update all data
```

#### Strategy Development
```bash
# View strategy repository
python -m src.main --list-strategies

# Run backtests with professional metrics
python -m src.main --strategy "My Strategy"

# System health monitoring
python -m src.main --mode system --status
```

#### Performance Analysis
- **Web Dashboard**: Real-time performance visualization and analysis
- **Analytics Directory**: Detailed CSV reports, rebalancing logs, performance attribution
- **System Logs**: Comprehensive execution and error logging in `logs/`
- **Logs**: Detailed execution logs in `logs/app.log`

## Professional System Architecture

```
Personal-Finance-Agent/
├── src/                       # 🏗️ Core system modules (professional architecture)
│   ├── data_center/          # 📊 Market data management
│   │   ├── data_loader.py    # Enhanced data loading with validation
│   │   ├── data_processor.py # Data normalization and analytics
│   │   └── download.py       # Data acquisition and updates
│   ├── strategies/           # 🎯 Strategy repository  
│   │   ├── base.py          # Professional base classes
│   │   ├── metadata.py      # Strategy documentation system
│   │   ├── registry.py      # Strategy management and discovery
│   │   ├── utils.py         # Strategy utilities
│   │   ├── builtin/         # Built-in institutional strategies
│   │   └── custom/          # User-defined strategies
│   ├── backtesting/          # 🔬 Professional testing platform
│   │   ├── engine.py        # Execution lag modeling & transaction costs
│   │   └── runner.py        # Backtest orchestration
│   ├── performance/          # 📈 Analytics and reporting
│   │   └── analytics.py     # Attribution analysis & risk metrics
│   ├── management/           # ⚙️ System orchestration
│   │   └── coordinator.py   # Central system management
│   ├── trading/              # 💼 Order execution framework
│   │   └── executor.py      # Simulation/paper/live trading modes
│   ├── main.py              # Professional CLI with system management
│   ├── gui.py               # Web-based dashboard
│   ├── cli.py               # Interactive command-line interface
│   └── app_logger.py        # Professional logging system
├── config/                   # 🔧 System configuration
│   ├── assets.py            # Asset definitions and mappings
│   └── system.py            # Core system parameters
├── data/                     # 💾 Market data (separated by processing stage)
│   ├── raw/                 # Unprocessed data from sources
│   │   ├── price/           # Historical price data
│   │   ├── pe/              # P/E ratio data  
│   │   └── yield/           # Interest rate data
│   ├── processed/           # Clean, normalized data
│   └── accounts/            # Portfolio holdings and transactions
├── analytics/                # 📊 Generated analysis and reports
│   ├── backtests/           # Detailed backtest results
│   └── performance/         # Performance reports and charts
├── docs/                     # 📖 Documentation and research
├── tests/                    # ✅ Comprehensive test suite
├── notebooks/                # 📓 Analysis and debugging notebooks  
└── logs/                     # 📝 System execution logs
```

## Create Your Own Strategy

### 1. Add Strategy Class
```python
# In src/strategies/custom/my_strategy.py
from src.strategies.base import StaticAllocationStrategy
from src.strategies.metadata import StrategyMetadata

class MyStrategy(StaticAllocationStrategy):
    def get_target_weights(self) -> Dict[str, float]:
        return {
            'SP500': 0.60,
            'TLT': 0.40
        }
    
    def get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="My Custom Strategy",
            strategy_id="my_custom_strategy",
            category="static",
            description="Custom 60/40 portfolio allocation"
        )
```

### 2. Register Strategy
```python
# In src/strategies/registry.py
from src.strategies.custom.my_strategy import MyStrategy

# Add to strategy registry
strategy_registry.register("My Custom Strategy", MyStrategy)
```

### 3. Test and Run
```bash
# Validate system
python -m src.main --validate

# Test your strategy
python -m src.main --list-strategies
python -m src.main --strategy "My Custom Strategy"

# Run comprehensive tests
python -m pytest tests/ -v
```

## GUI Features

The Streamlit web interface provides comprehensive tabs and sections:

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

### Asset Configuration
Edit `config/assets.py` to:
- **Add new assets** with data source mappings (TRADABLE_ASSETS, INDEX_ASSETS)
- **Configure PE data sources** (PE_ASSETS)
- **Set up yield data** (YIELD_ASSETS)

### System Configuration
Edit `config/system.py` to:
- **Adjust backtesting settings** (capital, commission, execution parameters)
- **Modify strategy parameters** (rebalancing thresholds, risk limits)
- **Configure system settings** (logging, performance analysis windows)

## Professional Data Pipeline

### **Smart Raw Data Management**
- **Automatic caching**: Only downloads missing data periods
- **Date-range naming**: Files named like `CSI300_price_20040101_to_20250715.csv`
- **Multi-source fallbacks**: akshare → yfinance with error handling
- **Refresh option**: Use `--refresh` flag to force re-download

### **Strategy-Specific Data Processing**
- **Automated Processing**: Raw data automatically merged into strategy-specific datasets
- **Intelligent Requirements**: Each strategy gets only the data it needs (price, PE, yield)
- **Performance Optimization**: Processed data cached and reused until raw data changes
- **Professional Pipeline**: `/data/raw/` → DataProcessor → `/data/processed/<strategy>/`

### **Data Processing Commands**
```bash
# Process data for all strategies
python -m src.main --process-data

# View processing status
python -m src.main --show-processing-status

# Download and auto-process data
python -m src.main --download-data

# Force refresh and reprocess everything
python -m src.main --refresh-data
```

## Troubleshooting

### Common Issues
- **"No PE data available"**: Run `python -m src.main --download-data` or use the "Download Data" button in the GUI
- **Import errors**: Always use `python -m src.main` (not `python src/main.py`)
- **Missing data**: Check system status with `python -m src.main --mode system --status`
- **Module not found**: Ensure you're running from the project root directory

### Useful Commands
```bash
# System validation and health
python -m src.main --validate
python -m src.main --mode system --status

# Data management  
python -m src.main --download-data --refresh    # Download and auto-process
python -m src.main --process-data                # Process existing raw data
python -m src.main --show-processing-status      # View processed data status
ls data/raw/price/                              # Check raw price data
ls data/processed/                              # Check processed strategy data

# Development and testing
python -m pytest tests/ -v
python -m src.main --debug --validate

# Monitoring
tail -f logs/app.log
```

## Dependencies

- **streamlit**: Interactive web GUI
- **backtrader**: Backtesting engine
- **akshare/yfinance**: Market data sources
- **pandas/numpy**: Data processing
- **matplotlib/seaborn**: Visualization
- **loguru**: Professional logging
- **python-dotenv**: Environment variable management

## License

Educational use only. Ensure compliance with data provider terms.
