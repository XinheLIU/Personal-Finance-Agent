# Personal Finance Agent - Source Code Structure

This document describes the reorganized source code structure following a modular architecture with three main modules.

## Overview

The Personal Finance Agent is organized into three main functional modules:

1. **Accounting** - Financial bookkeeping and reporting
2. **Portfolio** - Investment strategies and performance analysis  
3. **Data Management** - Data processing, visualization, and analytics

## Directory Structure

```
src/
├── modules/                    # Main functional modules
│   ├── accounting/            # 💰 Financial accounting module
│   │   ├── core/             # Core accounting functionality
│   │   │   ├── models.py     # Data models (Transaction, Asset, etc.)
│   │   │   ├── io.py         # CSV import/export operations
│   │   │   ├── balance_sheet.py
│   │   │   ├── income_statement.py
│   │   │   ├── cash_flow.py
│   │   │   └── ...
│   │   ├── ui/               # User interface components
│   │   │   ├── accounting_management.py
│   │   │   └── enhanced_accounting_page.py
│   │   ├── reports/          # Report generation and templates
│   │   └── utils/            # Utilities and examples
│   │
│   ├── portfolio/            # 📈 Investment portfolio module
│   │   ├── strategies/       # Investment strategy implementations
│   │   │   ├── base.py       # Base strategy classes
│   │   │   ├── registry.py   # Strategy registry
│   │   │   ├── builtin/      # Built-in strategies
│   │   │   └── custom/       # User-defined strategies
│   │   ├── backtesting/      # Backtesting engine and runners
│   │   ├── performance/      # Performance analysis and attribution
│   │   ├── trading/          # Trade execution (future expansion)
│   │   └── investment_management.py  # Main portfolio UI
│   │
│   └── data_management/      # 📊 Data processing and visualization
│       ├── data_center/      # Data loading and processing
│       │   ├── data_loader.py
│       │   ├── download.py
│       │   └── data_processor.py
│       ├── visualization/    # Charts and data visualization
│       │   ├── charts.py
│       │   ├── plotting.py
│       │   └── data_access.py
│       ├── analytics/        # Data analysis tools
│       ├── coordinator.py    # Cross-module coordination
│       └── system_data_management.py  # Data management UI
│
└── ui/                       # 🖥️  Main application interfaces
    ├── streamlit_app.py      # Main Streamlit web application
    ├── main.py               # Command-line main entry point
    ├── cli.py                # Command-line interface
    └── app_logger.py         # Application logging
```

## Module Descriptions

### 1. Accounting Module (`src/modules/accounting/`)

**Purpose**: Complete financial accounting and bookkeeping functionality.

**Key Components**:
- **Core**: Transaction processing, financial statement generation
- **UI**: Streamlit pages for accounting management
- **Reports**: Financial statement templates and export functionality
- **Utils**: Example code and utility functions

**Main Features**:
- Transaction CSV import/export
- Income statement generation
- Balance sheet creation
- Cash flow statement generation
- Multi-period financial analysis

### 2. Portfolio Module (`src/modules/portfolio/`)

**Purpose**: Investment strategy management and portfolio analysis.

**Key Components**:
- **Strategies**: Investment strategy implementations and registry
- **Backtesting**: Historical performance testing engine
- **Performance**: Performance metrics and attribution analysis
- **Trading**: Trade execution framework (extensible)

**Main Features**:
- Built-in investment strategies (60/40, All Weather, etc.)
- Custom strategy creation
- Historical backtesting
- Performance attribution analysis
- Risk metrics calculation

### 3. Data Management Module (`src/modules/data_management/`)

**Purpose**: Data processing, visualization, and cross-module coordination.

**Key Components**:
- **Data Center**: Market data downloading and processing
- **Visualization**: Chart generation and interactive displays
- **Analytics**: Data analysis and transparency tools
- **Coordinator**: System-wide coordination and orchestration

**Main Features**:
- Market data download from multiple sources
- Interactive data visualization
- System coordination between modules
- Data processing and caching

## Import Structure

The new modular structure uses clear import paths:

```python
# Accounting imports
from src.modules.accounting.core import Transaction, CategoryMapper
from src.modules.accounting.core.balance_sheet import generate_balance_sheet

# Portfolio imports  
from src.modules.portfolio.strategies.registry import StrategyRegistry
from src.modules.portfolio.backtesting.runner import run_backtest

# Data management imports
from src.modules.data_management.data_center.data_loader import DataLoader
from src.modules.data_management.visualization.charts import display_data_explorer

# UI imports
from src.ui.app_logger import LOG
```

## Benefits of This Structure

1. **Clear Separation of Concerns**: Each module has a specific responsibility
2. **Improved Maintainability**: Related functionality is grouped together
3. **Better Scalability**: New features can be added to appropriate modules
4. **Enhanced Testing**: Modules can be tested independently
5. **Easier Navigation**: Developers can quickly find relevant code
6. **Modular Development**: Teams can work on different modules simultaneously

## Migration Notes

- All import statements have been updated to reflect the new structure
- Orphaned files like `enhanced_accounting_page.py` have been moved to appropriate locations
- Old empty directories have been removed
- All `__init__.py` files have been created with proper module exports

## Running the Application

The main entry points remain the same:

```bash
# Web interface
streamlit run src/ui/streamlit_app.py

# Command line interface  
python src/ui/main.py --help
python src/ui/cli.py --help
```

This structure provides a solid foundation for continued development and feature expansion.
