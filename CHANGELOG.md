# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Bug Fix - 2025-08-15

### Fixed

- **Critical Timezone Handling Bug**: Fixed timezone comparison errors that prevented loading of yfinance CSV data
  - **Root Cause**: CSV files from yfinance contain timezone-aware timestamps (`2003-12-05 00:00:00-05:00`) but data loader had inconsistent timezone handling
  - **Error**: "Cannot compare tz-naive and tz-aware timestamps" when filtering data with start_date
  - **Solution**: Enhanced datetime parsing with `format='mixed'` and `utc=True`, then convert to timezone-naive for consistent comparisons
  - **Assets Fixed**: TIP, IEF, SHY (and any other assets with timezone-aware CSV data) now load successfully
  - **Impact**: Permanent Portfolio and other strategies using these assets now work correctly

- **Performance Attribution Analysis Issues**: Fixed data alignment problems preventing attribution analysis
  - **Root Cause**: Date format inconsistencies between portfolio data (date-only) and asset returns (datetime with timezone)
  - **Missing Functionality**: `FixedWeightStrategy` (used by SixtyForty, Permanent Portfolio, etc.) lacked weights evolution tracking
  - **Solution**: Comprehensive date normalization and enhanced strategy base classes with proper attribution support
  - **Result**: Attribution analysis now works correctly with 1,000+ daily records generated for comprehensive performance analysis

### Added

- **Comprehensive Timezone Test Suite**: Created `test_timezone_handling.py` with 5 test cases covering:
  - Timezone-aware data feed loading
  - Mixed timezone format handling (EST, PST, UTC, naive)
  - Real-world yfinance CSV format testing
  - Start date filtering with timezone data
  - Market data loading with timezone data
- **Enhanced Strategy Attribution Support**: Added weights evolution tracking and rebalancing logs to `FixedWeightStrategy`
  - **Features**: Daily weights tracking, rebalancing event logging, attribution-ready data structures
  - **Strategies Enhanced**: SixtyForty, Permanent Portfolio, All Weather, David Swensen strategies now support full attribution analysis
- **Improved Error Detection**: Tests now catch timezone-related data loading issues that were previously missed

## [0.3.5] - 2025-08-15

### Changed

- **Simplified Data Storage Architecture**: Completely restructured data storage from complex multi-file naming to singleton file strategy
  - **Old**: Multiple files per asset like `SP500_20040102_to_20250731.csv`, `SP500_price_20100909_to_20250814.csv`
  - **New**: Single file per asset-datatype like `SP500_price.csv`, `CSI300_pe.csv`, `US10Y_yield.csv`
  - Implemented smart data merging that preserves historical data while updating with new downloads
  - Automated migration system that consolidated existing files into singleton format
  - Enhanced data loader with fallback support for both singleton and legacy file naming

### Fixed

- **Data Loading Errors**: Resolved "Missing 'close' column" and "No valid data after cleaning" errors
  - Fixed case-sensitive column name handling (Close vs close)
  - Added support for mixed column formats (English vs Chinese)
  - Enhanced timezone handling for datetime columns
  - Improved yield data column detection and normalization
- **Frontend Data Integration**: Updated Streamlit app to use singleton data files
  - **Before**: Loading errors and empty datasets due to complex file naming
  - **After**: Successfully loads 23 datasets (17 price + 6 PE data) with clean singleton files
  - Eliminated "No valid data after cleaning" warnings for all assets
  - Enhanced data visualization pipeline with proper column mapping

### Added

- **Manual PE Data Workflow**: New dedicated folder and processing system for manual PE data updates
  - Created `data/raw/pe/manual/` subfolder for user-provided PE data files
  - Added `--process-manual-pe` command line option for processing manual files
  - Automated validation, cleaning, and merging of manual PE data with existing data
  - Comprehensive documentation and README files for user guidance
  - Smart data integration prioritizing manual data over automated sources
  - Support for multiple PE column formats (pe_ratio, pe, PE, PE_ratio)

### Performance

- **Data Loading Speed**: Significantly improved data loading performance
  - Reduced file system overhead by eliminating complex file pattern matching
  - Faster data merging with optimized deduplication logic
  - Streamlined frontend data pipeline with direct singleton file access

## [0.3.4] - 2025-08-14

### Added

