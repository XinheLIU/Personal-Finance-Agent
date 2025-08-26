# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2025-08-23 (personal-accountant branch)

### Added - Professional Accounting Module

- **Complete Accounting System**: CSV-based transaction management and financial statement generation with Chinese language support
- **Data Models**: Transaction/Asset models with decimal precision and comprehensive validation
- **Income Statement Engine**: Monthly/YTD statements with revenue/expense categorization and CNY tax calculations (0%, 10%, 20%)
- **CLI Integration**: `accounting-status` and `generate-income-statement` commands
- **Web Interface**: Dedicated "💰 Accounting" tab in Streamlit with data management and interactive statement generation
- **TDD Implementation**: 104 passing tests (44 data model, 39 I/O, 21 income statement tests)

### Files Added
- `src/accounting/` - Complete accounting module (models, I/O, income statement engine)
- `data/accounting/` - Data directory with sample transactions and statements export folder

### Files Modified
- `src/cli.py`, `src/streamlit_app.py` - Added accounting commands and web interface
- `README.md` - Updated with accounting documentation

## [0.3.7] - 2025-08-15

### Added
- **Standalone Performance Attribution System**: Independent attribution analysis with dedicated "📊 Attribution" tab
- **Sector-Based Attribution**: Brinson methodology with allocation, selection, and interaction effects across 9 professional sectors
- **Enhanced Visualizations**: Waterfall charts, sector comparisons, time series attribution, and export capabilities
- **Flexible Period Selection**: Presets and custom date ranges with daily/weekly/monthly frequency options

### Files Added
- `config/sectors.py` - Professional sector classification
- `src/performance/sector_attribution.py` - Brinson attribution engine
- Enhanced `src/visualization/charts.py` and `src/streamlit_app.py`

## Bug Fix - 2025-08-15

### Fixed
- **Timezone Handling**: Fixed timezone comparison errors preventing yfinance CSV data loading
- **Attribution Analysis**: Fixed data alignment issues and added weights evolution tracking to FixedWeightStrategy
- **Asset Loading**: TIP, IEF, SHY and other timezone-aware assets now load correctly

### Added
- `test_timezone_handling.py` with comprehensive timezone test coverage
- Enhanced strategy attribution support with daily weights tracking

## [0.3.5] - 2025-08-15

### Changed
- **Simplified Data Storage**: Restructured from complex multi-file naming to singleton files per asset-datatype
  - Old: `SP500_20040102_to_20250731.csv` → New: `SP500_price.csv`
  - Smart data merging preserves historical data while updating

### Fixed
- **Data Loading**: Resolved "Missing 'close' column" and column format issues
- **Frontend Integration**: Successfully loads 23 datasets with clean singleton files

### Added
- **Manual PE Data Workflow**: `data/raw/pe/manual/` folder with `--process-manual-pe` command
- **Performance**: Significantly improved data loading speed

## [0.3.4] - 2025-08-14

### Added
- **Performance Attribution Analysis**: Institutional-grade system with daily/weekly/monthly attribution
- **GUI/CLI Integration**: Attribution toggle, interactive charts, export capabilities, and CLI commands
- **Core Attribution Module**: `PerformanceAttributor` class with Brinson model and T+1 execution lag
- **Data Pipeline Helpers**: Processed-data helpers and merge-and-save functionality

### Changed
- **Documentation Overhaul**: Updated system architecture, data sources, and README
- **Module Organization**: Moved `legacy.py` to `classic.py`, strategies use processed-only data
- **Data Processing**: Centralized fallback logic, improved data merging

### Files Added/Modified
- Added: `src/performance/attribution.py`, `src/strategies/classic.py`
- Enhanced: Backtesting engine, visualization system, CLI/GUI interfaces

## Data Pipeline Refactor - 2025-08-12

### Changed
- **Data Separation**: Raw data in `/data/raw/`, processed in `/data/processed/<strategy_name>/`
- **DataProcessor**: Strategy-specific datasets with caching and metadata
- **CLI Commands**: Added `--process-data` and `--show-processing-status`
- **Performance**: Faster, memory-efficient loading with improved error handling

### Files Added/Modified
- Added: `src/data_center/data_processor.py`
- Updated: Download, strategies, management modules

## [0.3.3] - 2025-08-11

### Added
- **Tab-Based Navigation**: Horizontal tabs replacing sidebar dropdown for better UX
- **Enhanced Data Visualization**: Normalized asset comparison, multi-asset analysis, performance statistics
- **New Visualization Types**: Normalized comparison, time series, percentage returns, data quality checks
- **Visual Improvements**: Extended color palette, professional styling, responsive design

