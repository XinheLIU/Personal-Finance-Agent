# Key Workflows

This guide covers the most common end-to-end flows:

- Running backtests (GUI and CLI) and where to debug
- Developing and registering new strategies (no‑code via GUI and code-based)

## Prerequisites

- Create/activate your conda env and install deps:

```bash
conda activate py-fin
pip install -r requirements.txt
```

## 1) Run Backtests

### A. Download/refresh data

```bash
python -m src.data_download            # initial download
python -m src.data_download --refresh  # force refresh
```

### B. GUI mode (recommended)

```bash
python -m src.main --mode gui
```

- Backtest tab:
  - Select a strategy from the dropdown
  - Adjust Rebalance Days, Threshold, Initial Capital, Commission
  - Optionally set Backtest Start Date (YYYY-MM-DD)
  - Click Run Backtest to see summary metrics and performance chart
- Custom Strategy tab: define weights and run backtest without coding
- Portfolio tab: compare target vs. your holdings, edit and save holdings
- Data tab: view available data, download/refresh all data

### C. CLI mode

```bash
# List strategies
python -m src.cli list

# Run a strategy (optional params shown)
python -m src.cli run SixtyFortyStrategy --rebalance-days 30 --threshold 0.05

# Show current target weights and reasoning (dynamic)
python -m src.cli weights

# Download/refresh data
python -m src.cli download --refresh

# Alternate CLI via main
python -m src.main --mode cli --list-strategies
python -m src.main --mode cli --strategy DynamicAllocationStrategy
python -m src.main --download-data --refresh-data
```

### D. Run tests (sanity + regression)

```bash
python -m pytest tests/ -v
```

Useful suites:

- `tests/test_backtest.py`: validates all built-in strategies run and produce reasonable metrics
- `tests/test_pe_data_download.py`: validates manual PE parsing and recent fill logic
- `tests/test_strategy_utils.py`: validates PE/yield percentile utilities

## 2) Debugging Backtests

- Logs: both console and file via Loguru
  - File: `logs/app.log` (rotates at ~1MB)
  - Levels: DEBUG to stdout, ERROR to stderr, DEBUG to file
- Common fixes:
  - Missing data → run `python -m src.data_download` (use `--refresh` if needed)
  - FRED API errors → set `FRED_API_KEY` in `.env` (uses `python-dotenv`)
  - CSV/encoding issues → ensure UTF-8; yfinance cleaning removes invalid rows
- GUI data overview: Data tab shows available files and date ranges
- Analytics: backtests may write CSV logs under `analytics/` for deeper inspection

## 3) Develop New Strategies

### Option A: No‑code (GUI)

- Use the Custom Strategy tab
- Enter assets and weights so they sum to 100%
- Click Run Custom Strategy Backtest

To persist and reuse a custom strategy in code, use `StrategyBuilder` APIs (see Option C).

### Option B: Static allocation (code)

Create a class that inherits `StaticAllocationStrategy` and implement `get_target_weights()`.
File suggestions: `src/strategies/builtin/static_strategies.py` or `src/strategies/custom/user_strategy.py`.
Example skeleton:

```python
from src.strategies.base import StaticAllocationStrategy

class MyStaticStrategy(StaticAllocationStrategy):
    """My fixed-weight strategy"""
    def get_target_weights(self) -> dict[str, float]:
        return {
            "SP500": 0.60,
            "US10Y": 0.40,
        }
```

Register it so it appears in GUI/CLI:

- Add the class to the built-in registry list in `src/strategies/registry.py` (method `_register_builtin_strategies`).
- Or place it under `src/strategies/custom/` and load via Option C below.

### Option C: User-defined (code, JSON-backed)

Use `StrategyBuilder` to create and persist strategies without touching the registry manually:

```python
from src.strategies.custom.user_strategy import StrategyBuilder

# Validate and save
weights = {"SP500": 0.5, "GLD": 0.5}
ok, msg = StrategyBuilder.validate_weights(weights)
assert ok, msg
StrategyBuilder.save_strategy("My JSON Strategy", weights)

# Auto-registered at startup
```

These are auto-loaded by the `StrategyRegistry` at import time and will show up in the GUI and `python -m src.cli list`.

### Option D: Dynamic strategy (code)

Create a class inheriting `DynamicStrategy` and implement `calculate_target_weights(current_date)` using data loaded in the base class (market prices, PE, yields). Example skeleton:

```python
from typing import Dict
from src.strategies.base import DynamicStrategy

class MyDynamicStrategy(DynamicStrategy):
    """My dynamic allocation logic"""
    def calculate_target_weights(self, current_date) -> Dict[str, float]:
        # Use self.market_data / self.pe_cache / self.yield_data as needed
        return {"SP500": 0.7, "US10Y": 0.3}
```

Register it by adding to `_register_builtin_strategies()` or package as a user strategy similar to Option C.

### Validate your new strategy

```bash
python -m pytest tests/test_backtest.py -k "My"
python -m src.cli run MyStaticStrategy
```

## 4) Helpful References

- Strategy architecture: `src/strategies/base.py`
- Built-ins: `src/strategies/builtin/static_strategies.py`, `src/strategies/builtin/dynamic_strategies.py`
- Registry: `src/strategies/registry.py`
- Custom strategies: `src/strategies/custom/user_strategy.py`
- CLI: `src/cli.py`  |  GUI: `src/gui.py`  |  Entry: `src/main.py`
- Data pipeline: `src/data_download.py`, `src/data_loader.py`
