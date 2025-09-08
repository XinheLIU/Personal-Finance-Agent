# Test Suite for Personal Finance Agent

This directory contains the comprehensive test suite for the Personal Finance Agent, organized by functional modules to mirror the source code structure.

## Test Organization

The test suite is organized into the following structure:

```
tests/
├── modules/                    # 🧪 Module-specific tests
│   ├── accounting/            # 💰 Accounting module tests
│   │   ├── test_accounting.py              # Core accounting functionality
│   │   ├── test_comparative_analysis.py    # Multi-period comparisons
│   │   └── test_consolidated_reports.py    # Financial statement consolidation
│   │
│   ├── portfolio/            # 📈 Portfolio module tests
│   │   ├── test_backtest.py                # Backtesting engine tests
│   │   ├── test_strategy_utils.py          # Strategy utility functions
│   │   ├── test_strategy_instantiation_fix.py  # Strategy instantiation fixes
│   │   ├── test_performance_attribution.py # Performance attribution analysis
│   │   ├── test_performance_fixes.py       # Performance calculation fixes
│   │   └── test_attribution_scalar_fix.py  # Attribution scalar handling
│   │
│   └── data_management/      # 📊 Data management module tests
│       ├── test_pe_data_download.py        # P/E data download and processing
│       ├── test_analytics_visualization.py # Analytics and visualization
│       ├── test_asset_management.py        # Asset data management
│       └── test_timezone_handling.py       # Timezone handling fixes
│
├── integration/              # 🔗 Cross-module integration tests
│   └── demo_pe_data_flow.py               # End-to-end P/E data workflow
│
├── utils/                    # 🛠️  Utility and common functionality tests
│   └── test_series_boolean_fix.py         # Pandas Series boolean fixes
│
└── logs/                     # 📝 Test execution logs
    └── app.log
```

## Test Categories

### 1. Module Tests (`tests/modules/`)

#### Accounting Tests (`tests/modules/accounting/`)
- **test_accounting.py**: Core accounting functionality including transaction models, income statements, cash flow statements, and balance sheets
- **test_comparative_analysis.py**: Multi-period financial analysis and comparison functionality
- **test_consolidated_reports.py**: Consolidated financial reporting across multiple periods

#### Portfolio Tests (`tests/modules/portfolio/`)
- **test_backtest.py**: Backtesting engine validation for various investment strategies
- **test_strategy_utils.py**: Utility functions for strategy calculations (PE percentiles, yield calculations)
- **test_strategy_instantiation_fix.py**: Strategy class instantiation and registry functionality
- **test_performance_attribution.py**: Performance attribution analysis and sector allocation
- **test_performance_fixes.py**: Performance calculation bug fixes and improvements
- **test_attribution_scalar_fix.py**: Scalar handling in attribution calculations

#### Data Management Tests (`tests/modules/data_management/`)
- **test_pe_data_download.py**: Market P/E ratio data download and processing pipeline
- **test_analytics_visualization.py**: Data visualization and analytics functionality
- **test_asset_management.py**: Asset data loading, management, and validation
- **test_timezone_handling.py**: Timezone-aware data processing and date handling

### 2. Integration Tests (`tests/integration/`)
- **demo_pe_data_flow.py**: End-to-end testing of P/E data workflow from download to analysis

### 3. Utility Tests (`tests/utils/`)
- **test_series_boolean_fix.py**: Common utility fixes for pandas DataFrame and Series operations

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Tests by Module
```bash
# Accounting module tests
pytest tests/modules/accounting/

# Portfolio module tests  
pytest tests/modules/portfolio/

# Data management module tests
pytest tests/modules/data_management/
```

### Run Specific Test Files
```bash
# Run accounting core tests
pytest tests/modules/accounting/test_accounting.py

# Run backtesting tests
pytest tests/modules/portfolio/test_backtest.py

# Run data download tests
pytest tests/modules/data_management/test_pe_data_download.py
```

### Run Specific Test Methods
```bash
# Run specific test method
pytest tests/modules/accounting/test_accounting.py::TestTransactionModel::test_transaction_creation

# Run with verbose output
pytest tests/modules/portfolio/test_strategy_utils.py -v
```

## Test Coverage

The test suite covers:

- ✅ **Core Functionality**: All major features across accounting, portfolio, and data management
- ✅ **Edge Cases**: Boundary conditions and error handling
- ✅ **Integration**: Cross-module interactions and workflows
- ✅ **Bug Fixes**: Regression tests for identified and fixed issues
- ✅ **Performance**: Performance-critical calculations and algorithms

## Adding New Tests

When adding new tests:

1. **Place in appropriate module directory** based on what you're testing
2. **Follow naming convention**: `test_[feature_name].py`
3. **Update imports** to use the modular structure:
   ```python
   from src.modules.accounting.core import Transaction
   from src.modules.portfolio.strategies.registry import StrategyRegistry
   from src.modules.data_management.data_center.data_loader import DataLoader
   ```
4. **Add proper docstrings** explaining what the test validates
5. **Include both positive and negative test cases**

## Test Data

Test data is managed through:
- **Mock data generation** within test files
- **Temporary files** for I/O testing
- **Sample datasets** in `data/` directory for integration tests

This organized test structure ensures comprehensive coverage while maintaining clear separation of concerns and making it easy to identify which tests validate which functionality.