- **Professional Performance Attribution Analysis**: Institutional-grade attribution system that decomposes portfolio returns into asset-level contributions and rebalancing effects
  - Daily, weekly, and monthly attribution analysis with compound return calculations
  - Asset contribution tracking showing how each individual asset contributed to portfolio performance
  - Rebalancing impact analysis measuring the effect of portfolio rebalancing activities
  - Interactive web interface with attribution charts, tables, and export capabilities
  - Command-line interface with `--attribution`, `--attribution-period`, and `--export-attribution` options
  - Automated data export to CSV and Excel files in `/analytics/attribution/` directory
  - Attribution accuracy reconciliation and validation metrics
  - Time series visualization of attribution components over selected periods

- **Enhanced GUI Attribution Features**:
  - Attribution toggle checkbox in backtest interface
  - Interactive period selection (daily/weekly/monthly)
  - Stacked bar charts showing asset vs rebalancing contributions
  - Asset-level analysis tables with contribution breakdown
  - Time series charts of attribution components
  - CSV/Excel download capabilities directly from web interface

- **Enhanced CLI Attribution Commands**:
  - `python -m src.main --attribution "Strategy Name" --attribution-period weekly`
  - `python -m src.main --export-attribution "Strategy Name"`
  - `python -m src.cli attribution "Strategy Name" --period monthly`
  - Top contributors analysis and summary statistics in terminal output

- **Core Attribution Module** (`src/performance/attribution.py`):
  - `PerformanceAttributor` class implementing professional attribution methodology
  - Brinson attribution model with T+1 execution lag modeling
  - Daily attribution calculation with asset and weight change decomposition
  - Weekly and monthly attribution aggregation with compound return handling
  - Comprehensive attribution reporting and data export functionality

- Processed-data helpers in `src/strategies/utils.py`: `pe_percentile_from_processed`, `yield_percentile_from_processed`, `current_yield_from_processed`.
- Merge-and-save helper in `src/data_center/download.py`: `_merge_with_existing_and_save()` used for price, PE, and yield downloads.

### Changed

- **Comprehensive Documentation Overhaul**: Aligned all key documentation with the current state of the codebase to ensure accuracy and consistency.
- **Updated System Architecture Document**: Completely revamped `docs/04-development/personal-finance-system-architecture.md` with:
    - A new Mermaid diagram that directly maps to the `src/` directory structure.
    - Revised module descriptions to reflect their actual implementation and key classes (`EnhancedBacktestEngine`, `SystemCoordinator`, etc.).
    - Replaced all outdated and simplistic code snippets with new samples that accurately represent the current, more sophisticated implementation (e.g., using `backtrader`, `akshare`, and the class-based module structure).
- **Corrected Data Source Information**: Updated `docs/04-development/data-sources.md` to remove all references to the obsolete `Tushare` library and accurately describe the roles of `akshare`, `yfinance`, and manual data files.
- **Improved README**: Updated the main `README.md` with the corrected module descriptions and clearer, more accurate usage instructions for running the CLI and GUI.
- Rebalancing logs now save to a single file per strategy (overwritten each run) in `analytics/backtests/` using lower_snake_case: `{strategy}_rebalance_log.csv`.
- Strategies consume only processed data; all fallback/format logic centralized in the data processing layer. Dynamic allocation strategy refactored to processed-only inputs.
- Module naming: active code moved from `src/strategies/legacy.py` to `src/strategies/classic.py`; `legacy.py` retained as a thin compatibility shim.
- Downloaded data now preserves historical coverage by merging with existing files before saving; consolidated outputs span the full merged date range.

### Enhanced

- **Backtesting Engine**: Enhanced to capture attribution-ready data including asset returns, portfolio weights evolution, and rebalancing activities
- **Data Pipeline**: Improved data capture for attribution analysis with asset-level return tracking
- **Visualization System**: New attribution-specific charts and interactive visualizations in web interface
- **Documentation**: Comprehensive attribution analysis documentation with professional use cases and examples

### Files Modified/Added

