# Personal Finance Agent

This project is a comprehensive, modular quantitative investment analysis platform. It allows for the development, backtesting, and analysis of various investment strategies, from simple static portfolios to complex dynamic allocation models.

## Key Features

- **Modular Architecture**: A clean separation of concerns between data handling, strategy logic, backtesting, and performance analysis.
- **Extensible Strategy Framework**: Easily add new custom strategies by inheriting from a base class.
- **Built-in Strategies**: Comes with several pre-built strategies, including static asset allocations (e.g., 60/40, All-Weather) and a dynamic strategy based on market valuation.
- **Realistic Backtesting**: Powered by `backtrader`, the engine simulates execution lag, commissions, and slippage.
- **In-depth Performance Analysis**: Generates detailed reports and charts covering a wide range of performance and risk metrics.
- **Dual Interface**: Can be operated via a command-line interface (CLI) for automation or a Streamlit-based graphical user interface (GUI) for interactive analysis.

## Modules

The system is organized into the following core modules, each corresponding to a directory in `src/`:

- **`src/management` (System Coordinator)**: Oversees the entire system, coordinating all other modules via the `SystemCoordinator` class. It orchestrates backtests, manages configurations, and provides a central point for system health checks.
- **`src/strategies` (Strategy Module)**: A repository of investment strategies, inheriting from `BaseStrategy`. It includes static-weight portfolios (`classic.py`) and dynamic strategies that adjust to market conditions (`dynamic_strategies.py`).
- **`src/trading` (Trading Module)**: Executes trades as instructed by the strategy modules. It features a `TradeExecutor` for simulated, paper, and live trading, handling `Order` objects and simulating costs.
- **`src/backtesting` (Backtesting Platform)**: Implemented using the `backtrader` library within the `EnhancedBacktestEngine`. It allows strategies to be tested on historical data, modeling execution lag, commissions, and slippage to simulate performance realistically.
- **`src/performance` (Performance Analysis)**: The `PerformanceAnalyzer` evaluates strategy effectiveness, calculating key metrics (Sharpe ratio, max drawdown) and generating reports and charts with `matplotlib`.
- **`src/data_center` (Data Center)**: Manages all system data. `download.py` fetches raw market data using `akshare` and `yfinance`. `data_loader.py` provides clean, date-indexed DataFrames to other modules. `data_processor.py` generates derived datasets for strategies.

## Getting Started

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/Personal-Finance-Agent.git
    cd Personal-Finance-Agent
    ```

2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

#### 1. Download Data

Before running any backtests, you must download the necessary market data. The system will not create placeholder files and will fail if data is missing.

```bash
python -m src.data_center.download
```

#### 2. Run a Backtest (CLI)

You can run a backtest for a specific strategy using the main script in CLI mode.

```bash
# Run the built-in Dynamic Allocation strategy
python src/main.py --mode cli --strategy dynamic_allocation

# Run the classic 60/40 portfolio
python src/main.py --mode cli --strategy 60_40_portfolio
```

Backtest results, logs, and performance reports will be saved in the `analytics/` directory.

#### 3. Launch the GUI

For a more interactive experience, you can launch the Streamlit GUI.

```bash
streamlit run src/streamlit_app.py
```

From the GUI, you can run backtests, view performance dashboards, and analyze results interactively.

## Configuration

System and asset configurations are managed in the `config/` directory.

- **`config/system.py`**: Contains system-wide settings like initial capital and commission rates.
- **`config/assets.py`**: Defines the assets available for trading and their associated data source tickers.