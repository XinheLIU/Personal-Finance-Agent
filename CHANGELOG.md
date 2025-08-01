# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-08-01

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