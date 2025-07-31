# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-07-31

### Added

- **Gradio GUI:** Introduced a new graphical user interface built with Gradio, accessible by running `python -m src.main`.
- **Backtesting Tab:** The GUI includes a tab for running backtests with tunable parameters for the dynamic allocation strategy.
- **Portfolio Tab:** A consolidated tab to monitor target vs. current portfolio weights and edit current holdings.
- **Holdings Management:** Added functionality to store and manage user's current portfolio holdings in `data/holdings.json`.
- **On-Demand Calculation:** The application now pre-calculates and caches target weights on startup for immediate display in the GUI.

### Changed

- **Decoupled Logic:** Refactored the weight calculation logic out of the `backtrader` strategy to allow for standalone use in the GUI.
- **Error Handling:** Improved error handling in the GUI to provide better feedback to the user.
- **Dependencies:** Added `gradio` to `requirements.txt`.

## [0.2.0] - 2025-07-28

### Added

- **Analytics Module:** Introduced a new `src/analytics.py` module to generate detailed CSV reports for debugging and analysis.
- **Rebalancing Log:** The backtesting engine now produces a detailed rebalancing log in CSV format, stored in the new `/analytics` directory.

### Changed

- **Data Storage:** Restructured the `/data` directory to segregate price, PE, and yield data into separate subdirectories for improved scalability.
- **File Naming:** Updated the data file naming convention to a more standardized format: `ASSET_YYYYMMDD_to_YYYYMMDD.csv`.
- **Reporting Output:** All generated reports and charts are now saved to the `/analytics` directory.
- **Improved Debugging:** The new rebalancing log provides a detailed, step-by-step view of the strategy's execution, making it easier to debug and adjust.

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