- Added: `src/performance/attribution.py` (core attribution analysis system)
- Added: `src/strategies/classic.py`
- Modified: `src/backtesting/engine.py`, `src/backtesting/runner.py` (attribution data capture)
- Modified: `src/streamlit_app.py` (GUI attribution integration)
- Modified: `src/visualization/charts.py` (attribution visualization functions)
- Modified: `src/cli.py`, `src/main.py` (CLI attribution commands)
- Modified: `src/strategies/builtin/dynamic_strategies.py`, `src/strategies/utils.py`, `src/data_center/download.py`, `tests/test_backtest.py`
- Modified: `docs/04-development/personal-finance-system-architecture.md`
- Modified: `docs/04-development/data-sources.md`
- Modified: `README.md` (comprehensive attribution documentation)
- Modified: `CHANGELOG.md`
- Enhanced: Attribution data automatically saved to `/analytics/attribution/` directory
- Deprecated (shim): `src/strategies/legacy.py` now re-exports from `classic`

## Data Model & Processing Pipeline Refactor - 2025-08-12

- Separated raw and processed data; removed duplicate directories.
- Added strategy-specific processed datasets and automated processing after downloads.
- Introduced `DataProcessor` for merging price, PE, and yield data per strategy with caching and metadata.
- CLI: new `--process-data` and `--show-processing-status` commands; auto-processing on download.
- Strategies now use processed data (with raw fallback); improved loading speed and memory use.
- System health checks now include data processing; better error handling and freshness tracking.

**Files Added/Modified:**  
- `src/data_center/data_processor.py` (new pipeline)  
- Updated: `src/data_center/download.py`, `src/strategies/builtin/dynamic_strategies.py`, `src/strategies/legacy.py`, `src/main.py`, `src/management/coordinator.py`, `README.md`, `CHANGELOG.md`

**Data Structure:**  
- All raw data in `/data/raw/`
- Processed data in `/data/processed/<strategy_name>/` (tailored per strategy)
- Metadata saved with processed data

**Performance:**  
- Faster, memory-efficient data loading
- Transparent processing status

**Compliance:**  
- Institutional pipeline, strategy-level optimization, full lineage, robust error handling, and monitoring

## [0.3.3] - 2025-08-11

### GUI Navigation & Multi-Asset Visualization Enhancements

This release improves the Streamlit web interface with enhanced navigation and advanced multi-asset comparison capabilities.

#### 🌐 Navigation Improvements
- **Tab-Based Navigation**: Replaced sidebar dropdown with horizontal tab interface for all four main sections
- **Direct Access**: Users can now click directly on any tab (Backtest, Portfolio, Data Explorer, System) instead of using dropdown
- **Better UX**: More intuitive navigation with all options visible at once

#### 📊 Enhanced Data Visualization
- **Normalized Asset Comparison**: New visualization option to plot all selected assets starting at base value of 100
- **Multi-Asset Performance Analysis**: Enhanced comparison charts with improved color palette and legend positioning  
- **Performance Summary Statistics**: Automatic calculation of total returns, final values, and annualized volatility
- **Flexible Normalization**: Support for both normalized (base=100) and percentage return comparisons

#### 🔍 Data Explorer Enhancements
- **New Visualization Types**:
  - "Normalized Comparison (Start at 100)" - Primary option for easy asset comparison
  - "Individual Time Series" - Traditional single-asset view
  - "Percentage Returns Comparison" - Classic percentage return analysis
  - "Data Quality Check" - Enhanced data validation visualization
- **Interactive Statistics**: Expandable performance summary with key metrics
- **Enhanced Tooltips**: Improved hover information with asset names, dates, and values

#### 🎨 Visual Improvements
- **Extended Color Palette**: Support for up to 12 distinct colors for multiple assets
- **Better Legend Layout**: Right-side positioning for improved readability
- **Professional Styling**: Enhanced chart appearance with clean templates
- **Responsive Design**: Better container width utilization

### Files Modified
- `src/streamlit_app.py` - Converted navigation from sidebar dropdown to horizontal tabs
- `src/visualization/plotting.py` - Enhanced multi-asset comparison with normalization options
- `src/visualization/charts.py` - Added new visualization types and performance statistics

### Technical Improvements
- **Normalization Algorithm**: Robust asset comparison with common baseline at 100
- **Statistical Analysis**: Automatic volatility and return calculations  
- **Color Management**: Extended palette for better visual distinction
- **Error Handling**: Improved data validation and missing data handling

### User Experience
- **Faster Navigation**: One-click access to all main sections
- **Better Asset Comparison**: Easy visual comparison of multiple assets on common scale
- **Professional Analytics**: Institutional-grade performance metrics and visualization
- **Intuitive Interface**: More accessible and user-friendly design

