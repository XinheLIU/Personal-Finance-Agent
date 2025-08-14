# CLAUDE.md - Quant Investment System

This file provides guidance to Claude Code (claude.ai/code) when working with this professional quantitative investment management system.

## 🏗️ System Architecture

This system follows the **industry-standard 6-module quant investment architecture** used by professional asset management firms:

### Core Modules

1. **📊 Data Center** (`modules/data_center/`): Market data management with raw/processed separation
2. **🎯 Strategy Module** (`modules/strategies/`): Professional strategy repository with metadata system
3. **🔬 Backtesting Platform** (`modules/backtesting/`): Historical testing with execution lag modeling
4. **📈 Performance Analysis** (`modules/performance/`): Comprehensive analytics and attribution
5. **⚙️ Management Module** (`modules/management/`): System coordination and orchestration  
6. **💼 Trading Module** (`modules/trading/`): Order execution framework (sim/paper/live)

### Professional Features
- **Execution Lag Modeling**: Realistic T+1 execution delays
- **Transaction Cost Analysis**: Commission and slippage modeling
- **Performance Attribution**: Factor and sector-based analysis
- **System Health Monitoring**: Real-time diagnostics and status
- **Strategy Metadata**: Complete documentation and parameter tracking

## 🚀 Quick Start Commands

### System Management
```bash
# System validation and health
python -m src.main --validate                    # Validate configuration
python -m src.main --mode system --status        # System health check
python -m src.main --mode system --startup       # Initialize system

# Data management
python -m src.main --download-data               # Download market data
python -m src.main --download-data --refresh     # Force refresh all data
```

### User Interfaces
```bash
# Web GUI (recommended)
python -m src.main                              # Launch web interface (default)
python -m src.main --mode gui                   # Explicit GUI mode

# Command line interfaces  
python -m src.main --mode cli                   # Interactive CLI
python -m src.main --list-strategies            # List available strategies
python -m src.main --strategy-details "Dynamic Allocation"  # Strategy info

# Development and debugging
python -m src.main --debug --validate           # Debug mode validation
```

### Professional Testing
```bash
# Run comprehensive tests
python -m pytest tests/ -v                      # Full test suite
python -m tests.test_pe_data_download           # PE data tests
python -m tests.test_strategy_utils             # Strategy utilities tests
```

## 📁 New Directory Structure

```
modules/                    # Professional system modules
├── data_center/           # Market data management
├── strategies/            # Strategy repository with metadata
├── backtesting/           # Professional testing platform  
├── performance/           # Analytics and reporting
├── management/            # System coordination
└── trading/               # Order execution framework

config/                    # System configuration
├── assets.py             # Asset definitions and mappings  
└── system.py             # Core parameters and settings

data/                     # Market data (separated by processing stage)
├── raw/                  # Unprocessed data from sources
│   ├── price/           # Historical price data
│   ├── pe/              # P/E ratio data
│   └── yield/           # Interest rate data
├── processed/           # Clean, normalized data
└── accounts/            # Portfolio holdings and transactions

analytics/               # Generated analysis and reports
├── backtests/          # Detailed backtest results  
└── performance/        # Performance reports and charts
```

## 🎯 Strategy Development Workflow

### Adding New Strategy (Professional Process)
```python
# 1. Create strategy class in modules/strategies/custom/
from modules.strategies.base import StaticAllocationStrategy
from modules.strategies.metadata import StrategyMetadata

class MyStrategy(StaticAllocationStrategy):
    def get_target_weights(self) -> Dict[str, float]:
        return {
            'SP500': 0.60,
            'TLT': 0.40
        }
    
    def get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="My Strategy",
            strategy_id="my_strategy", 
            category="static",
            description="Custom 60/40 portfolio"
        )

# 2. Register strategy in modules/strategies/registry.py
# 3. Test with: python -m src.main --strategy "My Strategy"
```

### Professional Data Management
- **Raw Data**: `data/raw/` - Unprocessed downloads from akshare/yfinance
- **Processed Data**: `data/processed/` - Clean, normalized, validated data
- **Manual PE Data**: Place files in `data/raw/pe/` (HSI, SPX, NASDAQ formats)
- **Auto-validation**: System validates data quality and completeness

## 🔧 Key Configuration Files

### Asset Configuration (`config/assets.py`)
```python
# TRADABLE_ASSETS: Actual ETFs/funds for trading
# INDEX_ASSETS: Underlying indices for analysis
# PE_ASSETS: P/E ratio data sources
# YIELD_ASSETS: Interest rate data sources
```

### System Configuration (`config/system.py`)
```python  
# Core parameters: capital, commission, risk limits
# Performance settings: lookback periods, rolling windows
# System settings: logging, cache, refresh intervals
```

## 📊 Professional Components

### Enhanced Data Loader (`modules/data_center/data_loader.py`)
- **Validation**: Comprehensive data quality checks
- **Normalization**: Price series normalization for returns
- **Error Handling**: Graceful fallbacks and detailed logging
- **Performance**: Efficient caching and batch processing

### Backtesting Engine (`modules/backtesting/engine.py`)
- **Execution Lag**: T+1 execution delay modeling
- **Transaction Costs**: Commission and slippage simulation
- **Analytics**: Comprehensive performance metrics
- **Logging**: Detailed execution and rebalancing logs

### System Coordinator (`modules/management/coordinator.py`)
- **Health Monitoring**: Real-time system diagnostics
- **Strategy Management**: Registration, execution, monitoring
- **Error Recovery**: Automatic error handling and reporting
- **State Management**: System startup/shutdown orchestration

## 🔍 Development Patterns

### Import Structure (Post-Refactoring)
```python
# Configuration
from config.assets import TRADABLE_ASSETS, PE_ASSETS
from config.system import INITIAL_CAPITAL, COMMISSION

# Core modules
from modules.data_center.data_loader import DataLoader
from modules.backtesting.engine import EnhancedBacktestEngine
from modules.strategies.base import StaticAllocationStrategy
from modules.performance.analytics import PerformanceAnalyzer
```

### Data Access Patterns
```python
# Professional data loading with validation
data_loader = DataLoader()
market_data = data_loader.load_market_data(normalize=True)
pe_data = data_loader.load_pe_data()
```

### Error Handling Best Practices
```python
# Graceful degradation with detailed logging
try:
    result = professional_operation()
except Exception as e:
    LOG.error(f"Operation failed: {e}")
    return fallback_result()
```

## ⚠️ Important Notes for Claude Code

1. **Environment**: Use conda env `py-fin` for all Python operations
2. **Architecture**: Follow the 6-module professional structure
3. **Data Integrity**: Always validate data before processing
4. **Error Handling**: Implement graceful fallbacks with logging
5. **Testing**: Run system validation before major changes
6. **Documentation**: Update @README.md and @CHANGELOG.md after changes
7. **System Health**: Check `python -m src.main --mode system --status` for issues

## 🔄 Common Workflows

### Development Cycle
1. Validate system: `python -m src.main --validate`
2. Check system health: `python -m src.main --mode system --status`  
3. Make changes following module architecture
4. Test changes: Run relevant test suite
5. Update documentation if needed

### Data Management
1. Download/refresh data: `python -m src.main --download-data --refresh`
2. Validate data quality via system status
3. Process data through enhanced pipeline
4. Monitor system health for data issues
- use Claude.md as your scratchpad and memory for big and long changes (you can create plans and checklists there)