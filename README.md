# Personal Finance Agent - Multi-Asset Backtesting Framework

A comprehensive backtesting framework for implementing and testing custom asset allocation strategies. This system provides a robust foundation for developing, backtesting, and analyzing multi-asset portfolio strategies with professional-grade visualization and performance analysis.

## Project Overview

This framework provides a complete backtesting environment that allows you to:
- **Implement custom asset allocation strategies** with flexible configuration
- **Backtest multi-asset portfolios** across global markets (Chinese, US, Hong Kong)
- **Analyze performance** with comprehensive metrics and professional visualizations
- **Compare strategies** against benchmarks and other approaches
- **Manage data** with smart downloading and fallback mechanisms

The system includes **demo strategies** to demonstrate the framework's capabilities:
- **Dynamic Allocation Strategy**: Example of PE-based valuation strategy
- **Buy & Hold Strategy**: Simple benchmark for comparison

## Key Framework Features

### 🏗️ **Flexible Strategy Framework**
- **Easy strategy implementation** with clear class structure
- **Configurable parameters** for rebalancing, thresholds, and allocation rules
- **Multiple asset support** across different markets and data sources
- **Extensible architecture** for adding new strategies and assets

### 📊 **Professional Analysis & Visualization**
- **Enhanced seaborn plots** for portfolio performance visualization
- **Comprehensive performance metrics** (returns, drawdown, Sharpe ratio)
- **Strategy comparison tables** with outperformance analysis
- **Multiple output formats** (console, CSV, PNG, logs)

### 🔧 **Robust Data Management**
- **Multi-source data downloading** (akshare, yfinance) with automatic fallbacks
- **Smart file management** with date-range naming and duplicate checking
- **Error handling** with clear user guidance and troubleshooting
- **Support for various data formats** (Chinese and US market conventions)

### 📈 **Advanced Backtesting Engine**
- **Backtrader integration** for reliable backtesting
- **Portfolio value tracking** throughout the backtest period
- **Transaction logging** for strategy transparency
- **Performance attribution** and analysis tools

## Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Personal-Finance-Agent
```

### 2. Set up the virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download required data
```bash
python data_download.py
```

This downloads historical data for demo assets:
- **Price data**: CSI300, CSI500, HSTECH, SP500, NASDAQ100, TLT, GLD, US10Y
- **PE ratio data**: CSI300, CSI500, HSTECH, SP500, NASDAQ100

### 4. Run the demo backtest
```bash
python main.py
```

### 5. Review results
The framework generates:
- **Console output**: Performance summary and comparison tables
- **CSV files**: Detailed performance metrics
- **PNG files**: Professional portfolio performance charts
- **Log files**: Comprehensive execution logs

## Framework Architecture

### **Core Components**

#### **strategy.py** - Strategy Implementation Framework
```python
class YourCustomStrategy(bt.Strategy):
    """
    Template for implementing custom strategies
    """
    params = (
        ('rebalance_days', 30),  # Rebalancing frequency
        ('threshold', 0.01),     # Rebalancing threshold
    )
    
    def __init__(self):
        # Initialize your strategy
        self.portfolio_values = []  # For visualization
        self.portfolio_dates = []
    
    def calculate_target_weights(self, current_date):
        # Implement your allocation logic here
        weights = {}
        # Your custom allocation rules
        return weights
    
    def next(self):
        # Main strategy execution logic
        # Track portfolio value
        # Check rebalancing conditions
        # Execute trades
```

#### **main.py** - Backtesting Engine & Analysis
- **Backtesting orchestration** with backtrader
- **Performance analysis** and metric calculation
- **Visualization generation** with seaborn
- **Strategy comparison** and reporting
- **Multiple output formats** for different use cases

#### **data_download.py** - Data Management System
- **Multi-source data downloading** with fallback mechanisms
- **Smart file management** with automatic naming
- **Error handling** and user guidance
- **Data validation** and format standardization

## Implementing Your Own Strategy

### **1. Create a New Strategy Class**
```python
# In strategy.py or a new file
class MyCustomStrategy(bt.Strategy):
    params = (
        ('rebalance_days', 15),
        ('threshold', 0.02),
    )
    
    def __init__(self):
        # Load your required data
        self.load_market_data()
        self.portfolio_values = []
        self.portfolio_dates = []
    
    def calculate_target_weights(self, current_date):
        # Your custom allocation logic
        weights = {}
        
        # Example: Simple equal-weight allocation
        assets = ['CSI300', 'SP500', 'GLD']
        weight_per_asset = 1.0 / len(assets)
        for asset in assets:
            weights[asset] = weight_per_asset
            
        return weights
    
    def next(self):
        # Track portfolio value
        portfolio_value = self.broker.getvalue()
        self.portfolio_values.append(portfolio_value)
        self.portfolio_dates.append(self.datas[0].datetime.date(0))
        
        # Your rebalancing logic
        if len(self) % self.params.rebalance_days == 0:
            target_weights = self.calculate_target_weights(self.datas[0].datetime.date(0))
            self.rebalance_portfolio(target_weights)