## [0.3.2] - 2025-08-11

### Major System Architecture Transformation

This release represents a complete transformation from a backtesting framework to a **professional-grade quantitative investment management system** following industry-standard architecture patterns used by asset management firms.

#### 🏗️ Professional 6-Module Architecture Implementation
- **📊 Data Center Module** (`src/data_center/`): Comprehensive market data management with raw/processed separation
- **🎯 Strategy Module** (`src/strategies/`): Professional strategy repository with metadata and documentation system
- **🔬 Backtesting Platform** (`src/backtesting/`): Advanced testing with execution lag modeling and transaction cost analysis
- **📈 Performance Analysis** (`src/performance/`): Institutional-grade analytics with attribution analysis and risk metrics
- **⚙️ Management Module** (`src/management/`): Central system coordination with health monitoring and orchestration
- **💼 Trading Module** (`src/trading/`): Order execution framework supporting simulation, paper trading, and live trading modes

#### 🚀 Professional Features Added
- **Execution Lag Modeling**: Realistic T+1 execution delays for accurate backtesting
- **Transaction Cost Analysis**: Comprehensive commission and slippage modeling
- **System Health Monitoring**: Real-time diagnostics and module status reporting
- **Performance Attribution**: Factor and sector-based performance analysis
- **Strategy Metadata System**: Complete documentation and parameter tracking
- **Enhanced Data Validation**: Comprehensive data quality checks and normalization
- **Professional CLI**: System management commands with validation and status monitoring

#### 📁 New Directory Structure
- **`src/`**: Core system modules following institutional architecture pattern
- **`config/`**: Centralized configuration management (`assets.py`, `system.py`)
- **`data/raw/`**: Unprocessed market data from sources (price/, pe/, yield/)
- **`data/processed/`**: Clean, normalized, validated data
- **`data/accounts/`**: Portfolio holdings and transaction records
- **`analytics/backtests/`**: Detailed backtest results and analysis
- **`analytics/performance/`**: Performance reports and charts
- **`docs/`**: Documentation and research materials
- **`notebooks/`**: Analysis and debugging notebooks

#### ⚙️ Enhanced Data Management
- **Raw/Processed Separation**: Professional data pipeline with quality validation
- **Enhanced Data Loader**: Comprehensive validation, normalization, and error handling
- **Data Processor**: Advanced normalization and statistical analysis capabilities
- **Multi-source Integration**: Robust akshare and yfinance integration with fallbacks

#### 🔧 System Management & Operations
- **System Coordinator**: Central orchestration with startup/shutdown management
- **Health Diagnostics**: Comprehensive system health checks and module monitoring
- **Professional CLI**: `python -m src.main --validate`, `--mode system --status`
- **Error Recovery**: Automatic error handling and graceful degradation
- **State Management**: System state persistence and recovery

#### 📊 Advanced Analytics & Reporting
- **Professional Performance Metrics**: Sharpe ratio, Calmar ratio, VaR calculations
- **Attribution Analysis**: Sector and factor-based performance breakdown
- **Risk Management**: Drawdown analysis and position limits
- **Enhanced Reporting**: Comprehensive CSV reports and interactive charts
- **Rolling Analysis**: Multi-timeframe performance evaluation

#### 🌐 Updated User Interfaces
- **Enhanced Main Entry Point**: Professional CLI with system management commands
- **System Validation**: `--validate` command for configuration verification
- **Status Monitoring**: `--mode system --status` for health checks
- **Debug Mode**: Enhanced debugging capabilities with detailed logging

### Files Added
- `src/data_center/data_loader.py` - Enhanced data loading with validation
- `src/data_center/data_processor.py` - Data normalization and analytics
- `src/data_center/download.py` - Data acquisition and updates
- `src/strategies/metadata.py` - Strategy documentation system
- `src/strategies/registry.py` - Strategy management and discovery
- `src/strategies/utils.py` - Strategy utilities and helpers
- `src/backtesting/engine.py` - Professional backtesting with execution lag
- `src/backtesting/runner.py` - Backtest orchestration
- `src/performance/analytics.py` - Comprehensive performance analysis
- `src/management/coordinator.py` - System coordination and health monitoring
- `src/trading/executor.py` - Order execution framework
- `config/assets.py` - Asset definitions (moved and enhanced from `src/config.py`)
- `config/system.py` - System parameters and settings
- `docs/` - Comprehensive documentation directory
- `notebooks/` - Analysis and debugging notebooks

