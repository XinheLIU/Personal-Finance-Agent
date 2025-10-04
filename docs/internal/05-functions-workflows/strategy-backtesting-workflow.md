# Strategy Backtesting Workflow

## Overview
Tests investment strategies on historical market data using backtrader engine with realistic execution modeling (T+1 lag, commissions, slippage). Generates performance metrics, portfolio evolution, and rebalancing logs.

## 🏗️ Architecture

```
src/modules/portfolio/
├── strategies/
│   ├── base.py                  # BaseStrategy, StaticAllocationStrategy
│   ├── builtin/
│   │   ├── static_strategies.py  # 60/40, All-Weather, etc.
│   │   └── dynamic_strategies.py # PE-based, Momentum, Risk Parity
│   └── registry.py              # Strategy registration
├── backtesting/
│   ├── runner.py                # run_backtest() ⭐
│   └── engine.py                # EnhancedBacktestEngine
└── performance/
    └── analytics.py             # PerformanceAnalyzer
```

## 📊 Data Flow

```
Strategy Class + Parameters → Load Market Data → Setup Backtrader →
    Execute with T+1 Lag → Track Portfolio Values → Calculate Metrics →
    Save Results (CSV/JSON) → Optional Attribution Analysis
```

## 🔄 Workflow Steps

### 1. Strategy Selection

**Strategy Types**:
- **Static**: Fixed asset weights (60/40, All-Weather, Permanent Portfolio)
- **Dynamic**: Adaptive weights based on market conditions (PE-based, Momentum)

**Registry**: `strategy_registry.list_strategies()` returns all available strategies

### 2. Backtest Execution

**Entry Function**: `run_backtest(strategy_class, strategy_name, **kwargs)`

```python
# Key parameters
start_date: Optional[date]          # Backtest start (default: earliest data)
end_date: Optional[date]            # Backtest end (default: latest data)
initial_capital: float              # Starting capital (default: config.INITIAL_CAPITAL)
commission: float                   # Commission rate (default: config.COMMISSION)
enable_attribution: bool            # Enable attribution analysis (default: False)
```

### 3. Backtrader Setup

**Process**:
1. Create Cerebro engine: `cerebro = bt.Cerebro()`
2. Set broker capital & commission
3. Load data feeds for all assets
4. Add strategy with parameters
5. Add analyzers (Sharpe, Drawdown, Returns, Trades)

**Execution Modeling**:
- **T+1 Lag**: Orders execute next day (realistic delay)
- **Commission**: Percentage fee per trade
- **Slippage**: Price impact modeling (optional)

### 4. Strategy Execution

**Rebalancing Logic** (inside strategy):
```python
def next(self):
    # Calculate target weights
    target_weights = self.get_target_weights()

    # Rebalance if needed
    if self.should_rebalance():
        self.rebalance_portfolio(target_weights)
        self.log_rebalancing(date, weights)
```

**Rebalancing Triggers**:
- **Periodic**: Monthly, quarterly, annual
- **Threshold**: Drift > 5% from targets
- **Signal-based**: Dynamic strategies respond to indicators

### 5. Portfolio Tracking

**Captured Data**:
- `portfolio_dates`: List of dates
- `portfolio_values`: Portfolio value at each date
- `rebalance_log`: Rebalancing events with weights
- `weights_evolution`: Daily weight changes (optional)

### 6. Metrics Calculation

**Analyzer Output**:
```python
{
    'sharpe_ratio': 1.25,           # Risk-adjusted return
    'max_drawdown': -0.18,          # Worst peak-to-trough decline
    'total_return': 0.45,           # Total return (decimal)
    'annualized_return': 0.12,      # Annualized return (decimal)
    'num_trades': 24                # Total trades executed
}
```

### 7. Results Storage

**Files Created**:
```
analytics/backtests/
├── {strategy}_portfolio_values_{timestamp}.csv
├── {strategy}_rebalance_log.csv
└── {strategy}_performance_report.json
```

**Results Dictionary**:
```python
{
    'strategy_name': str,
    'initial_value': float,
    'final_value': float,
    'total_return': float,
    'annualized_return': float,
    'max_drawdown': float,
    'sharpe_ratio': float,
    'start_date': datetime,
    'end_date': datetime,
    'portfolio_dates': List[datetime],
    'portfolio_values': List[float],
    'portfolio_evolution': DataFrame,      # For attribution
    'rebalance_log': str,                  # CSV path
    'performance_report': dict,            # Detailed metrics
    'attribution_analysis': dict           # If enabled
}
```

## 💡 Key Components

### `run_backtest()` - Main Entry Point
Orchestrates entire backtest workflow from data loading to results persistence.

**Location**: `src/modules/portfolio/backtesting/runner.py`

### `BaseStrategy` - Strategy Base Class
All strategies inherit from this class and implement:
- `get_target_weights()`: Return target asset weights
- `should_rebalance()`: Determine rebalancing trigger
- `get_metadata()`: Strategy description & parameters

**Location**: `src/modules/portfolio/strategies/base.py`

### Backtrader Analyzers
- **SharpeRatio**: Risk-adjusted returns
- **DrawDown**: Maximum drawdown calculation
- **Returns**: Annualized return calculation
- **TradeAnalyzer**: Trade statistics

## ⚠️ Error Handling

**Missing Data**: Skips assets without data, continues with available
**NaN Portfolio Values**: Uses last valid value, logs warning
**Strategy Errors**: Returns None, logs detailed error
**Analyzer Failures**: Falls back to 0.0 for metrics

## 🔗 Integration Points

**Data Input**:
- `DataLoader.load_market_data()` - Loads market data
- `load_data_feed()` - Creates backtrader data feeds

**Strategy Registry**:
- `strategy_registry.get(name)` - Retrieves strategy class
- `strategy_registry.list_strategies()` - Lists all strategies

**Performance Analysis**:
- `PerformanceAnalyzer.generate_performance_report()` - Detailed metrics
- `PerformanceAttributor.generate_attribution_report()` - Attribution analysis

**Attribution**:
- Enabled via `enable_attribution=True`
- Requires: portfolio_data, asset_returns, weights_evolution
- Output: Allocation/selection/interaction effects

## 📝 CLI Usage

```bash
# Run backtest for specific strategy
python src/main.py --mode cli --strategy "60_40_portfolio"

# With custom parameters
python src/main.py --mode cli --strategy "dynamic_allocation" --start-date 2020-01-01
```

## 📝 GUI Usage

Navigate to **Investment Management** → **Strategy Backtesting** tab:
1. Select strategy from dropdown
2. Set backtest parameters (dates, capital)
3. Enable attribution analysis (optional)
4. Click "Run Backtest"
5. View results: metrics, charts, rebalancing log

## 📊 Example Output

**Console Log**:
```
Starting backtest for strategy: 60/40 Portfolio
Starting Portfolio Value: $100,000.00
Final Portfolio Value: $145,234.56
Backtest completed successfully
```

**Performance Metrics**:
```json
{
    "total_return": 0.452,
    "annualized_return": 0.089,
    "sharpe_ratio": 1.34,
    "max_drawdown": -0.156,
    "num_trades": 18
}
```

**Rebalancing Log** (`60_40_portfolio_rebalance_log.csv`):
```csv
date,SP500,TLT,reason
2020-01-01,0.60,0.40,initial
2020-04-01,0.60,0.40,quarterly
2020-07-01,0.60,0.40,quarterly
```
