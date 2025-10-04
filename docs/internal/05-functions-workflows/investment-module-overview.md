# Investment Module Overview

## Purpose
High-level overview of all investment/portfolio workflows and how they interact to provide end-to-end portfolio management, strategy testing, and performance analysis.

## 🏗️ Module Architecture

```
src/modules/portfolio/
├── strategies/              # Strategy definitions & registry
├── backtesting/             # Historical testing engine
├── performance/             # Analytics & attribution
├── presenters/              # Business logic coordination
├── views/                   # UI components
└── trading/                 # Order execution (future)

src/modules/data_management/
├── data_center/             # Market data download & loading
└── visualization/           # Charts & plotting
```

## 🔄 Workflow Interactions

```
┌─────────────────────────────────────────────────────────────────┐
│                    Investment Module Workflows                   │
└─────────────────────────────────────────────────────────────────┘

1. Market Data Download
   ↓ (Singleton CSV files)

2. Strategy Backtesting ←─── (Strategy Registry)
   ↓ (Backtest results)

3. Performance Analysis ←─── (Portfolio evolution)
   ↓ (Metrics & charts)

4. Performance Attribution ←─── (Returns + weights)
   ↓ (Attribution breakdown)

5. Portfolio Management ←─── (Strategy targets + holdings)
   ↓ (Gap analysis & rebalancing)

   → Rebalance → Back to Step 2 (Test new allocation)
```

## 📋 Workflow Reference Guide

### When to Use Each Workflow

| Task | Workflow | Entry Point |
|------|----------|-------------|
| Download latest market data | [Market Data Download](./market-data-download-workflow.md) | `download.py` CLI |
| Test a strategy historically | [Strategy Backtesting](./strategy-backtesting-workflow.md) | `run_backtest()` |
| Analyze backtest performance | [Performance Analysis](./performance-analysis-workflow.md) | `PerformanceAnalyzer` |
| Understand return drivers | [Performance Attribution](./performance-attribution-workflow.md) | `PerformanceAttributor` |
| Manage current holdings | [Portfolio Management](./portfolio-management-workflow.md) | `PortfolioPresenter` |

## 🔑 Key Components

### Strategy Registry
**Location**: `src/modules/portfolio/strategies/registry.py`

**Purpose**: Central repository of all available strategies

**Methods**:
- `list_strategies()` → Dict of available strategies
- `get(name)` → Retrieve strategy class by name
- `register(name, class)` → Add custom strategy

### Data Loader
**Location**: `src/modules/data_management/data_center/data_loader.py`

**Purpose**: Load and normalize market data for consumption

**Methods**:
- `load_market_data()` → All asset price data
- `load_pe_data()` → P/E ratio data
- `load_yield_data()` → Interest rate data

### Backtest Engine
**Location**: `src/modules/portfolio/backtesting/runner.py`

**Purpose**: Execute strategy backtests with realistic simulation

**Key Function**: `run_backtest(strategy_class, strategy_name, **kwargs)`

### Portfolio Presenter
**Location**: `src/modules/portfolio/presenters/portfolio_presenter.py`

**Purpose**: Coordinate portfolio management operations

**Methods**:
- `load_holdings()` / `save_holdings()` - Persistence
- `get_portfolio_gap_analysis()` - Compare vs strategy
- `balance_portfolio_weights()` - Auto-rebalancing

## 📊 Data Flow Diagram

```
┌─────────────────┐
│  External APIs  │ (akshare, yfinance, manual uploads)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Data Download  │ → Singleton CSV files (data/raw/{type}/)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Data Loader   │ → Normalized DataFrames
└────────┬────────┘
         │
         ├─────────────────────┬──────────────────────┐
         ↓                     ↓                      ↓
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Backtesting │      │   Portfolio  │      │ Visualization│
│    Engine    │      │   Manager    │      │    Charts    │
└──────┬───────┘      └──────┬───────┘      └──────────────┘
       │                     │
       ↓                     ↓
┌──────────────┐      ┌──────────────┐
│ Performance  │      │ Gap Analysis │
│  Analysis    │      │ Rebalancing  │
└──────┬───────┘      └──────────────┘
       │
       ↓
┌──────────────┐
│ Attribution  │
│  Analysis    │
└──────────────┘
```

## 🎯 Common Use Cases

### Use Case 1: Test a New Strategy
```
1. Market Data Download → Ensure data is current
2. Strategy Backtesting → Run historical test
3. Performance Analysis → Review metrics & charts
4. Performance Attribution → Understand return drivers
5. Portfolio Management → Implement if satisfied
```

### Use Case 2: Rebalance Existing Portfolio
```
1. Portfolio Management → Load current holdings
2. Portfolio Management → Compare with strategy target
3. Portfolio Management → Review gap analysis
4. Strategy Backtesting → Test rebalanced allocation (optional)
5. Portfolio Management → Save updated holdings
```

### Use Case 3: Compare Multiple Strategies
```
1. Market Data Download → Ensure data is current
2. Strategy Backtesting → Run all strategies in parallel
3. Performance Analysis → Generate comparison report
4. Performance Attribution → Identify best performers
5. Portfolio Management → Implement winning strategy
```

### Use Case 4: Monthly Portfolio Review
```
1. Market Data Download → Update with latest data
2. Portfolio Management → Check current allocation
3. Portfolio Management → Gap analysis vs target
4. Performance Attribution → Review last month's attribution
5. Portfolio Management → Rebalance if drift > threshold
```

## 🔗 Integration Points

### With Accounting Module
- Portfolio values feed into net worth calculations
- Transaction costs impact accounting records
- Rebalancing events create accounting transactions

### With Data Management Module
- Shares visualization components
- Uses common data loader infrastructure
- Exports reports to shared analytics directory

### External Integrations
- **akshare**: CN market data API
- **yfinance**: US market data API
- **backtrader**: Backtesting engine
- **plotly**: Interactive charts

## 📁 File Organization

```
docs/internal/05-functions-workflows/
├── market-data-download-workflow.md       # Workflow 1
├── strategy-backtesting-workflow.md       # Workflow 2
├── performance-analysis-workflow.md       # Workflow 3
├── performance-attribution-workflow.md    # Workflow 4
├── portfolio-management-workflow.md       # Workflow 5
└── investment-module-overview.md          # This file

analytics/
├── backtests/                # Backtest outputs
│   ├── {strategy}_portfolio_values_*.csv
│   ├── {strategy}_rebalance_log.csv
│   └── {strategy}_performance_report.json
└── performance/              # Performance charts
    └── {strategy}_{metric}_*.html

data/
├── raw/                      # Downloaded market data
│   ├── price/
│   ├── pe/
│   └── yield/
└── holdings.json            # Current portfolio
```

## 🚀 Quick Start

### For Developers
1. Review architecture overview (this file)
2. Read specific workflow documentation as needed
3. Check integration points for cross-module work
4. Follow data flow diagram for debugging

### For Users
1. GUI: Launch Streamlit → **Investment Management** tab
2. CLI: Run backtests via `python src/main.py --mode cli --strategy <name>`
3. API: Use presenters directly for programmatic access

## 📚 Related Documentation

- **User Guide**: `docs/public/built-in-strategy-info.md`
- **Attribution Guide**: `docs/public/performance-attribution-guide.md`
- **Architecture**: `docs/internal/04-architecture-core-modules/`
- **Development Plan**: `docs/internal/06-implementation/`