### Files Modified
- `src/main.py` - Complete rewrite with professional CLI and system management
- `src/data_loader.py` - Updated to use new data center module
- `README.md` - Updated with professional system documentation
- `CLAUDE.md` - Comprehensive developer guidance for new architecture

### Breaking Changes
- **Import Structure**: Configuration imports moved to `config/` directory
- **Module Structure**: Core functionality reorganized within `src/` with modular architecture
- **Data Organization**: Data separated into `data/raw/`, `data/processed/`, and `data/accounts/`
- **CLI Interface**: New command structure with professional system management capabilities
- **File Structure**: All modules now under `src/` following standard Python project layout

### Migration Guide
1. **Update imports**: `from config.assets import TRADABLE_ASSETS`
2. **Use new CLI commands**: 
   - `python -m src.main --validate` for system validation
   - `python -m src.main --mode system --status` for health checks
3. **Data structure**: Manual PE files now go in `data/raw/pe/`
4. **Strategy development**: Use new base classes in `src/strategies/base.py`
5. **Configuration**: Update settings in `config/assets.py` and `config/system.py`

### Professional Standards Compliance
- ✅ Industry-standard 6-module architecture
- ✅ Institutional-grade data management
- ✅ Professional error handling and logging
- ✅ Comprehensive system monitoring
- ✅ Production-ready configuration management
- ✅ Enterprise-level testing and validation

## [0.3.1] - 2025-08-07

### Major Architecture Refactoring

#### Strategy Framework Overhaul
- **Created modular strategy architecture** with base classes and inheritance
- **Added `src/strategies/` directory structure** with base classes, built-in strategies, and custom strategy support
- **Added StrategyRegistry**: Centralized strategy management system

#### Built-in Strategies Added
- **Static Allocation Strategies**: 60/40, Permanent Portfolio, All Weather, David Swensen, Buy & Hold, Equal Weight
- **Dynamic Strategies**: PE-based Dynamic Allocation, Momentum, Risk Parity

#### Command Line Interface
- **New CLI module**: `src/cli.py` with comprehensive command-line interface
- **Command options**: list strategies, run specific strategy, download data, show weights

#### GUI Enhancements
- **Dynamic strategy selection** from registry
- **Custom strategy creation** tab for user-defined strategies
- **Data management** and gap analysis features
- **Real-time strategy details** display

#### User Strategy Creation
- **StrategyBuilder utility** with JSON-based storage
- **GUI interface** for interactive weight assignment
- **Real-time backtesting** of custom strategies

### Files Added
- `src/strategies/` directory with base classes, built-in strategies, and custom strategy utilities
- `src/cli.py` command-line interface

### Files Modified
- `src/main.py`: Refactored for GUI/CLI modes
- `src/gui.py`: Updated for strategy registry integration
- `src/strategy.py`: Refactored to use new architecture
- `README.md`: Updated with CLI usage examples

### Usage Examples

## [0.3.0] - 2025-08-07

### Added

- **Built-in Strategies:** Added several built-in, fixed-weight portfolio strategies for comparison and benchmarking:
    - 60/40 Portfolio (60% Stocks, 40% Bonds)
    - Permanent Portfolio (25% Stocks, 25% Bonds, 25% Cash, 25% Gold)
    - All-Weather Portfolio (complex allocation with proxies for missing assets)
    - David Swensen's Portfolio (diversified portfolio with proxies for missing assets)
- **Custom Strategy Builder:** Added a new "Custom Strategy" tab in the GUI to allow users to create and backtest their own fixed-weight strategies by assigning weights to available assets.
- **CLI Mode:** Implemented a command-line interface (CLI) mode to run backtests without launching the GUI. Use `python -m src.main --mode cli` to run all strategies.
- **Data Download Button:** Added a "Download/Refresh All Data" button in the GUI to trigger the data download script directly from the application.
- **Strategy Details in GUI:** The "Backtest" tab now displays the underlying assets and their weights for the selected strategy.
- **Gap Analysis in GUI:** The "Portfolio" tab now includes a "Gap Analysis" table to visualize the difference between the selected strategy and the user's current holdings.
- **Backtest Start Date:** Users can now specify a start date for backtests in the GUI.
- **Enhanced Data Management Tab:** The "Data" tab now displays a list of all available data files and allows users to download data for new tickers.
- **Backtest Tests:** Added a new test file, `tests/test_backtest.py`, to run backtests for all strategies and ensure they complete successfully.