```

### **2. Add Your Strategy to main.py**
```python
# In main.py
from strategy import MyCustomStrategy

# Add to the backtesting section
results = run_backtest(MyCustomStrategy, "My Custom Strategy")
```

### **3. Configure Data Requirements**
```python
# In data_download.py, add your required assets
ASSETS_TO_DOWNLOAD = {
    'MY_ASSET': 'symbol_or_ticker',
    # Add more assets as needed
}
```

## Strategy Configuration Examples

### **Equal Weight Strategy**
```python
def calculate_target_weights(self, current_date):
    weights = {}
    num_assets = len(self.data_feeds)
    equal_weight = 1.0 / num_assets
    
    for asset in self.data_feeds:
        weights[asset] = equal_weight
    
    return weights
```

### **Momentum-Based Strategy**
```python
def calculate_target_weights(self, current_date):
    weights = {}
    
    # Calculate momentum for each asset
    for asset, data_feed in self.data_feeds.items():
        if data_feed is not None:
            # 60-day momentum
            momentum = (data_feed.close[0] / data_feed.close[-60] - 1)
            weights[asset] = max(0, momentum)  # Only positive momentum
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        for asset in weights:
            weights[asset] /= total_weight
    
    return weights
```

### **Risk Parity Strategy**
```python
def calculate_target_weights(self, current_date):
    weights = {}
    
    # Calculate volatility for each asset
    volatilities = {}
    for asset, data_feed in self.data_feeds.items():
        if data_feed is not None:
            # 252-day rolling volatility
            returns = pd.Series([data_feed.close[i] / data_feed.close[i-1] - 1 
                               for i in range(1, min(253, len(data_feed)))])
            volatilities[asset] = returns.std() * np.sqrt(252)
    
    # Equal risk contribution
    total_vol = sum(volatilities.values())
    for asset in volatilities:
        weights[asset] = 1 / (len(volatilities) * volatilities[asset])
    
    return weights
```

## File Structure

```
Personal-Finance-Agent/
├── data/                           # Historical data files
│   ├── *_price_*.csv              # Price data for all assets
│   ├── *_pe_*.csv                 # PE ratio data (if applicable)
│   └── US10Y_price_*.csv          # Yield data
├── logs/                          # Execution logs
├── strategy.py                    # Strategy framework and demo strategies
├── main.py                        # Backtesting engine and analysis
├── data_download.py               # Data management system
├── logger.py                      # Logging configuration
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Dependencies

```
backtrader          # Backtesting framework
akshare             # Chinese market data
yfinance            # US market data
matplotlib          # Basic plotting
seaborn             # Enhanced visualization
pandas              # Data manipulation
loguru              # Logging
numpy               # Numerical computations
```

## Customization Guide

### **Adding New Assets**
1. **Update data_download.py** with new asset symbols
2. **Modify DATA_FILES** mapping in main.py
3. **Update strategy logic** to include new assets

### **Modifying Strategy Parameters**
```python
# In your strategy class
params = (
    ('rebalancing_frequency', 7),    # Rebalance weekly
    ('allocation_threshold', 0.05),  # 5% threshold
    ('max_allocation', 0.4),         # Max 40% per asset
)
```

### **Custom Performance Metrics**
```python
# Add custom analyzers in main.py
cerebro.addanalyzer(bt.analyzers.Calmar, _name='calmar')
cerebro.addanalyzer(bt.analyzers.Sortino, _name='sortino')
```

### **Custom Visualization**
```python
# Modify plot_portfolio_performance() in main.py
def plot_custom_analysis(strategy_name, data):
    # Your custom plotting logic
    pass
```

## Troubleshooting

### **Data Issues**
```bash
# Check available data
ls data/

# Re-download with refresh
python data_download.py --refresh

# Check logs
tail -f logs/app.log
```

### **Strategy Errors**
- **Missing data**: Ensure all required assets are downloaded
- **Date range issues**: Check data file date ranges
- **Allocation errors**: Verify weight calculations sum to 1.0

### **Performance Issues**
- **Low returns**: Review strategy logic and parameters
- **High drawdown**: Adjust rebalancing frequency and thresholds
- **Missing allocations**: Check data availability and strategy logic

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-strategy`
3. **Implement your strategy** with proper documentation
4. **Test thoroughly** with different market conditions
5. **Submit a pull request** with clear description

## License

This project is for educational and research purposes. Please ensure compliance with data provider terms of service.

## Disclaimer

This framework is for educational purposes only. Past performance does not guarantee future results. Always conduct thorough research and consider consulting with financial professionals before making investment decisions.