### Files Modified
- `src/streamlit_app.py`, `src/visualization/plotting.py`, `src/visualization/charts.py`

## [0.3.2] - 2025-08-11

### Major System Architecture Transformation
Complete transformation to professional-grade quantitative investment management system.

### Added - 6-Module Professional Architecture
- **Data Center** (`src/data_center/`): Market data management with raw/processed separation
- **Strategy Module** (`src/strategies/`): Professional repository with metadata system
- **Backtesting Platform** (`src/backtesting/`): T+1 execution lag and transaction cost modeling
- **Performance Analysis** (`src/performance/`): Institutional-grade analytics and attribution
- **Management Module** (`src/management/`): System coordination and health monitoring
- **Trading Module** (`src/trading/`): Order execution framework (sim/paper/live)

### New Directory Structure
- `src/` - Core system modules
- `config/` - Centralized configuration (`assets.py`, `system.py`)
- `data/raw/`, `data/processed/`, `data/accounts/` - Organized data storage
- `analytics/backtests/`, `analytics/performance/` - Analysis outputs

### Professional Features
- Execution lag modeling, system health monitoring, professional CLI
- Enhanced data validation, strategy metadata, performance attribution

### Breaking Changes
- Configuration moved to `config/` directory
- New CLI command structure with system management
- All modules reorganized under `src/` following standard layout

## [0.3.1] - 2025-08-07

### Added
- **Modular Strategy Architecture**: Base classes, inheritance, and StrategyRegistry
- **Built-in Strategies**: Static (60/40, Permanent Portfolio, All Weather, etc.) and Dynamic (PE-based, Momentum, Risk Parity)
- **CLI Module**: `src/cli.py` with comprehensive command-line interface
- **GUI Enhancements**: Dynamic strategy selection, custom strategy creation, data management

### Files Added/Modified
- Added: `src/strategies/` directory, `src/cli.py`
- Modified: `src/main.py`, `src/gui.py`, `src/strategy.py`

## [0.3.0] - 2025-08-07

### Added
- **Built-in Portfolio Strategies**: 60/40, Permanent Portfolio, All-Weather, David Swensen portfolios
- **Custom Strategy Builder**: GUI tab for user-defined fixed-weight strategies
- **CLI Mode**: Command-line backtesting without GUI
- **GUI Features**: Strategy details, gap analysis, backtest start date selection, data management

### Changed
- **Architecture**: `main.py` as central entry point for GUI/CLI modes
- **Strategy Implementation**: Common `FixedWeightStrategy` base class
- **Testing**: Merged test directories, added backtest tests

## [0.2.1] - 2025-01-30

### Added
- **Manual P/E Data Integration**: Support for user-downloaded P/E files (HSI, HSTECH, S&P 500, NASDAQ 100)
- **P/E Data Fill-to-Recent**: Automatic gap filling using Yahoo Finance and price-based fallbacks
- **HSI Asset Support**: Added Hang Seng Index for better Hong Kong market coverage
- **P/E Test Suite**: Comprehensive testing in `src/test/`

### Changed
- **P/E Data Architecture**: Replaced inferred ratios with actual historical P/E data
- **Strategy Mix**: Updated to CSI300 (15%), CSI500 (15%), HSI (10%), HSTECH (10%)

## [0.2.0] - 2025-07-31

### Added
- **Gradio GUI**: New graphical interface with backtesting, portfolio, and analytics tabs
- **Holdings Management**: Portfolio tracking in `data/holdings.json`
- **Analytics Module**: CSV reports and rebalancing logs in `/analytics` directory
- **FRED API**: US Treasury yield data with yfinance fallback
- **Enhanced PE Data**: ETF-based collection (SPY, QQQ, FXI) for accuracy

### Changed
- **Data Storage**: Segregated price/PE/yield data, standardized file naming
- **Decoupled Logic**: Refactored weight calculation for standalone GUI use

## [0.2.2] - 2025-08-10

### Fixed
- **Critical Bugs**: Metaclass conflicts, missing dependencies, import errors
- **NaN Handling**: Robust portfolio value processing with numpy
- **File Operations**: Directory creation and filename sanitization

### Added
- **FixedWeightStrategy**: Base class for custom fixed-weight allocations
- **Error Handling**: Comprehensive validation and file operations

## [0.1.0] - 2025-07-22

### Added
- **Project Structure**: `src/` and `tests/` directories with modular organization
- **Unit Testing**: Framework with strategy calculation tests
- **Configuration**: Centralized config in `src/config.py`
- **Core Modules**: Data loading, backtesting, reporting, strategy utilities

### Changed
- **Code Quality**: Replaced hardcoded values, improved error handling, absolute imports