### Changed

- **Refactored `main.py`:** The main script now acts as a central entry point for both GUI and CLI modes, determined by the `--mode` argument.
- **Strategy Implementation:** Refactored fixed-weight strategies to inherit from a common `FixedWeightStrategy` base class, reducing code duplication.
- **GUI Layout:** Reorganized the GUI with new tabs for "Custom Strategy" and "Data" to improve usability.
- **Merged Test Directories:** The `src/test` directory has been merged into the top-level `tests` directory to consolidate all tests in one location.
- **Sanitized Strategy Names:** Strategy names are now sanitized before being used in file paths to prevent errors with special characters.

### Fixed

- **Buy and Hold Backtest:** Fixed an issue where the "Buy and Hold" strategy would fail due to a missing Sharpe Ratio analyzer.

### Removed

- **`backtest_runner.py`:** The functionality of this script has been integrated into `src/main.py` and the file has been removed.

## [0.2.1] - 2025-01-30

### Added

- **Manual P/E Data Integration:** Introduced support for user-downloaded manual P/E files from authoritative sources (HSI, HSTECH, S&P 500, NASDAQ 100).
- **P/E Data Fill-to-Recent:** Implemented automatic gap filling from manual historical data to current dates using Yahoo Finance and price-based fallback methods.
- **Multi-Format P/E Processing:** Added robust parsing for different manual file formats including various date formats ("Dec 2021", "2025/03/01", "2024/12/31") and column structures.
- **P/E Test Suite:** Created comprehensive test suite in `src/test/` including unit tests (`test_pe_data_download.py`) and interactive demo (`demo_pe_data_flow.py`).
- **HSI Asset Support:** Added Hang Seng Index (HSI) as a new tracked asset alongside HSTECH for better Hong Kong market coverage.

### Changed

- **P/E Data Architecture:** Replaced inferred P/E ratios (price-based estimates) with accurate historical P/E data from manual downloads plus akshare API.
- **Strategy Asset Mix:** Updated allocation weights to CSI300 (15%), CSI500 (15%), HSI (10%), HSTECH (10%) for improved diversification.
- **Monthly P/E Handling:** Enhanced `calculate_pe_percentile()` function to properly handle monthly P/E data frequency vs daily price data.
- **Data Configuration:** Updated `PE_ASSETS` configuration to support `manual_file` patterns and akshare symbols for different data sources.
- **P/E Data Loading:** Modified `load_pe_data()` to detect data frequency (monthly vs daily) and provide appropriate logging.

### Fixed

- **P/E Accuracy:** Eliminated assumption that earnings remain constant over time, replacing it with actual historical P/E ratios.
- **Date Handling:** Improved timezone-naive datetime handling for consistent P/E data processing across different sources.
- **Missing Data Graceful Handling:** Added smart gap detection (only fills if manual data >2 months old) and detailed error messages for missing files.

### Technical Details

- **New Functions:** `process_manual_pe_file()`, `fill_pe_data_to_recent()`, `get_recent_pe_from_yfinance()`, `estimate_recent_pe_from_price()`
- **File Requirements:** Users must download 4 manual P/E files and place in `data/pe/` or project root
- **Fallback Strategy:** Yahoo Finance → Price-based estimation → Detailed logging throughout
- **Test Coverage:** Complete test suite with edge case handling and interactive demonstrations

## [0.2.0] - 2025-07-31

### Added

- **Gradio GUI:** Introduced a new graphical user interface built with Gradio, accessible by running `python -m src.main`.
- **Backtesting Tab:** The GUI includes a tab for running backtests with tunable parameters for the dynamic allocation strategy.
- **Portfolio Tab:** A consolidated tab to monitor target vs. current portfolio weights and edit current holdings.
- **Holdings Management:** Added functionality to store and manage user's current portfolio holdings in `data/holdings.json`.
- **On-Demand Calculation:** The application now pre-calculates and caches target weights on startup for immediate display in the GUI.
- **Analytics Module:** Introduced a new `src/analytics.py` module to generate detailed CSV reports for debugging and analysis.
- **Rebalancing Log:** The backtesting engine now produces a detailed rebalancing log in CSV format, stored in the new `/analytics` directory.
- **FRED API Integration:** Added support for US Treasury yield data via FRED API with yfinance fallback for reliable data sourcing.
- **Enhanced PE Data Accuracy:** Implemented ETF-based PE data collection (SPY, QQQ, FXI) instead of index-based for more accurate valuation metrics.

