# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
