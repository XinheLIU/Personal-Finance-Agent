### Quant Investment System Architecture

The system is designed with a modular architecture, separating concerns to enhance maintainability and scalability. Each module corresponds to a specific directory within the `src/` folder.

```mermaid
flowchart TB
    subgraph User Interface
        direction LR
        CLI["CLI (main.py, cli.py)"]
        GUI["Streamlit GUI (streamlit_app.py)"]
    end

    subgraph Core System
        direction TB
        F[("src/data_center<br/>(Data Center)")]
        D["src/strategies<br/>(Strategy Module)"]
        E["src/backtesting<br/>(Backtesting Platform)"]
        A["src/performance<br/>(Performance Analysis)"]
        C["src/trading<br/>(Trading Module)"]
        B["src/management<br/>(System Coordinator)"]
    end

    CLI --> B
    GUI --> B
    B --> E
    B --> A
    E --> D
    F --> D
    F --> E
    A --> GUI
```

- **`src/management` (System Coordinator)**: Oversees the entire system, coordinating all other modules via the `SystemCoordinator` class. It orchestrates backtests, manages configurations, and provides a central point for system health checks.
- **`src/strategies` (Strategy Module)**: A repository of investment strategies, inheriting from `BaseStrategy`. It includes static-weight portfolios (`classic.py`) and dynamic strategies that adjust to market conditions (`dynamic_strategies.py`).
- **`src/trading` (Trading Module)**: Executes trades as instructed by the strategy modules. It features a `TradeExecutor` for simulated, paper, and live trading, handling `Order` objects and simulating costs.
- **`src/backtesting` (Backtesting Platform)**: Implemented using the `backtrader` library within the `EnhancedBacktestEngine`. It allows strategies to be tested on historical data, modeling execution lag, commissions, and slippage to simulate performance realistically.
- **`src/performance` (Performance Analysis)**: The `PerformanceAnalyzer` evaluates strategy effectiveness, calculating key metrics (Sharpe ratio, max drawdown) and generating reports and charts with `matplotlib`.
- **`src/data_center` (Data Center)**: Manages all system data. `download.py` fetches raw market data using `akshare` and `yfinance`. `data_loader.py` provides clean, date-indexed DataFrames to other modules. `data_processor.py` generates derived datasets for strategies.

#### Implementation Samples (by module)

- **Data Center (Download with `akshare`)**: Data is downloaded via scripts and stored locally. The system uses `akshare` for Chinese market data.

```python
# From: src/data_center/download.py
import akshare as ak

def download_akshare_index(symbol, asset_name):
    """Download index data from akshare"""
    try:
        LOG.info(f"Downloading {asset_name} data from akshare (symbol: {symbol})")
        data = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
        # ... (merging and saving logic) ...
    except Exception as e:
        LOG.error(f"Error downloading {asset_name} from akshare: {e}")
```

- **Data Center (Load for `backtrader`)**: The backtesting engine loads this local data into a format compatible with `backtrader`.

```python
# From: src/data_center/data_loader.py
class DataLoader:
    def load_data_feed(self, asset_name: str, name: str, start_date: Optional[str] = None) -> Optional[bt.feeds.PandasData]:
        """Load data feed from CSV file with enhanced validation"""
        # ... (finds file, reads CSV) ...
        df = self._validate_dataframe(df, asset_name)
        # ... (creates OHLCV columns) ...
        data_feed = PandasData(dataname=df)
        return data_feed
```

- **Strategy Module (Dynamic Allocation)**: Strategies calculate target weights based on processed data, such as P/E ratios or economic indicators.

```python
# From: src/strategies/builtin/dynamic_strategies.py
class DynamicAllocationStrategy(DynamicStrategy):
    def calculate_target_weights(self, current_date) -> Dict[str, float]:
        """Calculate target weights based on P/E percentiles and yield data"""
        # ... (loads processed data) ...
        pe_percentile = pe_percentile_from_processed(self.processed_data, 'CSI300', current_date, 10)
        yield_pct = yield_percentile_from_processed(self.processed_data, current_date, 20)
        # ... (calculates weights based on percentiles) ...
        return weights
```

- **Backtesting Platform (Running an Engine)**: A backtest is executed by configuring and running the `EnhancedBacktestEngine`.

```python
# From: src/backtesting/engine.py
from src.strategies.classic import BuyAndHoldStrategy

# Initialize engine
backtest_engine = EnhancedBacktestEngine(initial_capital=100000)

# Run backtest
results = backtest_engine.run_backtest(
    strategy_class=BuyAndHoldStrategy,
    strategy_name="Buy and Hold",
    start_date="2020-01-01",
    end_date="2023-12-31"
)
```

- **Management Module (System Coordination)**: The `SystemCoordinator` can manage the lifecycle of a strategy backtest.

```python
# From: src/management/coordinator.py
from src.strategies.classic import BuyAndHoldStrategy

coordinator = SystemCoordinator()
coordinator.startup_system()

coordinator.register_strategy(
    strategy_class=BuyAndHoldStrategy,
    strategy_name="Buy and Hold",
    parameters={'start_date': '2020-01-01'}
)

coordinator.start_strategy("Buy and Hold")
```

- **Performance Analysis Module (Generating a Report)**: After a backtest, the `PerformanceAnalyzer` generates detailed reports and charts.

```python
# From: src/performance/analytics.py
analyzer = PerformanceAnalyzer()
report = analyzer.generate_performance_report(
    strategy_results=backtest_results,
    save_charts=True
)
```

- **Trading Module (Simulated Execution)**: The `SimulationExecutor` can be used to simulate the process of placing an order.

```python
# From: src/trading/executor.py
from src.trading.executor import SimulationExecutor, OrderType

# Executor requires market data for simulation
sim_executor = SimulationExecutor(market_data=loaded_market_data)

# Create and submit a market order
buy_order = sim_executor.create_market_order(
    symbol='SPY',
    quantity=10,
    side='buy'
)
sim_executor.submit_order(buy_order)
```

### Key Workflow

1.  **Data Download**: The user runs `src/data_center/download.py` (or it's triggered automatically) to fetch the latest market data from sources like `yfinance` and `akshare`. Data is saved to `data/raw/`.
2.  **Data Processing**: For complex strategies, `src/data_center/data_processor.py` is run to create derived datasets (e.g., smoothed P/E ratios), which are saved to `data/processed/`.
3.  **Backtest Execution**: The user, via the CLI or GUI, initiates a backtest. The `SystemCoordinator` configures the `EnhancedBacktestEngine` with a selected strategy (e.g., `DynamicAllocationStrategy`) and data from the `DataLoader`.
4.  **Strategy Logic**: During the backtest, the strategy requests data for each time step and calculates target portfolio weights.
5.  **Execution Simulation**: The `EnhancedBacktestEngine`, using `backtrader`, simulates executing trades to match the target weights, applying commission and slippage costs.
6.  **Performance Analysis**: After the backtest completes, the `PerformanceAnalyzer` is used to compute metrics and generate charts and reports, which are saved in `analytics/performance/`.
7.  **Review**: The user reviews the generated reports and charts to evaluate the strategy's performance.