### Changed

- **Decoupled Logic:** Refactored the weight calculation logic out of the `backtrader` strategy to allow for standalone use in the GUI.
- **Error Handling:** Improved error handling in the GUI to provide better feedback to the user and prevent CSV parsing errors.
- **Data Storage:** Restructured the `/data` directory to segregate price, PE, and yield data into separate subdirectories for improved scalability.
- **File Naming:** Updated the data file naming convention to a more standardized format: `ASSET_YYYYMMDD_to_YYYYMMDD.csv`.
- **Reporting Output:** All generated reports and charts are now saved to the `/analytics` directory.
- **Data Sources:** Updated PE data collection to use ETF tickers (SPY, QQQ, FXI) instead of index tickers for improved accuracy.
- **Historical Data Range:** Extended PE data collection to cover the last 20 years (from 2004) instead of default yfinance range.
- **Dependencies:** Added `gradio` and `python-dotenv` to `requirements.txt` for GUI and environment variable support.

### Fixed

- **US10Y Data Loading:** Fixed yield data integration in market data loading pipeline.
- **Character Encoding:** Improved handling of international data sources with proper UTF-8 encoding.
- **Data Validation:** Enhanced data cleaning to remove invalid PE values and handle mixed data source formats.

## [0.2.2] - 2025-08-10

### Fixed
- **Metaclass Conflict**: Fixed `TypeError: metaclass conflict` in `src/strategies/base.py` by removing ABC inheritance from BaseStrategy
- **Missing Dependencies**: Added `pytest` and `gradio` to requirements.txt  
- **Missing Backtest Runner**: Created comprehensive `src/backtest_runner.py` module with proper error handling
- **GUI Strategy Map Error**: Fixed `NameError: name 'strategy_map' is not defined` in src/gui.py
- **Missing FixedWeightStrategy**: Added FixedWeightStrategy class to src/strategies/base.py for custom strategy creation
- **NaN Portfolio Values**: Added robust handling for NaN values in backtest results using numpy
- **File Path Issues**: Fixed directory creation and filename sanitization for strategies with special characters (like "60/40 Portfolio")
- **Import Errors**: Fixed all import statements in test files and modules

### Added
- **FixedWeightStrategy**: New base strategy class for custom fixed-weight allocations
- **Error Handling**: Comprehensive error handling for NaN values and file operations in backtest runner
- **File Sanitization**: Automatic filename sanitization for strategy names with special characters
- **Dependencies**: Added numpy for robust NaN handling

### Changed
- **BaseStrategy**: Removed ABC inheritance while preserving abstract method decorators
- **Backtest Runner**: Enhanced with proper NaN handling and robust file operations
- **GUI**: Fixed syntax error in else block and removed undefined strategy_map usage
- **Test Framework**: Updated to use new backtest runner module

## [0.1.0] - 2025-07-22

### Added

- **Project Structure:** Introduced `src` and `tests` directories to better organize the codebase.
- **Unit Tests:** Added a testing framework with `unittest` and initial tests for strategy calculation utilities.
- **Configuration:** Centralized all configuration into a new `src/config.py` file.
- **Modularity:** Created new modules for data loading (`data_loader.py`), backtest execution (`backtest_runner.py`), reporting (`reporting.py`), and strategy utilities (`strategy_utils.py`).

### Changed

- **Refactored `main.py`:** Simplified the main script to be a high-level orchestrator of the backtesting process.
- **Refactored `strategy.py`:** Moved complex calculation logic to `strategy_utils.py` to make the strategy easier to read and maintain.
- **Improved Error Handling:** Implemented a "fail-fast" mechanism in the data loader to raise a `FileNotFoundError` when critical data is missing.
- **Code Quality:** Replaced hardcoded values with configuration from `config.py` and updated all imports to be absolute from the `src` directory.
- **Logger:** Renamed `logger.py` to `app_logger.py` to avoid conflicts with other libraries.